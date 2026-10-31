"""API call, parsing and validation helpers."""
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

import prompts

load_dotenv()

MAX_CHARS = 15_000


class AppError(RuntimeError):
    """An error whose message is safe to show to the user."""


# ---------- Schema: the JSON the model must return ----------
class KeyTerm(BaseModel):
    term: str
    meaning: str


class ActionItem(BaseModel):
    task: str
    deadline: Optional[str] = None
    source_quote: str


class Risk(BaseModel):
    issue: str
    source_quote: str


class Explanation(BaseModel):
    document_type: Literal["scholarship", "bank_form", "contract", "government_notice", "other"]
    summary: str
    key_terms: list[KeyTerm]
    action_items: list[ActionItem]
    watch_out_for: list[Risk]
    unclear_or_missing: list[str]


@dataclass
class Outcome:
    result: Explanation
    unverified: list[str] = field(default_factory=list)  # quotes not found in the document
    warnings: list[str] = field(default_factory=list)  # e.g. wrong output language
    retried: bool = False  # the first reply was invalid, so we asked again


# ---------- LLM call (any OpenAI-compatible endpoint) ----------
def call_llm(messages: list[dict]) -> str:
    key, model = os.getenv("LLM_API_KEY"), os.getenv("LLM_MODEL")
    if not key or not model:
        raise AppError("Settings are missing. Copy .env.example to .env and set LLM_API_KEY and LLM_MODEL.")
    temperature = os.getenv("LLM_TEMPERATURE", "0.2")
    extra = {"temperature": float(temperature)} if temperature else {}
    try:
        client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL") or None, timeout=60)
        reply = client.chat.completions.create(model=model, messages=messages, **extra)
    except OpenAIError as e:
        raise AppError(f"The AI service returned an error: {e}") from e
    return reply.choices[0].message.content or ""


# ---------- Parsing and validation ----------
def extract_json(raw: str) -> dict:
    """Models often wrap JSON in ```json fences or add a sentence around it."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the reply.")
    return json.loads(raw[start : end + 1])


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\u200b\u200c\u200d]", "", text)  # invisible joiners differ between copies of Devanagari text
    return re.sub(r"\s+", " ", text).strip().lower()


def find_unverified_quotes(result: Explanation, document: str) -> list[str]:
    """Quotes the model says come from the document but that are not in it."""
    doc = _norm(document)
    quotes = [a.source_quote for a in result.action_items] + [r.source_quote for r in result.watch_out_for]
    return [q for q in quotes if not q.strip() or _norm(q) not in doc]


def devanagari_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum("\u0900" <= c <= "\u097f" for c in letters) / len(letters) if letters else 0.0


def language_warnings(summary: str, language: str) -> list[str]:
    ratio = devanagari_ratio(summary)
    if language == "Nepali" and ratio < 0.5:
        return ["The summary does not look like Nepali."]
    if language == "English" and ratio > 0.2:
        return ["The summary contains a lot of Devanagari although English was chosen."]
    return []


# ---------- The two things the app does ----------
def explain_document(document: str, language: str, detail: str) -> Outcome:
    system = prompts.EXPLAIN_SYSTEM.format(
        schema=prompts.SCHEMA_HINT, language=prompts.LANGUAGE[language], detail=prompts.DETAIL[detail]
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompts.EXPLAIN_USER.format(document=document)},
    ]
    result, retried, error = None, False, ""
    for _ in range(2):  # first try, plus one retry that shows the model its own error
        raw = call_llm(messages)
        try:
            result = Explanation.model_validate(extract_json(raw))  # bad JSON and bad schema are both ValueErrors
            break
        except ValueError as e:
            retried, error = True, str(e)[:400]
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": prompts.RETRY_MESSAGE.format(error=error)},
            ]
    if result is None:
        raise AppError(f"The AI reply was not valid even after a retry. Try again. Last error: {error}")
    return Outcome(result, find_unverified_quotes(result, document), language_warnings(result.summary, language), retried)


def answer_followup(document: str, chat: list[dict], question: str, language: str) -> str:
    system = prompts.CHAT_SYSTEM.format(language=prompts.LANGUAGE[language], document=document)
    return call_llm([{"role": "system", "content": system}] + chat[-10:] + [{"role": "user", "content": question}])


# ---------- Display ----------
def render_markdown(o: Outcome) -> str:
    r = o.result

    def quote(q: str) -> str:
        warn = "  ⚠️ *not found in your text*" if q in o.unverified else ""
        return f"\n  > {' '.join(q.split())}{warn}"

    parts = [f"### Summary\n*Looks like: {r.document_type.replace('_', ' ')}*\n\n{r.summary}"]
    if r.key_terms:
        parts.append("### Key terms\n" + "\n".join(f"- **{t.term}**: {t.meaning}" for t in r.key_terms))
    if r.action_items:
        parts.append(
            "### What you need to do\n"
            + "\n".join(f"- {a.task} (deadline: **{a.deadline or 'not stated'}**){quote(a.source_quote)}" for a in r.action_items)
        )
    if r.watch_out_for:
        parts.append("### Watch out for\n" + "\n".join(f"- {x.issue}{quote(x.source_quote)}" for x in r.watch_out_for))
    if r.unclear_or_missing:
        parts.append("### Unclear or missing\n" + "\n".join(f"- {u}" for u in r.unclear_or_missing))
    return "\n\n".join(parts)


def render_notes(o: Outcome) -> str:
    notes = [f"⚠️ {w}" for w in o.warnings]
    if o.unverified:
        notes.append(f"⚠️ {len(o.unverified)} quoted passage(s) were not found in your text. Treat them as unverified.")
    if o.retried:
        notes.append("ℹ️ The first reply was invalid, so the app asked again.")
    return "\n\n".join(notes) or "✅ Checks passed: valid JSON, all quotes found in your text."
