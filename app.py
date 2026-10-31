"""Gradio app. Run with: python app.py"""
import pathlib

import gradio as gr

from utils import MAX_CHARS, AppError, answer_followup, explain_document, render_markdown, render_notes

DISCLAIMER = (
    "Sajilo explains documents in plain language. It is **not legal or financial advice**: "
    "confirm important details with the office that issued the document. "
    "The text you paste is sent to the AI provider, so remove ID and account numbers first."
)
SAMPLE = pathlib.Path(__file__).parent / "data" / "sample_scholarship_en.txt"


def run_explain(document, language, detail):
    document = (document or "").strip()
    if len(document) < 20:
        raise gr.Error("There is not enough text to explain. Paste the full document and try again.")
    if len(document) > MAX_CHARS:
        raise gr.Error(f"The text has {len(document):,} characters; the limit is {MAX_CHARS:,}. Paste only the part you need.")
    try:
        outcome = explain_document(document, language, detail)
    except AppError as e:
        raise gr.Error(str(e))
    # A new document starts a new conversation, so the chat history is cleared.
    return render_markdown(outcome), render_notes(outcome), outcome.result.model_dump(), document, [], []


def run_chat(question, doc, chat, language):
    question = (question or "").strip()
    if not doc:
        raise gr.Error("Explain a document first, then ask questions about it.")
    if not question:
        return chat, chat, ""
    try:
        answer = answer_followup(doc, chat, question, language)
    except AppError as e:
        raise gr.Error(str(e))
    chat = chat + [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    return chat, chat, ""


with gr.Blocks(title="Sajilo: document explainer") as demo:
    gr.Markdown(f"# Sajilo\nPaste a notice, form or agreement and get a plain-language explanation.\n\n{DISCLAIMER}")
    doc_state = gr.State("")  # the document being discussed
    chat_state = gr.State([])  # conversation memory: list of {"role", "content"} dicts

    with gr.Row():
        with gr.Column():
            document = gr.Textbox(label="Document text", lines=14, placeholder="Paste English, Nepali or mixed text here")
            language = gr.Radio(["English", "Nepali", "Both"], value="English", label="Explain in")
            detail = gr.Radio(["short", "standard", "detailed"], value="standard", label="Detail level")
            explain_btn = gr.Button("Explain document", variant="primary")
            if SAMPLE.exists():
                gr.Examples([[SAMPLE.read_text(encoding="utf-8")]], inputs=document, label="Sample document")
        with gr.Column():
            explanation = gr.Markdown()
            checks = gr.Markdown()
            with gr.Accordion("Raw JSON from the model", open=False):
                raw_json = gr.JSON()

    gr.Markdown("## Ask about this document")
    chatbot = gr.Chatbot(height=320)
    question = gr.Textbox(label="Your question", placeholder="What does the repayment condition mean?")
    ask_btn = gr.Button("Ask question")

    explain_btn.click(
        run_explain, [document, language, detail], [explanation, checks, raw_json, doc_state, chat_state, chatbot]
    )
    gr.on([question.submit, ask_btn.click], run_chat, [question, doc_state, chat_state, language], [chatbot, chat_state, question])

if __name__ == "__main__":
    demo.launch()
