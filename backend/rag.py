"""Lightweight SchemeSathi retrieval using SQLite FTS5."""
import re
import sqlite3
from typing import Any


STOP_WORDS = {
    "the", "a", "an", "is", "are", "what", "which", "how",
    "can", "please", "tell", "me", "about", "for", "and",
    "or", "to", "of", "in", "my", "your", "scheme", "schemes",
    "government", "yojana", "eligible", "eligibility", "help",
    "hai", "hain", "kya", "kaise", "batao", "mujhe", "mere",
    "meri", "liye", "aur", "mein", "se", "ka", "ki", "ke"
}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[^\W_]+", str(text or "").casefold())
    return list(dict.fromkeys(
        word for word in words
        if len(word) > 1 and word not in STOP_WORDS
    ))


def _normalise(text: str) -> str:
    return " ".join(
        re.findall(r"[^\W_]+", str(text or "").casefold())
    )


def _search_text(scheme: dict[str, Any]) -> str:
    eligibility = scheme.get("eligibility") or {}
    parts = [
        scheme.get("id", ""),
        scheme.get("name", ""),
        scheme.get("state", ""),
        scheme.get("level", ""),
        scheme.get("description", ""),
        scheme.get("benefits", ""),
        eligibility,
        scheme.get("required_documents", []),
        scheme.get("verification_status", ""),
        scheme.get("matching_note", ""),
    ]
    return " ".join(
        part if isinstance(part, str) else str(part)
        for part in parts if part is not None
    )


def retrieve_schemes(
    question: str,
    schemes: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return relevant stored scheme records, ranked by FTS5."""
    if not isinstance(question, str) or not question.strip():
        return []
    if not isinstance(schemes, list) or limit < 1:
        return []

    tokens = _tokens(question)
    if not tokens:
        return []

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("""
            CREATE VIRTUAL TABLE scheme_search USING fts5(
                record_key UNINDEXED,
                name,
                details
            )
        """)

        indexed = {}
        direct = []
        q_normalised = _normalise(question)

        for index, scheme in enumerate(schemes):
            if not isinstance(scheme, dict):
                continue
            key = str(index)
            name = str(scheme.get("name") or "")
            scheme_id = str(scheme.get("id") or "")
            details = _search_text(scheme)

            indexed[key] = scheme
            connection.execute(
                "INSERT INTO scheme_search(record_key, name, details) "
                "VALUES (?, ?, ?)",
                (key, name, details),
            )

            normal_name = _normalise(name)
            normal_id = _normalise(scheme_id)
            if (
                normal_name and normal_name in q_normalised
            ) or (
                normal_id and normal_id in q_normalised
            ):
                direct.append(scheme)

        query = " OR ".join('"' + token + '"' for token in tokens)
        rows = connection.execute(
            """
            SELECT record_key
            FROM scheme_search
            WHERE scheme_search MATCH ?
            ORDER BY bm25(scheme_search, 0.0, 5.0, 1.0)
            LIMIT ?
            """,
            (query, max(limit * 3, limit)),
        ).fetchall()

        combined = direct + [
            indexed[row[0]] for row in rows if row[0] in indexed
        ]

        result = []
        seen = set()
        for scheme in combined:
            identity = scheme.get("id") or scheme.get("name")
            if identity in seen:
                continue
            seen.add(identity)
            result.append(scheme)
            if len(result) >= limit:
                break

        return result
    finally:
        connection.close()
