"""
Citation formatter — maps retrieved SearchResult objects to Citation API models.

Also builds the chunk dicts needed by the prompt template.
"""

from models.api_models import Citation, SearchResult


def results_to_citations(results: list[SearchResult]) -> list[Citation]:
    """
    Convert retrieval results into structured Citation objects
    for the API response.
    """
    return [
        Citation(
            chunk_id    = r.chunk_id,
            doc_id      = r.doc_id,
            doc_title   = r.doc_title,
            section     = r.section,
            path_or_url = r.path_or_url,
            score       = r.score,
        )
        for r in results
    ]


def results_to_prompt_chunks(results: list[SearchResult]) -> list[dict]:
    """
    Convert retrieval results into the dict format expected by
    prompt_templates.build_context_block().
    """
    return [
        {
            "doc_title": r.doc_title,
            "section":   r.section or "General",
            "score":     r.score,
            "content":   r.content,
        }
        for r in results
    ]
