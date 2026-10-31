# Sajilo: Nepali-English document explainer

<!-- Replace this paragraph with 2-3 sentences in your own words. -->
Paste a scholarship notice, bank form or agreement and get a plain-language explanation in English, Nepali or both: what it says, what you must do and by when, and what to watch out for. You can then ask follow-up questions about the same document.

## Problem statement

- **User:**
- **Problem:**
- **Why AI helps:**
- **Evidence:** (quotes from 2-3 people who struggled with a document like this)

## Demo

Link to the deployed app or the demo video:

![Explanation view](screenshots/explain.png)
![Follow-up chat](screenshots/chat.png)

## Setup

Tested with Python 3.12, Gradio 6.31, OpenAI SDK 3.42 and Pydantic 2.14.

1. Create a virtual environment: `python -m venv .venv`, then activate it (`source .venv/bin/activate`, or `.venv\Scripts\activate` on Windows).
2. Install the dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `LLM_API_KEY` and `LLM_MODEL`, plus `LLM_BASE_URL` unless you use OpenAI. `.env` is git-ignored. Never commit it.
4. Start the app: `python app.py`, then open the local URL it prints.

## How it works

`app.py` (Gradio interface) calls `utils.py` (LLM call, parsing, validation), which reads every prompt from `prompts.py`.

1. The model must reply with JSON. `utils.py` extracts it, validates it with Pydantic, and retries once, showing the model its own error, if it is invalid.
2. Every `source_quote` must appear in the original text. Quotes that do not are flagged as unverified in the interface.
3. When English or Nepali output is chosen, the script of the summary is checked.
4. Follow-up questions are answered with the document and the earlier chat in context.

## Testing

`python tests/run_tests.py` runs the 10 cases in `tests/test_cases.json` and saves `tests/results/<version>.md`. A case can set `must_contain_any`, `must_not_contain`, `expect_no_deadlines` or `expect_type`. These auto-checks are hints, so read the outputs yourself.

| Prompt version | Passed |
|---|---|
| v1 | /10 |

Failures I recorded (test ID, what went wrong, which version fixed it):

## Prompt iteration

See [prompt_log.md](prompt_log.md).

## Limits

- It explains documents. It is not legal or financial advice.
- Text input only, up to 15,000 characters. No PDF or photo upload.
- Nepali output quality depends on the model. Tested with: (list the models)
- The quote check catches invented quotes. It cannot catch a wrong explanation.
- The text you paste is sent to the AI provider. Remove ID and account numbers first.
- (add the limits you found while testing)

## Lessons learned

(Write this after your last test run: what failed, what surprised you, what you would change.)
