"""Flask webhook server for handling real-time Twilio call conversations."""
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, Response

from src.integrations.openrouter_client import OpenRouterClient
from src.personas.persona_factory import PersonaFactory
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

app = Flask(__name__)

# In-memory session store: {call_sid: session_data}
# Thread-safe with a lock since Flask handles requests concurrently
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = threading.Lock()

# Will be set by the orchestrator before calls are made
_llm_client: Optional[OpenRouterClient] = None
_public_url: str = ""


def init_server(llm_client: OpenRouterClient, public_url: str) -> None:
    """Initialize the webhook server with dependencies.

    Args:
        llm_client: OpenRouter LLM client for generating responses
        public_url: The ngrok public URL pointing to this server
    """
    global _llm_client, _public_url
    _llm_client = llm_client
    _public_url = public_url.rstrip("/")
    logger.info(f"Webhook server initialized — public URL: {_public_url}")


def get_session(call_sid: str) -> Optional[Dict[str, Any]]:
    """Get session data for a call.

    Args:
        call_sid: Twilio call SID

    Returns:
        Session dictionary or None
    """
    with _sessions_lock:
        return _sessions.get(call_sid)


def get_transcript(call_sid: str) -> Optional[str]:
    """Get the full conversation transcript for a completed call.

    Args:
        call_sid: Twilio call SID

    Returns:
        Formatted transcript string or None
    """
    session = get_session(call_sid)
    if not session:
        return None

    lines = []
    for msg in session.get("history", []):
        role = msg["role"]
        content = msg["content"]
        if role == "assistant":
            lines.append(f"[Patient - {session['persona_name']}]: {content}")
        elif role == "user":
            lines.append(f"[Receptionist]: {content}")
    return "\n\n".join(lines) if lines else "No conversation recorded."


def _build_twiml_gather(say_text: str, action_url: str, hints: str = "") -> str:
    """Build a TwiML response that speaks and then listens.

    Args:
        say_text: Text for Twilio to speak
        action_url: URL to POST when speech is captured
        hints: Optional speech recognition hints

    Returns:
        TwiML XML string
    """
    hints_attr = f' hints="{hints}"' if hints else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="alice">{_escape_xml(say_text)}</Say>'
        f'<Gather input="speech" action="{action_url}" timeout="8" '
        f'speechTimeout="2" language="en-US"{hints_attr}/>'
        # If caller says nothing after gather, hang up politely
        '<Say voice="alice">I didn\'t catch that. Thank you for calling. Goodbye!</Say>'
        "<Hangup/>"
        "</Response>"
    )


def _build_twiml_say_hangup(say_text: str) -> str:
    """Build a TwiML response that speaks and hangs up."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="alice">{_escape_xml(say_text)}</Say>'
        "<Hangup/>"
        "</Response>"
    )


def _escape_xml(text: str) -> str:
    """Escape special XML characters in text."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


def _should_end_conversation(history: list, turn_count: int, max_turns: int) -> bool:
    """Decide whether the patient should end the call."""
    if turn_count >= max_turns:
        return True
    # If the last patient message contains a farewell, end it
    if history:
        last_patient = next(
            (m["content"] for m in reversed(history) if m["role"] == "assistant"),
            ""
        ).lower()
        farewells = ["goodbye", "bye", "thank you so much", "that's all", "thanks, bye"]
        if any(f in last_patient for f in farewells):
            return True
    return False


def _generate_patient_response(session: Dict[str, Any], receptionist_speech: str) -> str:
    """Generate the patient's next response using the LLM.

    Args:
        session: Current call session
        receptionist_speech: What the receptionist just said

    Returns:
        Patient's response text
    """
    if not _llm_client:
        return "Um, okay. Thank you. Goodbye!"

    persona = session["persona"]
    history = session["history"]

    # Add receptionist message to history
    history.append({"role": "user", "content": receptionist_speech})

    # Generate patient response
    messages = [{"role": "system", "content": persona.get_system_prompt()}]
    messages.extend(history)

    response = _llm_client.generate_response(messages, max_tokens=200, temperature=0.85)
    patient_reply = response if response else "Um... okay. Thank you. Goodbye!"

    # Add patient response to history
    history.append({"role": "assistant", "content": patient_reply})
    session["turn_count"] += 1

    return patient_reply


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/start", methods=["POST"])
def start_call():
    """Called by Twilio when the call is answered. Starts the conversation."""
    call_sid = request.form.get("CallSid", "unknown")
    persona_name = request.args.get("persona", "scheduler")
    call_id = request.args.get("call_id", "unknown")

    logger.info(f"Call connected — SID: {call_sid}, Persona: {persona_name}")

    # Look up the persona
    persona = PersonaFactory.get_persona_by_name(persona_name)

    # Create session
    with _sessions_lock:
        _sessions[call_sid] = {
            "call_id": call_id,
            "persona_name": persona.name,
            "persona": persona,
            "history": [],
            "turn_count": 0,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
        }

    # Patient speaks first with their opening line
    opening = persona.get_initial_greeting()

    with _sessions_lock:
        session = _sessions[call_sid]
        session["history"].append({"role": "assistant", "content": opening})
        session["turn_count"] += 1

    action_url = f"{_public_url}/respond?persona={persona_name}&call_id={call_id}"

    twiml = _build_twiml_gather(opening, action_url)
    return Response(twiml, mimetype="text/xml")


@app.route("/respond", methods=["POST"])
def respond():
    """Called by Twilio after each speech capture. Continues the conversation."""
    call_sid = request.form.get("CallSid", "unknown")
    speech_result = request.form.get("SpeechResult", "").strip()
    persona_name = request.args.get("persona", "scheduler")
    call_id = request.args.get("call_id", "unknown")

    logger.info(f"Turn received — SID: {call_sid}, Speech: '{speech_result[:80]}'")

    with _sessions_lock:
        session = _sessions.get(call_sid)

    if not session:
        # Session lost — gracefully hang up
        return Response(_build_twiml_say_hangup("Thank you for calling. Goodbye!"), mimetype="text/xml")

    if not speech_result:
        speech_result = "[silence]"

    # Generate patient's next line
    patient_reply = _generate_patient_response(session, speech_result)

    max_turns = 12
    if _should_end_conversation(session["history"], session["turn_count"], max_turns):
        # Patient wraps up and hangs up
        farewell = "Okay, thank you so much for your help! Goodbye!"
        with _sessions_lock:
            if call_sid in _sessions:
                _sessions[call_sid]["status"] = "completed"
        return Response(_build_twiml_say_hangup(farewell), mimetype="text/xml")

    action_url = f"{_public_url}/respond?persona={persona_name}&call_id={call_id}"
    twiml = _build_twiml_gather(patient_reply, action_url)
    return Response(twiml, mimetype="text/xml")


@app.route("/status", methods=["POST"])
def call_status():
    """Called by Twilio when call status changes."""
    call_sid = request.form.get("CallSid", "unknown")
    status = request.form.get("CallStatus", "unknown")

    logger.info(f"Call status update — SID: {call_sid}, Status: {status}")

    if status in ("completed", "failed", "busy", "no-answer", "canceled"):
        with _sessions_lock:
            if call_sid in _sessions:
                _sessions[call_sid]["status"] = status
                _sessions[call_sid]["ended_at"] = datetime.now().isoformat()

    return Response("", status=204)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return {"status": "ok", "sessions": len(_sessions)}, 200
