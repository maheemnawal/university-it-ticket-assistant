---
title: University IT Ticket Assistant
sdk: docker
app_port: 7860
---
# University IT Help Desk Ticket Assistant

This app reads a university IT help desk ticket, picks one of 10 categories, and writes a one-sentence summary. The result is only a suggestion for a human to review. The app never performs real actions such as password resets or account changes. All 100 tickets are fictional.

## Mode

The app runs in **live** mode. It calls the Groq API with the model `openai/gpt-oss-20b`.

Settings go in a `.env` file (see `.env.example`):

```
BACKEND=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

- The real API key is never committed to GitHub.
- Nothing here is a trained model. Prompt v1 and v2 results come from a hosted LLM. The keyword baseline and TF-IDF are simple methods that are not trained.

## Project files

| File | Purpose |
|---|---|
| `service.py` | Prompts v1/v2, Pydantic `TicketResult`, model call |
| `api.py` | FastAPI app with `/analyze` and `/health` |
| `app.py` | Streamlit frontend |
| `evaluate.py` | Baseline, TF-IDF, prompt v1/v2 evaluation |
| `tests/test_api.py` | API tests |
| `tickets.csv` | 100 labeled tickets |
| `categories.csv` | 10 categories with meaning and example |
| `results/` | Confusion matrices (CSV) |
| `screenshots/` | Demo evidence |

## How to run

```
pip install -r requirements.txt
python evaluate.py
pytest tests
uvicorn api:app --reload
streamlit run app.py
```

- Backend runs at https://university-it-ticket-assistant-two.vercel.app/health (check `/health`).
- Frontend is Streamlit. If the backend is on another address, set `API_URL`.

## Deployment

- Backend on Render: start command `uvicorn api:app --host 0.0.0.0 --port $PORT`. The Groq key is added in Render's environment settings.
- Frontend on Streamlit Community Cloud, with `API_URL` set to the Render link in Secrets.
- Note: on the free Render plan the backend sleeps when idle, so the first request can take up to a minute.

**App link:** https://university-it-tickets.streamlit.app/

## Categories

There are 10 categories for university IT: `password_reset`, `wifi_network`, `email_issue`, `software_install`, `lms_access`, `printing`, `hardware_fault`, `vpn_remote`, `classroom_av`, `security_incident`.

Each one has a one-line meaning and an example in `categories.csv`.

## Dataset

`tickets.csv` has 100 tickets with the columns: id, ticket, expected_category, split.

- Exactly 10 tickets per category, so there is no imbalance.
- 80 tickets are `development` (8 per category) and 20 are `eval` (the last 2 per category).
- Eval labels were fixed before running any predictions and were not changed afterwards.

## Prompts

- **v1:** a short, basic instruction to pick a category and write a summary.
- **v2:** lists all 10 allowed categories with their meanings, asks for a one-sentence factual summary (max 25 words), says never to claim an action was completed, and sends the ticket separately inside `<ticket>` tags so the model treats it as data and not as instructions.

## Validation and errors

A Pydantic model `TicketResult` checks that:
- the category is one of the 10 allowed
- the summary is one sentence and not too long
- the summary does not claim things like "fixed", "resolved" or "reset"

| Situation | Response |
|---|---|
| Blank input | 400 |
| Invalid model output | 502 |
| Backend unavailable | 503 (the "Simulate backend failure" checkbox in the UI shows this) |

## Results (20 eval tickets, live mode)

| Method | Accuracy |
|---|---|
| Keyword baseline (1 keyword per category) | 0.50 |
| TF-IDF cosine 1-NN (development to eval) | 0.95 |
| Live prompt v1 | 0.00 |
| Live prompt v2 | 1.00 |

Confusion matrices are in `results/`:
- `confusion_keyword_baseline.csv`
- `confusion_tfidf_cosine_1nn.csv`
- `confusion_live_prompt_v1.csv`
- `confusion_live_prompt_v2.csv`

## Errors and limitations

1. **Prompt v1 scored 0.00 because of output format, not understanding.** The model wrote display names like "Password Reset" and "Phishing" instead of ids like `password_reset`. Pydantic rejected every answer, and rejected answers were counted as `unknown`, so the whole v1 confusion matrix sits in the `unknown` column. Prompt v2 lists the allowed categories, which fixed this.
2. **The keyword baseline returns `unknown` for 9 of 20 tickets** because it checks only one word per category. It also labels the phishing email as `email_issue`, because the word "email" is stronger than the security signs.
3. **TF-IDF 1-NN sends the Adobe license ticket to `wifi_network`.** It matched a WiFi ticket that shares common words, so it follows word overlap and not meaning.
4. **Prompt v2 got 20/20, but this is weak evidence.** There are only 20 eval tickets, so one mistake changes accuracy by 5 points. The tickets are written by us and may be easier than real tickets.

## Evidence

Screenshots are in `screenshots/`:
- `valid_200.png`: valid ticket with category and summary
- `blank_400.png`: blank input
- `invalid_output_502.png`: model output rejected (prompt v1)
- `failure_503.png`: simulated backend failure