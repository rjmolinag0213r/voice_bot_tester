# Voice Bot Testing System

> Automated testing system for AI voice receptionists using realistic patient personas

## Overview

This system automates the testing of AI voice receptionists by simulating realistic patient conversations using various personas. It makes actual phone calls, records conversations, analyzes them for bugs, and generates comprehensive reports.

**Built for:** Pretty Good AI Engineering Challenge

## Features

✅ **4 Distinct Patient Personas**
- **The Scheduler** - Tests office hours validation (weekend/evening appointments)
- **The Refiller** - Tests medication handling with vague information
- **The Confused Senior** - Tests multi-topic conversation handling
- **The Edge-Case** - Tests error handling with interruptions and changes

✅ **Automated Testing**
- Makes 10+ test calls automatically
- Distributes calls evenly across personas
- Natural conversation flow with realistic speech patterns

✅ **Comprehensive Analysis**
- Automatic bug detection using pattern matching and heuristics
- Severity classification (Critical, High, Medium, Low)
- Evidence extraction from conversations

✅ **Professional Reporting**
- Markdown bug reports with detailed findings
- JSON reports for programmatic analysis
- Individual call transcripts for review

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Twilio account with phone number
- OpenRouter API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd voice_bot_tester
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   OPENROUTER_API_KEY=your_openrouter_key
   ```

### Usage

**Run the complete test suite:**
```bash
python main.py run
```

**Run with specific number of calls:**
```bash
python main.py run --calls 15
```

**List available personas:**
```bash
python main.py list-personas
```

**Run with verbose logging:**
```bash
python main.py run --verbose
```

## Project Structure

```
voice_bot_tester/
├── src/
│   ├── integrations/          # Twilio & OpenRouter clients
│   │   ├── twilio_client.py   # Call management
│   │   └── openrouter_client.py  # LLM integration
│   ├── personas/              # Patient personas
│   │   ├── base_persona.py    # Base class
│   │   ├── scheduler.py       # Office hours tester
│   │   ├── refiller.py        # Medication tester
│   │   ├── confused_senior.py # Multi-topic tester
│   │   ├── edge_case.py       # Edge case tester
│   │   └── persona_factory.py # Persona management
│   ├── utils/                 # Utilities
│   │   ├── logger.py          # Logging setup
│   │   ├── transcription.py   # Audio transcription
│   │   ├── bug_detector.py    # Bug analysis
│   │   └── report_generator.py # Report creation
│   ├── config.py              # Configuration management
│   └── call_orchestrator.py   # Main orchestration logic
├── recordings/                # Call recordings (generated)
├── reports/                   # Test reports (generated)
├── logs/                      # Application logs (generated)
├── docs/                      # Documentation
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options:

| Variable | Description | Default |
|----------|-------------|----------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID | Required |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | Required |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number | Required |
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `TARGET_PHONE_NUMBER` | Number to call for testing | +18054398008 |
| `LLM_MODEL` | LLM model to use | anthropic/claude-3.5-sonnet |
| `LLM_TEMPERATURE` | Sampling temperature | 0.8 |
| `MIN_CALL_DURATION` | Minimum call length (seconds) | 60 |
| `MAX_CALL_DURATION` | Maximum call length (seconds) | 180 |
| `TOTAL_CALLS` | Default number of calls | 12 |

## Output

After running tests, you'll find:

**Reports Directory (`reports/`):**
- `bug_report.md` - Comprehensive bug report with findings
- `test_results.json` - Machine-readable test results
- `transcript_*.txt` - Individual call transcripts

**Logs Directory (`logs/`):**
- Detailed execution logs with timestamps

**Recordings Directory (`recordings/`):**
- Audio recordings of calls (if enabled)

## Patient Personas

### 1. The Scheduler
**Goal:** Test office hours validation

- Requests weekend appointments (Saturday/Sunday)
- Asks for late evening appointments (7-8pm)
- Requests very early morning slots (6-7am)
- Tests if AI incorrectly confirms appointments outside business hours

### 2. The Refiller
**Goal:** Test medication handling

- Needs prescription refill but vague about dosage
- Mentions "little white pill" without specifics
- Unsure if medication is 10mg or 20mg
- Tests if AI processes refills without proper verification

### 3. The Confused Senior
**Goal:** Test multi-topic handling

- Asks multiple questions in rambling manner
- Jumps between topics (Medicare, parking, location)
- Tells tangential stories
- Tests if AI maintains context and answers all questions

### 4. The Edge-Case
**Goal:** Test error handling

- Changes mind mid-conversation
- Interrupts frequently ("wait," "actually")
- Asks unusual boundary-case questions
- Tests if AI handles chaos gracefully

## Bug Detection

The system automatically detects:

- ❌ **Office Hours Violations** - Appointments outside business hours
- ❌ **Medication Safety Issues** - Refills without dosage verification
- ❌ **Context Loss** - Failing to address multiple questions
- ❌ **Poor Error Handling** - Confusion when requests change
- ❌ **General Issues** - Excessive errors or apologies

Each bug includes:
- Severity level (Critical/High/Medium/Low)
- Clear description
- Evidence from transcript
- Call ID for reference

## Development

**Run tests:**
```bash
python -m pytest tests/
```

**Code structure:**
- Clean, readable Python with type hints
- Comprehensive error handling and logging
- Modular design with clear separation of concerns
- Extensible persona system for adding new test cases

## Troubleshooting

**"ModuleNotFoundError" when running:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**"Twilio authentication failed":**
- Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in `.env`
- Check credentials in Twilio console

**"OpenRouter API error":**
- Verify `OPENROUTER_API_KEY` is correct
- Ensure you have API credits

**No recordings generated:**
- Check Twilio recording settings
- Verify network connectivity

## Cost Estimation

Typical costs for 10-15 test calls:
- **Twilio calls:** ~$0.02-0.05 per minute = $1-3
- **OpenRouter LLM:** ~$0.50-2 per call = $5-15
- **Total:** $10-20 for complete test suite

## Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design decisions and system architecture.

## License

MIT License - see LICENSE file for details

## Author

Built for Pretty Good AI Engineering Challenge

## Support

For questions or issues:
- Check existing issues in repository
- Review ARCHITECTURE.md for design decisions
- Contact: kevin@prettygoodai.com
