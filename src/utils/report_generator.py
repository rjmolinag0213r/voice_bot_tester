"""Report generation for test results and bug findings."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from src.utils.bug_detector import Bug, BugSeverity
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ReportGenerator:
    """Generates reports from test results."""
    
    def __init__(self, output_dir: Path = Path("reports")):
        """Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Report generator initialized with output dir: {output_dir}")
    
    def generate_bug_report(
        self,
        bugs: List[Bug],
        test_summary: Dict[str, Any],
        output_filename: str = "bug_report.md"
    ) -> Path:
        """Generate a comprehensive bug report.
        
        Args:
            bugs: List of detected bugs
            test_summary: Summary of test execution
            output_filename: Output file name
            
        Returns:
            Path to generated report
        """
        logger.info(f"Generating bug report with {len(bugs)} bugs...")
        
        report_path = self.output_dir / output_filename
        
        with open(report_path, 'w') as f:
            # Header
            f.write("# Voice Bot Testing - Bug Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Calls Made:** {test_summary.get('total_calls', 0)}\n")
            f.write(f"- **Total Bugs Found:** {len(bugs)}\n")
            f.write(f"- **Critical Bugs:** {len([b for b in bugs if b.severity == BugSeverity.CRITICAL])}\n")
            f.write(f"- **High Severity Bugs:** {len([b for b in bugs if b.severity == BugSeverity.HIGH])}\n")
            f.write(f"- **Medium Severity Bugs:** {len([b for b in bugs if b.severity == BugSeverity.MEDIUM])}\n")
            f.write(f"- **Low Severity Bugs:** {len([b for b in bugs if b.severity == BugSeverity.LOW])}\n")
            f.write("\n")
            
            # Test Coverage
            f.write("## Test Coverage\n\n")
            f.write("The following patient personas were used to test the AI receptionist:\n\n")
            for persona in test_summary.get('personas_tested', []):
                f.write(f"- **{persona['name']}**: {persona['description']}\n")
            f.write("\n")
            
            # Bugs by Severity
            f.write("## Detailed Bug Reports\n\n")
            
            for severity in [BugSeverity.CRITICAL, BugSeverity.HIGH, BugSeverity.MEDIUM, BugSeverity.LOW]:
                severity_bugs = [b for b in bugs if b.severity == severity]
                if not severity_bugs:
                    continue
                
                f.write(f"### {severity.value} Severity Issues\n\n")
                
                for i, bug in enumerate(severity_bugs, 1):
                    f.write(f"#### {i}. {bug.title}\n\n")
                    f.write(f"**Severity:** {bug.severity.value}\n\n")
                    f.write(f"**Call ID:** {bug.call_id}\n\n")
                    f.write(f"**Persona:** {bug.persona}\n\n")
                    f.write(f"**Description:**\n{bug.description}\n\n")
                    f.write(f"**Evidence:**\n```\n{bug.evidence}\n```\n\n")
                    f.write("---\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            if any(b.severity == BugSeverity.CRITICAL for b in bugs):
                f.write("### Critical Issues Requiring Immediate Attention\n\n")
                f.write("The following critical issues were found and should be addressed immediately:\n\n")
                for bug in [b for b in bugs if b.severity == BugSeverity.CRITICAL]:
                    f.write(f"- {bug.title}\n")
                f.write("\n")
            
            if any(b.severity == BugSeverity.HIGH for b in bugs):
                f.write("### High Priority Improvements\n\n")
                f.write("These high-priority issues significantly impact user experience:\n\n")
                for bug in [b for b in bugs if b.severity == BugSeverity.HIGH]:
                    f.write(f"- {bug.title}\n")
                f.write("\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. Review all critical and high severity bugs\n")
            f.write("2. Prioritize fixes based on user impact\n")
            f.write("3. Implement fixes and re-test with the same personas\n")
            f.write("4. Consider expanding test coverage with additional edge cases\n")
        
        logger.info(f"Bug report saved to: {report_path}")
        return report_path
    
    def generate_json_report(
        self,
        bugs: List[Bug],
        test_summary: Dict[str, Any],
        output_filename: str = "test_results.json"
    ) -> Path:
        """Generate a JSON report for programmatic access.
        
        Args:
            bugs: List of detected bugs
            test_summary: Summary of test execution
            output_filename: Output file name
            
        Returns:
            Path to generated report
        """
        report_path = self.output_dir / output_filename
        
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'summary': test_summary,
            'bugs': [bug.to_dict() for bug in bugs],
            'statistics': {
                'total_bugs': len(bugs),
                'by_severity': {
                    'critical': len([b for b in bugs if b.severity == BugSeverity.CRITICAL]),
                    'high': len([b for b in bugs if b.severity == BugSeverity.HIGH]),
                    'medium': len([b for b in bugs if b.severity == BugSeverity.MEDIUM]),
                    'low': len([b for b in bugs if b.severity == BugSeverity.LOW])
                }
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"JSON report saved to: {report_path}")
        return report_path
    
    def save_transcript(
        self,
        call_id: str,
        persona_name: str,
        transcript: str,
        output_filename: str = None
    ) -> Path:
        """Save a call transcript.
        
        Args:
            call_id: Call identifier
            persona_name: Name of persona used
            transcript: Transcript text
            output_filename: Optional custom filename
            
        Returns:
            Path to saved transcript
        """
        if not output_filename:
            output_filename = f"transcript_{call_id}.txt"
        
        transcript_path = self.output_dir / output_filename
        
        with open(transcript_path, 'w') as f:
            f.write(f"Call ID: {call_id}\n")
            f.write(f"Persona: {persona_name}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            f.write(transcript)
        
        return transcript_path
