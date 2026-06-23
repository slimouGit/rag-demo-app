import sqlite3
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_document_name
            ON document_chunks(document_name)
        """
        )


def get_db_overview():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT 
                document_name,
                COUNT(*) AS chunk_count,
                MIN(id) AS first_chunk_id,
                MAX(id) AS last_chunk_id
            FROM document_chunks
            GROUP BY document_name
            ORDER BY document_name
        """
        ).fetchall()

    return [
        {
            "document_name": row[0],
            "chunk_count": row[1],
            "first_chunk_id": row[2],
            "last_chunk_id": row[3],
        }
        for row in rows
    ]


def get_chunks_for_document(document_name: str):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, chunk_index, content, embedding
            FROM document_chunks
            WHERE document_name = ?
            ORDER BY chunk_index
        """,
            (document_name,),
        ).fetchall()

    return [
        {
            "id": row[0],
            "chunk_index": row[1],
            "content": row[2],
            "embedding_preview": row[3][:120] + "...",
        }
        for row in rows
    ]


def delete_document(document_name: str):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM document_chunks
            WHERE document_name = ?
        """,
            (document_name,),
        )


def delete_chunk(chunk_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM document_chunks
            WHERE id = ?
        """,
            (chunk_id,),
        )
