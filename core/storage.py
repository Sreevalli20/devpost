"""Storage layer for evaluation history using SQLite."""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from .schemas import HistoryEntry


class Storage:
    """SQLite-based storage for evaluation history."""

    def __init__(self, db_path: str = "proofpilot.db"):
        """Initialize storage with database path."""
        self.db_path = db_path
        self._initialize_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    evidence_text TEXT,
                    evidence_urls TEXT,
                    claims TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    processing_time REAL NOT NULL
                )
            """)

    def save_evaluation(self, analysis_id: str, question: str, answer: str,
                       evidence_text: str, evidence_urls: List[str],
                       claims: List[Dict], metrics: Dict[str, Any],
                       processing_time: float) -> None:
        """
        Save an evaluation to the database.

        Args:
            analysis_id: Unique identifier for the analysis
            question: The original question
            answer: The AI-generated answer
            evidence_text: Pasted evidence text
            evidence_urls: List of evidence URLs
            claims: List of claim dictionaries
            metrics: Metrics dictionary
            processing_time: Processing time in seconds
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO evaluations
                (id, timestamp, question, answer, evidence_text, evidence_urls, claims, metrics, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                datetime.utcnow().isoformat(),
                question,
                answer,
                evidence_text,
                json.dumps(evidence_urls),
                json.dumps(claims),
                json.dumps(metrics),
                processing_time
            ))

    def get_evaluation(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an evaluation by ID.

        Args:
            analysis_id: The analysis ID

        Returns:
            Evaluation dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM evaluations WHERE id = ?",
                (analysis_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

    def get_history(self, limit: int = 50) -> List[HistoryEntry]:
        """
        Get evaluation history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of HistoryEntry objects
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, question, claims, metrics
                FROM evaluations
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            entries = []
            for row in cursor.fetchall():
                claims = json.loads(row['claims'])
                metrics = json.loads(row['metrics'])

                entry = HistoryEntry(
                    analysis_id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    question=row['question'],
                    total_claims=metrics.get('total_claims', 0),
                    supported_claims=metrics.get('supported_claims', 0),
                    contradicted_claims=metrics.get('contradicted_claims', 0),
                    insufficient_evidence_claims=metrics.get('insufficient_evidence_claims', 0)
                )
                entries.append(entry)

            return entries

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get aggregated metrics across all evaluations.

        Returns:
            Dictionary with summary statistics
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM evaluations")
            total_evaluations = cursor.fetchone()['count']

            if total_evaluations == 0:
                return {
                    'total_evaluations': 0,
                    'total_claims': 0,
                    'average_support_rate': 0.0,
                    'average_contradiction_rate': 0.0
                }

            cursor = conn.execute("SELECT claims, metrics FROM evaluations")
            all_claims = 0
            total_support_rate = 0.0
            total_contradiction_rate = 0.0

            for row in cursor.fetchall():
                metrics = json.loads(row['metrics'])
                all_claims += metrics.get('total_claims', 0)
                total_support_rate += metrics.get('evidence_support_rate', 0)
                total_contradiction_rate += metrics.get('contradiction_rate', 0)

            return {
                'total_evaluations': total_evaluations,
                'total_claims': all_claims,
                'average_support_rate': round(total_support_rate / total_evaluations, 2),
                'average_contradiction_rate': round(total_contradiction_rate / total_evaluations, 2)
            }

    def delete_evaluation(self, analysis_id: str) -> bool:
        """
        Delete an evaluation by ID.

        Args:
            analysis_id: The analysis ID

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM evaluations WHERE id = ?",
                (analysis_id,)
            )
            return cursor.rowcount > 0

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            'id': row['id'],
            'timestamp': row['timestamp'],
            'question': row['question'],
            'answer': row['answer'],
            'evidence_text': row['evidence_text'],
            'evidence_urls': json.loads(row['evidence_urls']),
            'claims': json.loads(row['claims']),
            'metrics': json.loads(row['metrics']),
            'processing_time': row['processing_time']
        }
