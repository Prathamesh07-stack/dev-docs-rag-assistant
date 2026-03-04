"""
Prompt templates for the RAG chat endpoint.

Design philosophy:
  - System prompt is strict: LLM MUST answer only from provided context
  - Citations are required in a structured format: [Doc: title, §Section]
  - Ambiguous questions → ask for clarification rather than guessing
  - Low-confidence / no-context → explicit refusal message, no hallucination

The prompt uses XML-style tags for context blocks — this works well across
all major LLMs (GPT, Claude, Llama) for clear section separation.
"""

SYSTEM_PROMPT = """You are a Documentation Assistant. Your job is to answer questions about internal engineering documentation accurately and concisely.

STRICT RULES — follow these without exception:
1. Answer ONLY using the information in the <context> blocks below.
2. Do NOT use any outside knowledge, training data, or assumptions.
3. After EVERY factual statement, cite the source using this exact format: [Doc: {title}, §{section}]
4. If the answer cannot be found in the context, say exactly: "I don't have enough information in the docs to answer this confidently."
5. If the question is ambiguous or too vague, ask ONE clarifying question instead of guessing.
6. Be concise. Prefer bullet points for multi-step instructions.
7. Never fabricate URLs, commands, or configs that aren't in the context."""


def build_context_block(chunks: list[dict]) -> str:
    """
    Format retrieved chunks as numbered XML context blocks.

    Each chunk becomes:
      <context id="1">
      Source: doc_title | §Section Title | score: 0.91
      ---
      chunk content here...
      </context>
    """
    if not chunks:
        return "<context>\nNo relevant documentation found.\n</context>"

    blocks = []
    for i, chunk in enumerate(chunks, 1):
        doc_title = chunk.get("doc_title", "Unknown Doc")
        section   = chunk.get("section", "") or "General"
        score     = chunk.get("score", 0)
        content   = chunk.get("content", "").strip()

        block = (
            f'<context id="{i}">\n'
            f"Source: {doc_title} | §{section} | confidence: {score:.2f}\n"
            f"---\n"
            f"{content}\n"
            f"</context>"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def build_history_block(history: list[dict]) -> str:
    """
    Format conversation history as a compact exchange log.
    Keeps the last N turns visible to the LLM for follow-up context.
    """
    if not history:
        return ""

    lines = ["<conversation_history>"]
    for turn in history:
        role    = turn.get("role", "user")
        content = turn.get("content", "").strip()
        lines.append(f"[{role.upper()}]: {content}")
    lines.append("</conversation_history>")
    return "\n".join(lines)


def build_full_prompt(
    question: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> list[dict]:
    """
    Build the full message list for the LLM API call.

    Returns OpenAI-compatible messages format:
      [
        {"role": "system",    "content": "..."},
        {"role": "user",      "content": "..."},  ← history (optional)
        {"role": "assistant", "content": "..."},  ← history (optional)
        ...
        {"role": "user",      "content": "..."},  ← current question + context
      ]
    """
    context_block   = build_context_block(chunks)
    history_block   = build_history_block(history or [])

    user_message = f"""{history_block}

{context_block}

Question: {question}

Remember: Answer ONLY from the context above. Cite every claim with [Doc: title, §section]."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message.strip()},
    ]


# Canned response when no chunks pass the confidence threshold
LOW_CONFIDENCE_RESPONSE = (
    "I don't have enough information in the docs to answer this confidently. "
    "Could you rephrase your question or provide more context? "
    "I can only answer questions based on the indexed documentation."
)
