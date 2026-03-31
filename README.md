# Auto Google Form Complete

An AI-powered bot that automatically fills and submits a 73-question academic Google Form from **9 different psychological perspectives**. Built for a research study examining the relationship between future anxiety, social media usage purposes, and general self-efficacy among university students.

## How It Works

1. **AI generates responses** — A large language model role-plays as a Turkish university student whose natural thinking aligns with a specific psychological approach
2. **Validates all answers** — Ensures every response matches the form's valid options (Likert scales, multiple choice, etc.)
3. **Submits page by page** — Handles Google Forms' multi-page structure with proper session tokens (`fbzx`), sub-entry IDs, and page history

## Supported Psychological Perspectives

| Key | Perspective | Anxiety Level | Self-Efficacy |
|-----|------------|---------------|---------------|
| `cbt` | Cognitive-Behavioral (CBT) | Moderate | High |
| `psychodynamic` | Psychodynamic | High | Moderate |
| `humanistic` | Humanistic | Low | High |
| `existential` | Existential | Moderate-High | Moderate |
| `gestalt` | Gestalt | Low | High |
| `systemic` | Systemic | Moderate | Context-dependent |
| `emdr` | EMDR | High | Developing |
| `behavioral` | Behavioral | Moderate | Moderate-High |
| `solution_focused` | Solution-Focused | Low | High |

## Form Structure (73 Questions)

| Section | Questions | Scale |
|---------|-----------|-------|
| Consent | 1 | Checkbox |
| Demographics | 10 | Multiple choice / Open |
| Future Anxiety Scale | 19 | 5-point Likert (Never → Always) |
| Social Network Usage Purposes | 26 | 7-point Likert (1–7) |
| General Self-Efficacy Scale | 17 | 5-point Likert (1–5) |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file with your API key (at least one)
GROQ_API_KEY=your-groq-key        # Free — recommended
GEMINI_API_KEY=your-gemini-key     # Free tier available
ANTHROPIC_API_KEY=your-claude-key  # Paid
```

**Get a free API key:**
- **Groq** (recommended): https://console.groq.com/keys
- **Gemini**: https://aistudio.google.com/apikey
- **Anthropic**: https://console.anthropic.com

The bot auto-detects which key is available (priority: Groq > Gemini > Claude).

## Usage

```bash
# Single perspective
python main.py --perspective cbt

# All 9 perspectives
python main.py --all

# Multiple submissions of the same perspective
python main.py --perspective gestalt --count 5

# Dry run — generate answers without submitting
python main.py --perspective cbt --dry-run
```

## Project Structure

```
├── config.py          # Form schema: 73 entry IDs, questions, valid options
├── perspectives.py    # 9 psychological approach definitions + system prompts
├── generator.py       # AI response generation with validation & retry
├── submitter.py       # Multi-page Google Forms submission (session + tokens)
├── main.py            # CLI orchestrator (argparse)
├── requirements.txt   # Dependencies
├── .env               # API keys (not tracked by git)
└── logs/              # Submission logs as JSON (auto-created)
```

## How Submission Works

Google Forms with multiple pages reject a single flat POST. This bot:

1. **GETs** the form to obtain a session cookie and `fbzx` token
2. **POSTs** each page sequentially with the correct `pageHistory` and `partialResponse`
3. Uses **sub-entry IDs** (not the top-level entry IDs) as field names
4. Adds `_sentinel` fields for checkbox inputs
5. Validates the final response for the confirmation message

## Logs

Every submission is saved to `logs/{perspective}_{timestamp}.json` containing:
- The perspective used
- All 73 generated answers
- Submission result (success/failure, HTTP status)
