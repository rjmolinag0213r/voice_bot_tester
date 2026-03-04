#!/usr/bin/env python3
"""Main entry point for the Voice Bot Testing System."""
import sys
import argparse
from pathlib import Path

from src.config import get_settings
from src.call_orchestrator import CallOrchestrator
from src.personas.persona_factory import PersonaFactory
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║       Voice Bot Testing System v1.0.0                    ║
    ║       Pretty Good AI - Engineering Challenge             ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def list_personas():
    """List all available personas."""
    print("\nAvailable Patient Personas:\n")
    print("="*80)
    
    personas = PersonaFactory.get_all_personas()
    for i, persona in enumerate(personas, 1):
        print(f"\n{i}. {persona.name}")
        print(f"   Description: {persona.description}")
        print(f"   Testing Goal: {persona.get_testing_goal()}")
    
    print("\n" + "="*80)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Voice Bot Testing System for Pretty Good AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py run --calls 12
  python main.py list-personas
  python main.py run --calls 10 --verbose
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the test suite')
    run_parser.add_argument(
        '--calls',
        type=int,
        help='Number of calls to make (default from .env)'
    )
    run_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    # List personas command
    subparsers.add_parser('list-personas', help='List all available patient personas')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    print_banner()
    
    try:
        if args.command == 'list-personas':
            list_personas()
            return 0
        
        elif args.command == 'run':
            # Load settings
            logger.info("Loading configuration...")
            settings = get_settings()
            
            # Create orchestrator
            orchestrator = CallOrchestrator(settings)
            
            # Run tests
            num_calls = args.calls if args.calls else None
            summary = orchestrator.run_test_suite(num_calls=num_calls)
            
            # Print summary
            print("\n" + "="*80)
            print("TEST EXECUTION SUMMARY")
            print("="*80)
            print(f"Total Calls: {summary['total_calls']}")
            print(f"Successful: {summary['successful_calls']}")
            print(f"Failed: {summary['failed_calls']}")
            print(f"Total Bugs Found: {summary['total_bugs_found']}")
            print("\nReports have been generated in the 'reports/' directory.")
            print("="*80)
            
            return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
