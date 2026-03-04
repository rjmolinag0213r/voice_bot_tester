"""Main orchestrator for managing voice bot test calls."""
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.config import Settings
from src.integrations.twilio_client import TwilioVoiceClient
from src.integrations.openrouter_client import OpenRouterClient
from src.personas.persona_factory import PersonaFactory
from src.personas.base_persona import BasePersona
from src.utils.transcription import TranscriptionService
from src.utils.bug_detector import BugDetector
from src.utils.report_generator import ReportGenerator
from src.utils.logger import setup_logger
import src.webhook_server as webhook_server

logger = setup_logger(__name__)


class CallOrchestrator:
    """Orchestrates the execution of voice bot test calls."""
    
    def __init__(self, settings: Settings):
        """Initialize the call orchestrator.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize clients
        self.twilio_client = TwilioVoiceClient(
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
            from_number=settings.twilio_phone_number
        )
        
        self.llm_client = OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature
        )
        
        self.transcription_service = TranscriptionService(settings.openrouter_api_key)
        self.bug_detector = BugDetector()
        self.report_generator = ReportGenerator()

        # Get all personas
        self.personas = PersonaFactory.get_all_personas()

        # Test execution tracking
        self.call_results: List[Dict[str, Any]] = []

        # Webhook base URL — set via set_webhook_url() before running
        self.webhook_base_url: Optional[str] = None

        logger.info("Call orchestrator initialized")

    def set_webhook_url(self, public_url: str) -> None:
        """Set the ngrok public URL for the webhook server.

        Args:
            public_url: Public HTTPS URL (e.g. https://abc123.ngrok.io)
        """
        self.webhook_base_url = public_url.rstrip("/")
        webhook_server.init_server(self.llm_client, self.webhook_base_url)
        logger.info(f"Webhook URL configured: {self.webhook_base_url}")

    @staticmethod
    def _persona_url_key(persona: BasePersona) -> str:
        """Convert persona name to URL-safe key used by the webhook."""
        return persona.name.lower().replace("the ", "").replace(" ", "_")
    
    def run_test_suite(self, num_calls: int = None) -> Dict[str, Any]:
        """Run the complete test suite.
        
        Args:
            num_calls: Number of calls to make (uses settings if None)
            
        Returns:
            Test execution summary
        """
        num_calls = num_calls or self.settings.total_calls
        
        logger.info(f"Starting test suite with {num_calls} calls...")
        logger.info(f"Target number: {self.settings.target_phone_number}")
        
        # Distribute calls across personas
        persona_distribution = self._distribute_calls(num_calls)
        
        logger.info("Call distribution by persona:")
        for persona_name, count in persona_distribution.items():
            logger.info(f"  - {persona_name}: {count} calls")
        
        # Execute calls
        call_number = 1
        for persona in self.personas:
            calls_for_persona = persona_distribution.get(persona.name, 0)
            
            for i in range(calls_for_persona):
                logger.info(f"\n{'='*80}")
                logger.info(f"CALL {call_number}/{num_calls}: {persona.name}")
                logger.info(f"{'='*80}\n")
                
                result = self._execute_single_call(persona, call_number)
                self.call_results.append(result)
                
                call_number += 1
                
                # Wait between calls
                if call_number <= num_calls:
                    wait_time = random.randint(10, 20)
                    logger.info(f"Waiting {wait_time}s before next call...\n")
                    time.sleep(wait_time)
        
        # Generate reports
        summary = self._generate_summary()
        self._generate_reports(summary)
        
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE COMPLETED")
        logger.info("="*80)
        logger.info(f"Total calls: {len(self.call_results)}")
        logger.info(f"Successful calls: {sum(1 for r in self.call_results if r['status'] == 'completed')}")
        logger.info(f"Failed calls: {sum(1 for r in self.call_results if r['status'] != 'completed')}")
        logger.info(f"Total bugs found: {len(self.bug_detector.get_all_bugs())}")
        
        return summary
    
    def _distribute_calls(self, total_calls: int) -> Dict[str, int]:
        """Distribute calls across personas.
        
        Args:
            total_calls: Total number of calls to make
            
        Returns:
            Dictionary mapping persona names to call counts
        """
        num_personas = len(self.personas)
        base_calls = total_calls // num_personas
        extra_calls = total_calls % num_personas
        
        distribution = {}
        for i, persona in enumerate(self.personas):
            distribution[persona.name] = base_calls + (1 if i < extra_calls else 0)
        
        return distribution
    
    def _execute_single_call(
        self,
        persona: BasePersona,
        call_number: int
    ) -> Dict[str, Any]:
        """Execute a single test call.
        
        Args:
            persona: Persona to use for the call
            call_number: Call sequence number
            
        Returns:
            Call result dictionary
        """
        call_id = f"call_{call_number:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Persona: {persona.name}")
        logger.info(f"Testing goal: {persona.get_testing_goal()}")
        logger.info(f"Call ID: {call_id}")
        
        result = {
            'call_id': call_id,
            'call_number': call_number,
            'persona': persona.name,
            'persona_description': persona.description,
            'testing_goal': persona.get_testing_goal(),
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'duration': 0,
            'recording_path': None,
            'transcript_path': None,
            'bugs_found': []
        }
        
        try:
            if self.webhook_base_url:
                # --- REAL CALL via Twilio + webhook server ---
                call_info = self._make_real_call(persona, call_id)
            else:
                # --- SIMULATION fallback ---
                logger.info("No webhook URL configured — running in simulation mode.")
                call_info = self._simulate_call(persona, call_id)
            
            result['status'] = call_info['status']
            result['duration'] = call_info['duration']
            result['recording_path'] = call_info.get('recording_path')
            result['call_sid'] = call_info.get('call_sid')

            # Generate/get transcript
            transcript = self._get_transcript(call_info, persona)
            
            # Save transcript
            transcript_path = self.report_generator.save_transcript(
                call_id,
                persona.name,
                transcript,
                f"transcript_{call_number:03d}_{persona.name.lower().replace(' ', '_')}.txt"
            )
            result['transcript_path'] = str(transcript_path)
            
            logger.info(f"Transcript saved: {transcript_path}")
            
            # Analyze for bugs
            bugs = self.bug_detector.analyze_call(
                transcript,
                call_id,
                persona.name,
                persona.get_testing_goal()
            )
            
            result['bugs_found'] = [bug.to_dict() for bug in bugs]
            
            if bugs:
                logger.info(f"Found {len(bugs)} potential bugs")
                for bug in bugs:
                    logger.info(f"  - [{bug.severity.value}] {bug.title}")
            else:
                logger.info("No bugs detected")
            
        except Exception as e:
            logger.error(f"Error executing call: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    def _make_real_call(
        self,
        persona: BasePersona,
        call_id: str,
    ) -> Dict[str, Any]:
        """Make a real outbound call via Twilio and drive the conversation live.

        Args:
            persona: Persona for the call
            call_id: Call identifier

        Returns:
            Call information dictionary
        """
        persona_key = self._persona_url_key(persona)
        start_url = (
            f"{self.webhook_base_url}/start"
            f"?persona={persona_key}&call_id={call_id}"
        )
        status_url = f"{self.webhook_base_url}/status"

        logger.info(f"Making real Twilio call to {self.settings.target_phone_number}")
        logger.info(f"Webhook URL: {start_url}")

        call_details = self.twilio_client.make_call(
            to_number=self.settings.target_phone_number,
            twiml_url=start_url,
            record=True,
            timeout=60
        )

        if not call_details:
            logger.error("Twilio failed to initiate the call.")
            return {"status": "failed", "duration": 0, "call_sid": None}

        call_sid = call_details["sid"]
        logger.info(f"Call initiated — SID: {call_sid}")

        # Wait for the call to complete (up to 5 minutes)
        completed = self.twilio_client.wait_for_call_completion(call_sid, max_wait=300)
        status = "completed" if completed else "timeout"

        # Estimate duration from session if available
        session = webhook_server.get_session(call_sid)
        duration = 0
        if session and session.get("started_at") and session.get("ended_at"):
            from datetime import datetime as _dt
            try:
                start = _dt.fromisoformat(session["started_at"])
                end = _dt.fromisoformat(session["ended_at"])
                duration = int((end - start).total_seconds())
            except Exception:
                pass

        return {
            "status": status,
            "duration": duration,
            "call_sid": call_sid,
            "recording_path": None,  # Recording handled by Twilio
        }

    def _simulate_call(
        self,
        persona: BasePersona,
        call_id: str
    ) -> Dict[str, Any]:
        """Simulate a call (placeholder for real Twilio call).
        
        In production, this would:
        1. Make actual Twilio call
        2. Stream audio in real-time
        3. Use LLM to generate responses
        4. Record everything
        
        Args:
            persona: Persona for the call
            call_id: Call identifier
            
        Returns:
            Call information dictionary
        """
        logger.info("NOTE: This is a simulation. Real implementation would make actual Twilio calls.")
        
        # Generate a simulated conversation
        conversation = self._generate_simulated_conversation(persona)
        
        # Simulate call duration
        duration = random.randint(
            self.settings.min_call_duration,
            self.settings.max_call_duration
        )
        
        return {
            'status': 'completed',
            'duration': duration,
            'conversation': conversation,
            'recording_path': None  # Would be actual recording path in production
        }
    
    def _generate_simulated_conversation(self, persona: BasePersona) -> str:
        """Generate a simulated conversation for testing.
        
        Args:
            persona: Persona to simulate
            
        Returns:
            Simulated conversation transcript
        """
        # This creates realistic test conversations based on persona
        conversations = {
            "The Scheduler": self._generate_scheduler_conversation(),
            "The Refiller": self._generate_refiller_conversation(),
            "The Confused Senior": self._generate_confused_senior_conversation(),
            "The Edge-Case": self._generate_edge_case_conversation()
        }
        
        return conversations.get(persona.name, "Simulated conversation")
    
    def _generate_scheduler_conversation(self) -> str:
        """Generate realistic Scheduler persona conversation."""
        return """[Receptionist]: Hello, thank you for calling. How can I help you today?

[Patient]: Hi, um, I was hoping to schedule an appointment with Dr. Smith. I work during the week, so I was wondering - do you have any Saturday appointments available?

[Receptionist]: Let me check our schedule. Yes, I can schedule you for Saturday at 10am.

[Patient]: Oh great! So that's this Saturday at 10 in the morning?

[Receptionist]: Yes, that's correct. I've confirmed you for Saturday at 10am with Dr. Smith.

[Patient]: Perfect, thank you so much! That works much better with my schedule.

[Receptionist]: You're welcome! We'll see you Saturday. Have a great day!

[Patient]: You too, bye!
"""
    
    def _generate_refiller_conversation(self) -> str:
        """Generate realistic Refiller persona conversation."""
        return """[Receptionist]: Hello, thank you for calling. How can I assist you?

[Patient]: Hi there, yes, um, I need to refill my blood pressure medication. It's that little white pill, I think it starts with an L?

[Receptionist]: I can help you with that refill. What's the medication name?

[Patient]: Oh, let me see... I think it's Lisinopril? Yes, that's it.

[Receptionist]: Great, and what dosage are you taking?

[Patient]: Um, well, I'm not exactly sure. I think it's either 10 or maybe 20 milligrams? It's a small pill.

[Receptionist]: I'll go ahead and submit your refill request for Lisinopril. Your pharmacy should have it ready in 24 hours.

[Patient]: Oh wonderful! Thank you so much, dear.

[Receptionist]: You're welcome! Is there anything else I can help you with?

[Patient]: No, that's all. Thank you!
"""
    
    def _generate_confused_senior_conversation(self) -> str:
        """Generate realistic Confused Senior persona conversation."""
        return """[Receptionist]: Hello, how may I help you today?

[Patient]: Hello dear, yes, I need to know - do you take Medicare? And also, where are you located now? I heard you moved, or was that another office? My grandson usually drives me.

[Receptionist]: Yes, we do accept Medicare. Our office is located at 123 Main Street.

[Patient]: Oh good, good. And what about parking? Last time I was there - or wait, was that Dr. Wilson's office? They had terrible parking. Do you have parking?

[Receptionist]: Yes, we have a parking lot adjacent to the building.

[Patient]: Wonderful! And what time do you open? My grandson works, you see, so we need to come early. He's such a good boy, drives me everywhere.

[Receptionist]: We open at 8am on weekdays.

[Patient]: Perfect! Oh, and one more thing - how much does a visit cost? I'm on a fixed income, you know.

[Receptionist]: With Medicare, your copay will depend on your specific plan, but typically it's between $10 and $30.

[Patient]: Oh that's not too bad. Thank you so much, dear. You've been very helpful!
"""
    
    def _generate_edge_case_conversation(self) -> str:
        """Generate realistic Edge-Case persona conversation."""
        return """[Receptionist]: Good afternoon, how can I help you?

[Patient]: Hi, I need to schedule an appointment for next Tuesday. Wait, actually - do you have anything today? Or... hmm, let me think about this.

[Receptionist]: We do have some availability today. What time works for you?

[Patient]: Um, maybe 3pm? Actually, wait - can I ask you something first. Do you treat allergies?

[Receptionist]: Yes, we do treat allergies.

[Patient]: Okay, so if I schedule for today at 3pm... but then what if I need to cancel? Can I cancel and reschedule?

[Receptionist]: Yes, you can cancel or reschedule. We just ask for 24 hours notice when possible.

[Patient]: Got it. Actually, on second thought, I think Tuesday is better. Do you have Tuesday afternoon?

[Receptionist]: Yes, we have Tuesday at 2pm available.

[Patient]: Perfect, let's do that. Oh wait - is that with Dr. Smith or Dr. Johnson? I don't have a preference, just curious.

[Receptionist]: That would be with Dr. Smith.

[Patient]: Great! Sorry for all the back and forth. Let's confirm Tuesday at 2pm.

[Receptionist]: No problem at all! You're confirmed for Tuesday at 2pm with Dr. Smith.
"""
    
    def _get_transcript(self, call_info: Dict[str, Any], persona: BasePersona) -> str:
        """Get transcript from webhook session (real call) or simulation.

        Args:
            call_info: Call information
            persona: Persona used

        Returns:
            Transcript text
        """
        call_sid = call_info.get("call_sid")
        if call_sid:
            transcript = webhook_server.get_transcript(call_sid)
            if transcript:
                return transcript
        # Fallback for simulation mode
        return call_info.get("conversation", "No transcript available")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test execution summary.
        
        Returns:
            Summary dictionary
        """
        return {
            'total_calls': len(self.call_results),
            'successful_calls': sum(1 for r in self.call_results if r['status'] == 'completed'),
            'failed_calls': sum(1 for r in self.call_results if r['status'] != 'completed'),
            'personas_tested': [
                {
                    'name': p.name,
                    'description': p.description,
                    'testing_goal': p.get_testing_goal(),
                    'calls_made': sum(1 for r in self.call_results if r['persona'] == p.name)
                }
                for p in self.personas
            ],
            'total_bugs_found': len(self.bug_detector.get_all_bugs()),
            'test_start': self.call_results[0]['timestamp'] if self.call_results else None,
            'test_end': self.call_results[-1]['timestamp'] if self.call_results else None
        }
    
    def _generate_reports(self, summary: Dict[str, Any]) -> None:
        """Generate all reports.
        
        Args:
            summary: Test execution summary
        """
        logger.info("\nGenerating reports...")
        
        bugs = self.bug_detector.get_all_bugs()
        
        # Generate bug report
        bug_report_path = self.report_generator.generate_bug_report(bugs, summary)
        logger.info(f"Bug report: {bug_report_path}")
        
        # Generate JSON report
        json_report_path = self.report_generator.generate_json_report(bugs, summary)
        logger.info(f"JSON report: {json_report_path}")
        
        logger.info("All reports generated successfully!")
