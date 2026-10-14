"""Pydantic schemas for API requests and responses."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class VerificationStatus(str, Enum):
    """Verification status for claims."""
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceSource(BaseModel):
    """Source of evidence."""
    type: str = Field(..., description="Type of source: 'text' or 'url'")
    content: str = Field(..., description="The evidence content or URL")
    title: Optional[str] = Field(None, description="Title or description of the source")


class Claim(BaseModel):
    """A claim extracted from an answer."""
    text: str = Field(..., description="The claim text")
    status: VerificationStatus = Field(..., description="Verification status")
    supporting_evidence: List[str] = Field(default_factory=list, description="Evidence supporting the claim")
    contradicting_evidence: List[str] = Field(default_factory=list, description="Evidence contradicting the claim")
    sources: List[EvidenceSource] = Field(default_factory=list, description="Sources referenced")
    explanation: str = Field(..., description="Explanation of the verification decision")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")


class AnalysisRequest(BaseModel):
    """Request for reliability analysis."""
    question: str = Field(..., description="The original question")
    answer: str = Field(..., description="The AI-generated answer to analyze")
    evidence_text: Optional[str] = Field(None, description="Pasted evidence text")
    evidence_urls: List[str] = Field(default_factory=list, description="List of evidence URLs")


class AnalysisResponse(BaseModel):
    """Response from reliability analysis."""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the analysis was performed")
    claims: List[Claim] = Field(..., description="Extracted and verified claims")
    metrics: Dict[str, Any] = Field(..., description="Evaluation metrics")
    processing_time_seconds: float = Field(..., description="Time taken for analysis")


class Metrics(BaseModel):
    """Evaluation metrics."""
    total_claims: int = Field(..., description="Total number of claims analyzed")
    supported_claims: int = Field(..., description="Number of supported claims")
    contradicted_claims: int = Field(..., description="Number of contradicted claims")
    insufficient_evidence_claims: int = Field(..., description="Number of claims with insufficient evidence")
    evidence_support_rate: float = Field(..., description="Percentage of claims supported")
    contradiction_rate: float = Field(..., description="Percentage of claims contradicted")
    insufficient_evidence_rate: float = Field(..., description="Percentage of claims with insufficient evidence")
    source_coverage: int = Field(..., description="Number of unique sources")
    average_confidence: float = Field(..., description="Average confidence across all claims")


class HistoryEntry(BaseModel):
    """Entry in evaluation history."""
    analysis_id: str
    timestamp: datetime
    question: str
    total_claims: int
    supported_claims: int
    contradicted_claims: int
    insufficient_evidence_claims: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
