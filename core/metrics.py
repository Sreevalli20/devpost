"""Metrics calculation for evaluation results."""
from typing import List, Dict, Any
from .schemas import Claim, VerificationStatus


class MetricsCalculator:
    """Calculates evaluation metrics from verified claims."""

    def calculate(self, claims: List[Claim]) -> Dict[str, Any]:
        """
        Calculate metrics from a list of verified claims.

        Args:
            claims: List of verified Claim objects

        Returns:
            Dictionary of calculated metrics
        """
        if not claims:
            return self._empty_metrics()

        total = len(claims)
        supported = sum(1 for c in claims if c.status == VerificationStatus.SUPPORTED)
        contradicted = sum(1 for c in claims if c.status == VerificationStatus.CONTRADICTED)
        insufficient = sum(1 for c in claims if c.status == VerificationStatus.INSUFFICIENT_EVIDENCE)

        # Calculate rates
        support_rate = (supported / total) * 100 if total > 0 else 0
        contradiction_rate = (contradicted / total) * 100 if total > 0 else 0
        insufficient_rate = (insufficient / total) * 100 if total > 0 else 0

        # Calculate source coverage
        unique_sources = set()
        for claim in claims:
            for source in claim.sources:
                unique_sources.add(source.content)

        # Calculate average confidence
        avg_confidence = sum(c.confidence for c in claims) / total if total > 0 else 0

        return {
            'total_claims': total,
            'supported_claims': supported,
            'contradicted_claims': contradicted,
            'insufficient_evidence_claims': insufficient,
            'evidence_support_rate': round(support_rate, 2),
            'contradiction_rate': round(contradiction_rate, 2),
            'insufficient_evidence_rate': round(insufficient_rate, 2),
            'source_coverage': len(unique_sources),
            'average_confidence': round(avg_confidence, 2)
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics when no claims are present."""
        return {
            'total_claims': 0,
            'supported_claims': 0,
            'contradicted_claims': 0,
            'insufficient_evidence_claims': 0,
            'evidence_support_rate': 0.0,
            'contradiction_rate': 0.0,
            'insufficient_evidence_rate': 0.0,
            'source_coverage': 0,
            'average_confidence': 0.0
        }
