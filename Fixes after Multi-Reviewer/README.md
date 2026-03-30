# MBTI Theory Quiz

A terminal-based quiz app that helps you learn to identify people's MBTI personality types. Work through sections covering MBTI basics, cognitive functions, stereotypes, behaviors, and observable traits — then get personalized tips based on your own type.
Apart from the main reviewer, I used three specific agents to review.

## Requirements

- Python 3.7+
- No external dependencies (uses only the standard library)

## Usage

```bash
python quiz.py
```

## How It Works

1. **Create an account** — enter your name, email, password, and select your MBTI type.
2. **Log in** — use your email and password.
3. **Take quizzes** — work through sections in order, or browse and pick any section.
4. **See results** — after each section you get your score, correct answers for anything you missed, and a personalized tip.
5. **Track progress** — your dashboard shows completed sections, scores, and skills learned.

## Quiz Sections (in sequential order)

1. MBTI Basics
2. Cognitive Functions
3. Stereotypes
4. MBTI Behaviors
5. Traits to Look For

## File Structure

| File | Purpose |
|------|---------|
| `quiz.py` | Main application — all app logic |
| `questions.json` | Question bank (25 questions across 5 sections) |
| `tips.json` | Personalized MBTI tips for all 16 types |
| `users.dat` | User accounts (binary/pickle, passwords are hashed) |
| `scores.dat` | Score history per user (binary/pickle) |
| `feedback.json` | Section ratings from users |
| `SPEC.md` | Full specification and acceptance criteria |
| `REVIEW.md` | Code review against the spec |
