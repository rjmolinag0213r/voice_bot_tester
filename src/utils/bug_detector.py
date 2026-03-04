"""Bug detection system for analyzing call transcripts."""
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BugSeverity(Enum):
    """Bug severity levels."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Bug:
    """Represents a detected bug."""
    title: str
    severity: BugSeverity
    description: str
    evidence: str
    call_id: str
    persona: str
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'call_id': self.call_id,
            'persona': self.persona,
            'timestamp': self.timestamp
        }


class BugDetector:
    """Analyzes call transcripts for potential bugs."""
    
    # Patterns for detecting common issues
    WEEKEND_DAYS = r'\b(saturday|sunday|weekend)\b'
    LATE_HOURS = r'\b([7-9]|1[0-2])\s*(?:pm|p\.m\.)\b'
    EARLY_HOURS = r'\b([5-7])\s*(?:am|a\.m\.)\b'
    CONFIRMATION_WORDS = r'\b(confirmed|scheduled|booked|set up|all set)\b'
    
    def __init__(self):
        """Initialize bug detector."""
        self.bugs: List[Bug] = []
        logger.info("Bug detector initialized")
    
    def analyze_call(
        self,
        transcript: str,
        call_id: str,
        persona_name: str,
        persona_goal: str
    ) -> List[Bug]:
        """Analyze a call transcript for bugs.
        
        Args:
            transcript: Call transcript text
            call_id: Unique call identifier
            persona_name: Name of the persona used
            persona_goal: Testing goal of the persona
            
        Returns:
            List of detected bugs
        """
        logger.info(f"Analyzing call {call_id} for bugs...")
        call_bugs = []
        
        # Detect office hours violations
        if persona_name == "The Scheduler":
            call_bugs.extend(self._detect_office_hours_bugs(transcript, call_id, persona_name))
        
        # Detect medication handling issues
        elif persona_name == "The Refiller":
            call_bugs.extend(self._detect_medication_bugs(transcript, call_id, persona_name))
        
        # Detect multi-topic handling issues
        elif persona_name == "The Confused Senior":
            call_bugs.extend(self._detect_context_bugs(transcript, call_id, persona_name))
        
        # Detect error handling issues
        elif persona_name == "The Edge-Case":
            call_bugs.extend(self._detect_edge_case_bugs(transcript, call_id, persona_name))
        
        # General bug detection
        call_bugs.extend(self._detect_general_bugs(transcript, call_id, persona_name))
        
        self.bugs.extend(call_bugs)
        logger.info(f"Found {len(call_bugs)} potential bugs in call {call_id}")
        
        return call_bugs
    
    def _detect_office_hours_bugs(self, transcript: str, call_id: str, persona: str) -> List[Bug]:
        """Detect bugs related to office hours scheduling."""
        bugs = []
        transcript_lower = transcript.lower()
        
        # Check for weekend appointments being confirmed
        if re.search(self.WEEKEND_DAYS, transcript_lower) and \
           re.search(self.CONFIRMATION_WORDS, transcript_lower):
            
            # Extract relevant context
            lines = transcript.split('\n')
            evidence_lines = [l for l in lines if re.search(self.WEEKEND_DAYS, l.lower()) or 
                            re.search(self.CONFIRMATION_WORDS, l.lower())]
            evidence = '\n'.join(evidence_lines[:3]) if evidence_lines else "See full transcript"
            
            bugs.append(Bug(
                title="Appointment scheduled outside office hours (Weekend)",
                severity=BugSeverity.HIGH,
                description="AI confirmed an appointment for a weekend day. Medical offices are typically closed on weekends. The AI should inform the patient about office hours and offer weekday alternatives.",
                evidence=evidence,
                call_id=call_id,
                persona=persona
            ))
        
        # Check for late evening appointments
        if re.search(self.LATE_HOURS, transcript_lower) and \
           re.search(self.CONFIRMATION_WORDS, transcript_lower):
            
            lines = transcript.split('\n')
            evidence_lines = [l for l in lines if re.search(self.LATE_HOURS, l.lower()) or 
                            re.search(self.CONFIRMATION_WORDS, l.lower())]
            evidence = '\n'.join(evidence_lines[:3]) if evidence_lines else "See full transcript"
            
            bugs.append(Bug(
                title="Appointment scheduled outside office hours (Late evening)",
                severity=BugSeverity.HIGH,
                description="AI confirmed an appointment for late evening (7pm or later). Most medical offices close by 5-6pm. The AI should verify office hours before confirming.",
                evidence=evidence,
                call_id=call_id,
                persona=persona
            ))
        
        return bugs
    
    def _detect_medication_bugs(self, transcript: str, call_id: str, persona: str) -> List[Bug]:
        """Detect bugs related to medication refills."""
        bugs = []
        transcript_lower = transcript.lower()
        
        # Check if refill was confirmed without dosage verification
        refill_keywords = r'\b(refill|prescription|medication)\b'
        dosage_keywords = r'\b(dosage|milligram|mg|dose|strength)\b'
        
        if re.search(refill_keywords, transcript_lower) and \
           re.search(self.CONFIRMATION_WORDS, transcript_lower):
            
            # Check if dosage was discussed
            if not re.search(dosage_keywords, transcript_lower):
                bugs.append(Bug(
                    title="Medication refill confirmed without dosage verification",
                    severity=BugSeverity.CRITICAL,
                    description="AI confirmed a prescription refill without verifying the medication dosage. This is a critical safety issue as incorrect dosages can be harmful.",
                    evidence="Refill confirmed without dosage discussion - see full transcript",
                    call_id=call_id,
                    persona=persona
                ))
        
        return bugs
    
    def _detect_context_bugs(self, transcript: str, call_id: str, persona: str) -> List[Bug]:
        """Detect bugs related to multi-topic conversations."""
        bugs = []
        
        # Check if multiple questions were asked
        question_marks = transcript.count('?')
        if question_marks >= 3:
            # Check if AI addressed all questions
            # This is a heuristic - in real implementation, you'd use NLP
            logger.info(f"Call {call_id} contained {question_marks} questions - checking if all were addressed")
        
        return bugs
    
    def _detect_edge_case_bugs(self, transcript: str, call_id: str, persona: str) -> List[Bug]:
        """Detect bugs related to edge cases and unusual requests."""
        bugs = []
        transcript_lower = transcript.lower()
        
        # Check for signs of confusion when patient changes mind
        change_mind_keywords = r'\b(actually|wait|never mind|on second thought|change)\b'
        confusion_signs = r'\b(confused|what|huh|understand)\b'
        
        if re.search(change_mind_keywords, transcript_lower, re.IGNORECASE):
            if re.search(confusion_signs, transcript_lower, re.IGNORECASE):
                bugs.append(Bug(
                    title="AI showed confusion when patient changed their mind",
                    severity=BugSeverity.MEDIUM,
                    description="When the patient changed their mind or interrupted, the AI showed signs of confusion or didn't handle the change gracefully.",
                    evidence="See transcript for change-of-mind handling",
                    call_id=call_id,
                    persona=persona
                ))
        
        return bugs
    
    def _detect_general_bugs(self, transcript: str, call_id: str, persona: str) -> List[Bug]:
        """Detect general bugs across all personas."""
        bugs = []
        transcript_lower = transcript.lower()
        
        # Check for error messages or system failures
        error_keywords = r'\b(error|failed|sorry|cannot|unable|don\'t understand)\b'
        if transcript_lower.count('error') > 2 or transcript_lower.count('sorry') > 3:
            bugs.append(Bug(
                title="Excessive errors or apologies in conversation",
                severity=BugSeverity.MEDIUM,
                description="The AI showed multiple errors or apologized excessively, indicating poor conversation handling.",
                evidence="Multiple error indicators - see full transcript",
                call_id=call_id,
                persona=persona
            ))
        
        return bugs
    
    def get_all_bugs(self) -> List[Bug]:
        """Get all detected bugs."""
        return self.bugs
    
    def get_bugs_by_severity(self, severity: BugSeverity) -> List[Bug]:
        """Get bugs filtered by severity."""
        return [bug for bug in self.bugs if bug.severity == severity]
