# ProofPilot AI — Real-Time AI Reliability Lab

**Test AI answers. Verify evidence. Measure reliability.**

ProofPilot AI is a professional AI evaluation tool that verifies AI-generated claims against user-supplied evidence. It provides transparent, explainable verification with clear metrics and exportable reports.

## Features

- **Claim Extraction**: Automatically extracts checkable claims from AI-generated answers
- **Evidence Verification**: Compares claims against trusted evidence sources (text and URLs)
- **Transparent Classification**: Clear support, contradiction, and insufficient-evidence labels
- **Real-Time Metrics**: Evidence support rate, contradiction rate, source coverage, and more
- **Exportable Reports**: Download detailed evaluation reports in Markdown or JSON format
- **Modern UI**: Professional enterprise-grade interface with dark theme
- **No Paid API Required**: Baseline heuristic verification works without paid services

## Quick Start

### Local Development

**Prerequisites**:
- Python 3.8 or higher
- pip package manager

**Installation**:
```bash
pip install -r requirements.txt
python app.py
```

The application will start on `http://localhost:5000`

### Deployment

This application is configured for deployment on Render using the provided `render.yaml` file.

## Architecture

```
proofpilot-ai/
├── core/           # Core business logic
│   ├── analyzer.py      # Claim extraction and verification
│   ├── evidence.py      # Evidence retrieval with SSRF protection
│   ├── metrics.py       # Metrics calculation
│   ├── schemas.py       # Data models
│   └── storage.py       # SQLite database layer
├── static/         # Static assets
│   ├── css/
│   │   └── style.css    # Custom theme styles
│   └── js/
│       └── app.js       # Frontend JavaScript
├── templates/      # HTML templates
│   └── index.html      # Main application page
├── app.py          # Flask application entry point
├── requirements.txt # Python dependencies
├── render.yaml     # Render deployment configuration
└── README.md       # This file
```

## Security

- No secrets hardcoded in the project
- URL fetching blocks localhost, private IPs, and internal addresses (SSRF protection)
- Request size limits enforced (10MB max)
- Input validation on all endpoints
- User-supplied code is never executed

## Metrics

ProofPilot AI tracks:

- **Evidence Support Rate**: Percentage of claims supported by evidence
- **Contradiction Rate**: Percentage of claims contradicted by evidence
- **Insufficient Evidence Rate**: Percentage of claims with insufficient evidence
- **Source Coverage**: Number of unique sources referenced
- **Average Confidence**: Average confidence score across all claims

All metrics are calculated from actual evaluations.

## Limitations

- Baseline verification uses heuristic matching; it may miss nuanced relationships
- URL retrieval depends on network accessibility and website availability
- Evidence similarity scores are not proof of factual correctness
- SQLite storage is local; data persistence depends on your hosting configuration
- For production use, consider integrating with advanced NLI models or LLM APIs and deploying to a cloud VM with persistent storage

## Technology Stack

- **Frontend**: Responsive HTML, CSS, and JavaScript
- **Backend**: Python with Flask
- **Server**: Gunicorn (production)
- **Storage**: SQLite database
- **Evaluation**: Heuristic text matching (extensible for NLI models)
- **Dependencies**: Flask, Gunicorn, httpx, BeautifulSoup4, lxml

## License

This project is provided as-is for educational and demonstration purposes.

---

**Note**: This is a demonstration project. While functional, it should not be used for critical decision-making without proper validation and extension for specific use cases.
