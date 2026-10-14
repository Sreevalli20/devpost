"""Configuration management for ProofPilot AI."""
import os
from typing import Optional


class Settings:
    """Application settings."""

    def __init__(self):
        # API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.gradio_port = int(os.getenv("GRADIO_PORT", "7860"))

        # Optional API Keys (not required for baseline functionality)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # Processing Limits
        self.max_claims_per_analysis = int(os.getenv("MAX_CLAIMS_PER_ANALYSIS", "50"))
        self.max_evidence_length = int(os.getenv("MAX_EVIDENCE_LENGTH", "10000"))
        self.request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

        # Storage (use /tmp for Hugging Face Spaces to avoid permission issues)
        default_db = "/tmp/proofpilot.db" if os.path.exists("/tmp") else "proofpilot.db"
        self.database_path = os.getenv("DATABASE_PATH", default_db)

        # Application
        self.app_name = "ProofPilot AI"
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"


# Global settings instance
settings = Settings()
