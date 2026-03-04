"""Twilio integration for making voice calls and handling recordings."""
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TwilioVoiceClient:
    """Client for managing Twilio voice calls."""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """Initialize Twilio client.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Your Twilio phone number
        """
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.account_sid = account_sid
        self.auth_token = auth_token
        logger.info(f"Twilio client initialized with number {from_number}")
    
    def make_call(
        self,
        to_number: str,
        twiml_url: Optional[str] = None,
        record: bool = True,
        timeout: int = 60
    ) -> Optional[Dict[str, Any]]:
        """Make an outbound call.
        
        Args:
            to_number: Target phone number
            twiml_url: URL that returns TwiML instructions
            record: Whether to record the call
            timeout: Call timeout in seconds
            
        Returns:
            Call details dictionary or None if failed
        """
        try:
            logger.info(f"Initiating call to {to_number}...")
            
            call_params = {
                'to': to_number,
                'from_': self.from_number,
                'timeout': timeout,
            }
            
            if record:
                call_params['record'] = True
                call_params['recording_status_callback_event'] = ['completed']
            
            # If no TwiML URL, use simple text-to-speech
            if not twiml_url:
                call_params['twiml'] = '<Response><Say>Hello, this is a test call.</Say></Response>'
            else:
                call_params['url'] = twiml_url
            
            call = self.client.calls.create(**call_params)
            
            logger.info(f"Call initiated with SID: {call.sid}")
            
            return {
                'sid': call.sid,
                'status': call.status,
                'from': self.from_number,
                'to': to_number,
                'start_time': call.date_created
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error making call: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error making call: {e}")
            return None
    
    def get_call_status(self, call_sid: str) -> Optional[str]:
        """Get the current status of a call.
        
        Args:
            call_sid: Call SID
            
        Returns:
            Call status string or None
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return call.status
        except Exception as e:
            logger.error(f"Error fetching call status: {e}")
            return None
    
    def wait_for_call_completion(self, call_sid: str, max_wait: int = 300) -> bool:
        """Wait for a call to complete.
        
        Args:
            call_sid: Call SID
            max_wait: Maximum wait time in seconds
            
        Returns:
            True if call completed, False otherwise
        """
        logger.info(f"Waiting for call {call_sid} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.get_call_status(call_sid)
            
            if status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                logger.info(f"Call {call_sid} ended with status: {status}")
                return status == 'completed'
            
            time.sleep(5)
        
        logger.warning(f"Call {call_sid} did not complete within {max_wait}s")
        return False
    
    def get_call_recordings(self, call_sid: str) -> list:
        """Get recordings for a specific call.
        
        Args:
            call_sid: Call SID
            
        Returns:
            List of recording objects
        """
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            return recordings
        except Exception as e:
            logger.error(f"Error fetching recordings: {e}")
            return []
    
    def download_recording(
        self,
        recording_sid: str,
        output_path: Path,
        format: str = "mp3"
    ) -> bool:
        """Download a recording to file.
        
        Args:
            recording_sid: Recording SID
            output_path: Path to save the recording
            format: Audio format (mp3 or wav)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Construct recording URL
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Recordings/{recording_sid}.{format}"
            
            logger.info(f"Downloading recording {recording_sid} to {output_path}")
            
            response = requests.get(url, auth=(self.account_sid, self.auth_token))
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)
            
            logger.info(f"Recording saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading recording: {e}")
            return False
    
    def get_call_transcription(self, call_sid: str) -> Optional[str]:
        """Get transcription for a call if available.
        
        Args:
            call_sid: Call SID
            
        Returns:
            Transcription text or None
        """
        try:
            recordings = self.get_call_recordings(call_sid)
            
            for recording in recordings:
                # Try to get transcriptions for this recording
                transcriptions = self.client.transcriptions.list(
                    recording_sid=recording.sid
                )
                
                if transcriptions:
                    return transcriptions[0].transcription_text
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching transcription: {e}")
            return None
