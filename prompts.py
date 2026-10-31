"""All prompts live here. Bump PROMPT_VERSION whenever you change any of them
and log the change in prompt_log.md."""

PROMPT_VERSION = "v1"

LANGUAGE = {
    "English": "English",
    "Nepali": "Nepali (नेपाली, Devanagari script)",
    "Both": "English first, then the same text in Nepali (Devanagari script)",
}

DETAIL = {
    "short": "Be brief: a 2-sentence summary and at most 3 key terms.",
    "standard": "Write a 3-4 sentence summary and explain every important term.",
    "detailed": "Write a 5-6 sentence summary and explain every term and clause in simple words.",
}

SCHEMA_HINT = """{
  "document_type": "scholarship | bank_form | contract | government_notice | other",
  "summary": "...",
  "key_terms": [{"term": "...", "meaning": "..."}],
  "action_items": [{"task": "...", "deadline": "... or null", "source_quote": "..."}],
  "watch_out_for": [{"issue": "...", "source_quote": "..."}],
  "unclear_or_missing": ["..."]
}"""

# v1 is deliberately plain, so your log starts from a real baseline.
EXPLAIN_SYSTEM = """You explain official documents to ordinary people in Nepal.
Read the document and reply with JSON in exactly this shape:
{schema}
Write in: {language}.
{detail}"""

EXPLAIN_USER = "Document:\n{document}"

RETRY_MESSAGE = "Your last reply could not be used: {error}\nReply again with only the corrected JSON."

CHAT_SYSTEM = """You answer follow-up questions about a document for an ordinary reader in Nepal.
Answer in: {language}.

Document:
{document}"""
