"""Data models for ProofPilot AI."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class VerificationStatus(str, Enum):
    """Verification status for claims."""
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceSource:
    """Source of evidence."""
    def __init__(self, type: str, content: str, title: Optional[str] = None):
        self.type = type
        self.content = content
        self.title = title

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "title": self.title
        }


class Claim:
    """A claim extracted from an answer."""
    def __init__(
        self,
        text: str,
        status: VerificationStatus,
        supporting_evidence: List[str] = None,
        contradicting_evidence: List[str] = None,
        sources: List[EvidenceSource] = None,
        explanation: str = "",
        confidence: float = 0.0
    ):
        self.text = text
        self.status = status
        self.supporting_evidence = supporting_evidence or []
        self.contradicting_evidence = contradicting_evidence or []
        self.sources = sources or []
        self.explanation = explanation
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "status": self.status.value,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "sources": [s.to_dict() for s in self.sources],
            "explanation": self.explanation,
            "confidence": self.confidence
        }


class HistoryEntry:
    """Entry in evaluation history."""
    def __init__(
        self,
        analysis_id: str,
        timestamp: datetime,
        question: str,
        total_claims: int,
        supported_claims: int,
        contradicted_claims: int,
        insufficient_evidence_claims: int
    ):
        self.analysis_id = analysis_id
        self.timestamp = timestamp
        self.question = question
        self.total_claims = total_claims
        self.supported_claims = supported_claims
        self.contradicted_claims = contradicted_claims
        self.insufficient_evidence_claims = insufficient_evidence_claims

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp.isoformat(),
            "question": self.question,
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "contradicted_claims": self.contradicted_claims,
            "insufficient_evidence_claims": self.insufficient_evidence_claims
        }
