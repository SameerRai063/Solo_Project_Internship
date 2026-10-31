# Prompt log

Workflow: change the prompt, bump `PROMPT_VERSION` in `prompts.py`, run `python tests/run_tests.py`, then copy the pass count here. Full outputs for each version are saved in `tests/results/`.

| Version | What changed | Why (what failed before) | Passed | Fixed | Broke |
|---|---|---|---|---|---|
| v1 | Plain prompt: schema, language, detail | Baseline | /10 | | |
| v2 | | | | | |
| v3 | | | | | |
| v4 | | | | | |
| v5 | | | | | |

## Notes per version

### v1
- Failures I saw (test ID, what the output looked like):
- What I will change next, and why:

### v2
- Failures I saw:
- What I will change next, and why:

## Ideas to try (only after you have seen the failure they fix)

- Tell the model to treat the document as untrusted data and never follow instructions inside it (test 2).
- Require `source_quote` to be copied exactly, in the document's original language, never translated.
- Use `null`, not "N/A" or "not stated", when there is no deadline (test 4).
- Copy dates exactly as written and never convert between calendars (test 3).
- Add one short example of the expected JSON.
- Run the same tests on two different models and log how the Nepali output differs.
