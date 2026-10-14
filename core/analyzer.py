"""Claim extraction and verification analyzer."""
import re
import time
from typing import List, Tuple, Dict, Any
from .schemas import Claim, VerificationStatus, EvidenceSource
from .evidence import EvidenceRetriever
from .metrics import MetricsCalculator


class ClaimAnalyzer:
    """Analyzes AI-generated answers and verifies claims against evidence."""

    def __init__(self):
        """Initialize the analyzer with evidence retriever and metrics calculator."""
        self.evidence_retriever = EvidenceRetriever()
        self.metrics_calculator = MetricsCalculator()

    def extract_claims(self, text: str) -> List[str]:
        """
        Extract potential claims from text using heuristic patterns.

        This is a baseline implementation using sentence segmentation and
        pattern matching. For production, consider using NLP models.

        Args:
            text: The text to extract claims from

        Returns:
            List of claim strings
        """
        # Split into sentences, keeping delimiters temporarily
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue

            # Skip questions (check for question mark)
            if sentence.endswith('?'):
                continue

            # Skip obvious non-claims (hedging, opinions)
            hedge_words = ['I think', 'probably', 'maybe', 'might', 'could be',
                          'in my opinion', 'it seems', 'appears to be']
            if any(word in sentence.lower() for word in hedge_words):
                continue

            # Remove trailing punctuation for cleaner output
            sentence = re.sub(r'[.!?]+$', '', sentence).strip()

            # Keep factual-sounding sentences
            claims.append(sentence)

        return claims

    def verify_claim(self, claim: str, evidence_text: str, evidence_urls: List[str]) -> Claim:
        """
        Verify a single claim against provided evidence.

        Uses heuristic text matching for baseline verification.
        For production, integrate with NLI models or LLM APIs.

        Args:
            claim: The claim to verify
            evidence_text: Pasted evidence text
            evidence_urls: List of evidence URLs

        Returns:
            Claim object with verification status
        """
        start_time = time.time()

        # Combine all evidence
        all_evidence = evidence_text
        sources = []

        # Add evidence from URLs
        retrieved_evidence = []
        for url in evidence_urls:
            try:
                url_content = self.evidence_retriever.fetch_url(url)
                if url_content:
                    retrieved_evidence.append(url_content)
                    sources.append(EvidenceSource(type="url", content=url, title=f"Source: {url}"))
            except Exception as e:
                # Log but continue with other sources
                pass

        if retrieved_evidence:
            all_evidence += " " + " ".join(retrieved_evidence)

        if evidence_text:
            sources.append(EvidenceSource(type="text", content=evidence_text[:100], title="Pasted evidence"))

        # Normalize text for comparison
        claim_normalized = self._normalize_text(claim)
        evidence_normalized = self._normalize_text(all_evidence)

        # Check for supporting evidence
        supporting_snippets = self._find_supporting_evidence(claim_normalized, evidence_normalized)
        contradicting_snippets = self._find_contradicting_evidence(claim_normalized, evidence_normalized)

        # Determine verification status
        if not all_evidence.strip():
            status = VerificationStatus.INSUFFICIENT_EVIDENCE
            explanation = "No evidence provided to verify this claim."
            confidence = 0.0
        elif contradicting_snippets:
            status = VerificationStatus.CONTRADICTED
            explanation = "Evidence contradicts this claim."
            confidence = 0.8
        elif supporting_snippets:
            status = VerificationStatus.SUPPORTED
            explanation = "Evidence supports this claim."
            confidence = 0.7
        else:
            status = VerificationStatus.INSUFFICIENT_EVIDENCE
            explanation = "Insufficient evidence to verify this claim."
            confidence = 0.3

        processing_time = time.time() - start_time

        return Claim(
            text=claim,
            status=status,
            supporting_evidence=supporting_snippets[:3],  # Limit to top 3
            contradicting_evidence=contradicting_snippets[:3],
            sources=sources,
            explanation=explanation,
            confidence=confidence
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _find_supporting_evidence(self, claim: str, evidence: str) -> List[str]:
        """Find evidence snippets that support the claim."""
        claim_words = set(claim.split())
        if not claim_words:
            return []

        # Split evidence into sentences
        evidence_sentences = re.split(r'[.!?]+', evidence)

        supporting = []
        for sentence in evidence_sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            sentence_words = set(sentence.split())

            # Calculate word overlap
            overlap = len(claim_words & sentence_words)
            if overlap >= min(3, len(claim_words) * 0.5):
                supporting.append(sentence)

        return supporting

    def _find_contradicting_evidence(self, claim: str, evidence: str) -> List[str]:
        """Find evidence snippets that contradict the claim."""
        # Simple contradiction detection using negation words
        negation_words = ['not', 'never', 'no', 'none', 'neither', 'nor',
                         'cannot', "can't", "won't", "didn't", "doesn't"]

        claim_words = set(claim.split())
        if not claim_words:
            return []

        evidence_sentences = re.split(r'[.!?]+', evidence)

        contradicting = []
        for sentence in evidence_sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            # Check for negation and word overlap
            has_negation = any(neg in sentence for neg in negation_words)
            sentence_words = set(sentence.split())
            overlap = len(claim_words & sentence_words)

            if has_negation and overlap >= 2:
                contradicting.append(sentence)

        return contradicting

    def analyze(self, question: str, answer: str, evidence_text: str = None,
                evidence_urls: List[str] = None) -> Tuple[List[Claim], Dict[str, Any]]:
        """
        Perform complete analysis of an answer.

        Args:
            question: The original question
            answer: The AI-generated answer
            evidence_text: Pasted evidence text
            evidence_urls: List of evidence URLs

        Returns:
            Tuple of (claims list, metrics dict)
        """
        start_time = time.time()

        if evidence_urls is None:
            evidence_urls = []
        if evidence_text is None:
            evidence_text = ""

        # Extract claims
        claims_text = self.extract_claims(answer)

        # Verify each claim
        verified_claims = []
        for claim_text in claims_text:
            claim = self.verify_claim(claim_text, evidence_text, evidence_urls)
            verified_claims.append(claim)

        # Calculate metrics
        metrics = self.metrics_calculator.calculate(verified_claims)

        processing_time = time.time() - start_time
        metrics['processing_time_seconds'] = processing_time

        return verified_claims, metrics
