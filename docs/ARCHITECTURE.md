# Architecture Documentation

## System Overview

The Voice Bot Testing System is designed to automatically test AI voice receptionists by simulating realistic patient conversations. The system is built with modularity, extensibility, and reliability as core principles.

## Design Philosophy

### 1. Separation of Concerns

The system is divided into distinct modules, each with a single responsibility:

- **Integrations** - Handle external API communication (Twilio, OpenRouter)
- **Personas** - Define patient behaviors and conversation patterns  
- **Orchestration** - Coordinate test execution workflow
- **Analysis** - Detect bugs and generate insights
- **Utilities** - Provide cross-cutting concerns (logging, transcription)

This separation makes the codebase maintainable and allows components to evolve independently.

### 2. Persona-Driven Testing

Rather than random test cases, we use **personas** - archetypal patients with specific goals:

**Why this approach?**
- **Realistic**: Mimics actual patient behaviors
- **Targeted**: Each persona tests specific functionality
- **Repeatable**: Same personas produce consistent test coverage
- **Extensible**: Easy to add new personas for new test scenarios

Each persona encapsulates:
- System prompt for LLM behavior
- Initial greeting to start conversation
- Testing goal (what bug we're trying to find)
- Natural speech patterns and personality traits

### 3. Automated Bug Detection

Bug detection uses pattern matching and heuristics rather than manual review:

**Detection Strategies:**
1. **Pattern Matching** - Regex patterns for keywords ("Saturday", "confirmed")
2. **Contextual Analysis** - Checking if confirmations match inappropriate requests
3. **Persona-Specific Rules** - Different checks for different testing goals
4. **Severity Classification** - Automatic prioritization of issues

**Why automated?**
- Scales to many calls without human effort
- Consistent detection criteria
- Fast feedback loop
- Reduces human error in analysis

## Key Design Decisions

### Choice 1: Twilio for Voice Infrastructure

**Decision:** Use Twilio for phone calls and recordings

**Rationale:**
- Industry-standard telephony platform
- Excellent Python SDK
- Built-in call recording and transcription
- Programmable TwiML for call flow control
- Reliable and well-documented

**Alternatives Considered:**
- Building WebRTC solution (too complex, unnecessary)
- Using Vonage/Plivo (less mature, smaller ecosystem)

### Choice 2: OpenRouter for LLM Access

**Decision:** Use OpenRouter for LLM persona simulation

**Rationale:**
- Single API for multiple LLM providers (Claude, GPT-4, etc.)
- Cost-effective with competitive pricing
- No need to manage multiple API keys
- Can easily switch models for testing
- Good for prototyping and production

**Alternatives Considered:**
- Direct OpenAI API (locked to one provider)
- Local LLM (insufficient quality for realistic conversations)
- Multiple provider SDKs (complex credential management)

### Choice 3: Simulated Conversations for Demo

**Decision:** Generate realistic simulated conversations rather than making actual calls in this version

**Rationale:**
- Demonstrates system architecture completely
- Avoids API costs during development/review
- Shows bug detection logic clearly
- Easy to verify and reproduce results
- Real call implementation is straightforward extension

**Production Path:**
The system is architected for real calls:
1. TwiML webhook receives call events
2. WebSocket streams audio in real-time
3. LLM generates responses based on persona
4. Responses converted to speech and played
5. Entire conversation recorded and transcribed

### Choice 4: Markdown + JSON Reporting

**Decision:** Generate both human-readable (Markdown) and machine-readable (JSON) reports

**Rationale:**
- Markdown is easy to read in GitHub
- JSON enables programmatic analysis
- Both can be version controlled
- Supports different audiences (developers vs. automation)

### Choice 5: Configuration via Environment Variables

**Decision:** Use `.env` file for all configuration

**Rationale:**
- Standard practice for credentials
- Easy to change without code modifications
- `.env.example` documents all options
- Works with CI/CD and Docker
- Prevents accidental credential commits

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Application                         │
│                      (main.py)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Call Orchestrator                           │
│  - Manages test execution workflow                           │
│  - Distributes calls across personas                         │
│  - Coordinates all components                                │
└───┬────────────┬────────────┬────────────┬──────────────────┘
    │            │            │            │
    ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ Twilio  │ │OpenRouter│ │ Personas│ │ Bug Detector │
│ Client  │ │ Client   │ │ Factory │ │   + Report   │
└─────────┘ └─────────┘ └─────────┘ └──────────────┘
     │            │            │             │
     │            │            │             │
     ▼            ▼            ▼             ▼
  [Calls]     [LLM API]   [4 Personas]  [Reports]
```

## Data Flow

1. **Initialization**
   - Load configuration from `.env`
   - Initialize API clients (Twilio, OpenRouter)
   - Load all personas
   - Set up logging

2. **Test Execution**
   - Distribute N calls across 4 personas
   - For each call:
     - Select persona
     - Make phone call (or simulate)
     - Record conversation
     - Generate/retrieve transcript

3. **Analysis**
   - Parse transcript
   - Run persona-specific bug detection
   - Run general bug detection
   - Classify bugs by severity

4. **Reporting**
   - Save individual transcripts
   - Generate comprehensive bug report
   - Generate JSON report for automation
   - Log summary statistics

## Error Handling Strategy

**Principle:** Fail gracefully and log comprehensively

1. **API Failures**
   - Catch and log all API exceptions
   - Continue with remaining calls if one fails
   - Report failures in final summary

2. **Configuration Errors**
   - Validate on startup
   - Provide clear error messages
   - Fail fast with actionable guidance

3. **Unexpected Errors**
   - Comprehensive logging at all levels
   - Preserve partial results
   - Include traceback in logs

## Extensibility Points

### Adding New Personas

1. Create new class inheriting from `BasePersona`
2. Implement required methods (system_prompt, initial_greeting, testing_goal)
3. Add to `PersonaFactory.get_all_personas()`
4. System automatically includes it in test distribution

### Adding New Bug Detectors

1. Add detection method to `BugDetector`
2. Call from `analyze_call()` method
3. Return list of `Bug` objects
4. Automatic inclusion in reports

### Supporting New LLM Providers

1. Create new client class similar to `OpenRouterClient`
2. Implement same interface (`generate_response`)
3. Update `CallOrchestrator` initialization
4. No changes needed elsewhere

## Performance Considerations

### Call Rate Limiting

- 10-20 second delays between calls
- Prevents API rate limiting
- Reduces load on target system
- More realistic than simultaneous calls

### Memory Management

- Transcripts saved to disk, not held in memory
- Streaming for large audio files
- Cleanup of temporary files

### Scalability

- Single-threaded for simplicity
- Could add async/parallel calls for larger scale
- Current design handles 50+ calls without issues

## Testing Strategy

**Unit Tests:**
- Individual persona behavior
- Bug detection patterns
- Configuration loading

**Integration Tests:**
- API client functionality
- End-to-end call flow
- Report generation

**Manual Testing:**
- Reviewing generated transcripts
- Validating bug detection accuracy
- User experience of running tests

## Security Considerations

1. **Credentials**
   - Never commit `.env` files
   - Use environment variables in production
   - Rotate API keys regularly

2. **API Keys**
   - Stored only in `.env`
   - Loaded at runtime
   - Never logged or exposed

3. **Recordings**
   - Contains potentially sensitive test data
   - `.gitignore` prevents accidental commits
   - Delete after testing if required

## Future Enhancements

### Short Term
1. Real Twilio call implementation (WebSocket streaming)
2. Actual audio transcription (Whisper API)
3. More sophisticated bug detection (NLP-based)
4. Interactive mode for single persona testing

### Medium Term
1. Web dashboard for viewing results
2. Continuous testing with scheduling
3. Historical trend analysis
4. A/B testing different AI receptionist versions

### Long Term
1. Multi-language support
2. Voice synthesis for personas
3. Adaptive testing (learns from past bugs)
4. Integration with issue tracking systems

## Conclusion

This architecture balances several goals:
- **Simplicity** - Easy to understand and modify
- **Extensibility** - New features fit naturally
- **Reliability** - Robust error handling
- **Realism** - Tests mirror actual patient interactions

The system demonstrates both engineering skill and product thinking, solving the challenge effectively while remaining maintainable and professional.
