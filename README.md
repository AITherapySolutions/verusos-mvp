# VerusOS Safety Filter

**Real-time safety detection for companion AI platforms.**

Context-aware API that catches what keyword filters miss — crisis signals, grooming patterns, and high-risk content — while avoiding false positives on safe content like song lyrics and roleplay.

---

## Why VerusOS?

Generic keyword filters have two failure modes:
- **False positives:** Flagging "I want to die laughing" as a crisis
- **False negatives:** Missing subtle grooming like "You're so mature for your age"

VerusOS solves both with context-aware detection built by a licensed mental health counselor with 30 years of crisis response experience.

---

## Performance

| Metric | Result |
|--------|--------|
| Crisis Detection | 100% recall |
| Grooming Detection | 80% recall |
| Response Time | <200ms |

---

## Quick Start

```bash
curl -X POST https://VerusosSafety.replit.app/api/v1/detect \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "session_id": "session-001",
    "user_id_hash": "user-abc123",
    "message": {
      "role": "user",
      "content": "I don'\''t want to be here anymore"
    },
    "context": {
      "time_of_day": "3am"
    }
  }'
```

### Response

```json
{
  "risk_level": "RED",
  "risk_score": 92,
  "categories": {
    "crisis_detected": true,
    "grooming_detected": false
  },
  "recommended_action": "escalate",
  "explanation": "Direct expression of hopelessness with high-risk time context"
}
```

---

## What It Detects

### Crisis Signals
- Suicidal ideation (direct and indirect)
- Self-harm references
- Hopelessness and despair patterns

### Grooming Patterns
- Age-inappropriate compliments
- Isolation tactics
- Boundary testing
- Requests for personal information

### Context Awareness
- Distinguishes song lyrics from real distress
- Recognizes roleplay vs. genuine statements
- Adjusts risk based on time of day, session patterns

---

## Integration

VerusOS integrates with any platform via REST API. One endpoint, instant response.

**Supported frameworks:**
- Python
- Node.js
- Any HTTP client

See [Integration Guide](docs/integration-guide.md) for full documentation.

---

## Pricing

**Founder Pricing (through January 31, 2026):** $28,000/year

Includes:
- Unlimited API calls
- Crisis + Grooming detection
- Context-aware analysis
- Dashboard + Audit logging
- Integration support

[Book a Demo](https://calendly.com/tammy-aitherapysolutions/30min)

---

## About

Built by **Tammy Horn, LMHC** — 30 years of crisis response experience, licensed mental health counselor.

VerusOS is a product of AI Therapy Solutions, LLC.

---

## Contact

- **Email:** tammy@aitherapysolutions.com
- **Demo:** [Book 30 minutes](https://calendly.com/tammy-aitherapysolutions/30min)
- **Video:** [24-second demo](https://streamable.com/mpmm38)

---

## License

Proprietary. Contact for licensing inquiries.
