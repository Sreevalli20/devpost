"""Flask application for ProofPilot AI."""
import os
import json
import uuid
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.exceptions import BadRequest, InternalServerError

from core.analyzer import ClaimAnalyzer
from core.storage import Storage


# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max request size

# Initialize components
analyzer = ClaimAnalyzer()
storage = Storage('proofpilot.db')


@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Analyze the reliability of an AI-generated answer.

    Expected JSON body:
    {
        "question": string,
        "answer": string,
        "evidence_text": string (optional),
        "evidence_urls": array of strings (optional)
    }
    """
    try:
        data = request.get_json()

        if not data:
            raise BadRequest('No JSON data provided')

        # Validate required fields
        answer = data.get('answer', '').strip()
        if not answer:
            raise BadRequest('Answer is required')

        question = data.get('question', '').strip()
        evidence_text = data.get('evidence_text', '').strip()
        evidence_urls = data.get('evidence_urls', [])

        # Validate evidence_urls is a list
        if not isinstance(evidence_urls, list):
            raise BadRequest('evidence_urls must be an array')

        # Limit evidence length
        if len(evidence_text) > 50000:
            raise BadRequest('Evidence text too long (max 50000 characters)')

        # Limit number of URLs
        if len(evidence_urls) > 10:
            raise BadRequest('Too many URLs (max 10)')

        # Perform analysis
        claims, metrics = analyzer.analyze(
            question=question,
            answer=answer,
            evidence_text=evidence_text,
            evidence_urls=evidence_urls
        )

        # Save to storage
        analysis_id = str(uuid.uuid4())
        try:
            storage.save_evaluation(
                analysis_id=analysis_id,
                question=question,
                answer=answer,
                evidence_text=evidence_text,
                evidence_urls=evidence_urls,
                claims=[c.to_dict() for c in claims],
                metrics=metrics,
                processing_time=metrics.get('processing_time_seconds', 0)
            )
        except Exception as e:
            # Continue even if storage fails
            app.logger.error(f'Storage error: {str(e)}')

        return jsonify({
            'analysis_id': analysis_id,
            'claims': [c.to_dict() for c in claims],
            'metrics': metrics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f'Analysis error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/history', methods=['GET'])
def history():
    """Get evaluation history."""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Cap at 100

        entries = storage.get_history(limit=limit)
        return jsonify({
            'history': [e.to_dict() for e in entries]
        })

    except Exception as e:
        app.logger.error(f'History error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Get aggregated metrics."""
    try:
        summary = storage.get_metrics_summary()
        return jsonify(summary)

    except Exception as e:
        app.logger.error(f'Metrics error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear all evaluation history."""
    try:
        storage.clear_all_evaluations()
        return jsonify({'message': 'History cleared successfully'})

    except Exception as e:
        app.logger.error(f'Clear history error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/export/<analysis_id>', methods=['GET'])
def export(analysis_id):
    """Export an analysis as Markdown or JSON."""
    try:
        format_type = request.args.get('format', 'markdown').lower()

        if format_type not in ['markdown', 'json']:
            raise BadRequest('Invalid format. Use "markdown" or "json"')

        evaluation = storage.get_evaluation(analysis_id)
        if not evaluation:
            return jsonify({'error': 'Analysis not found'}), 404

        if format_type == 'json':
            response = jsonify(evaluation)
            response.headers['Content-Disposition'] = f'attachment; filename=proofpilot_{analysis_id}.json'
            return response
        else:
            # Generate Markdown report
            report = generate_markdown_report(evaluation)
            response = app.response_class(
                report,
                mimetype='text/markdown',
                headers={'Content-Disposition': f'attachment; filename=proofpilot_{analysis_id}.md'}
            )
            return response

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f'Export error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


def generate_markdown_report(evaluation: dict) -> str:
    """Generate a Markdown report from evaluation data."""
    lines = [
        '# ProofPilot AI Analysis Report',
        '',
        f'**Generated:** {evaluation["timestamp"]}',
        f'**Analysis ID:** {evaluation["id"]}',
        '',
        '## Question',
        evaluation['question'],
        '',
        '## Answer',
        evaluation['answer'],
        '',
        '## Metrics',
        '```json',
        json.dumps(evaluation['metrics'], indent=2),
        '```',
        '',
        '## Claims',
        ''
    ]

    for i, claim in enumerate(evaluation['claims'], 1):
        status_emoji = {
            'supported': '✅',
            'contradicted': '❌',
            'insufficient_evidence': '⚠️'
        }.get(claim['status'], '❓')

        lines.append(f'### {status_emoji} Claim {i}')
        lines.append(f'**Status:** {claim["status"].replace("_", " ").title()}')
        lines.append(f'**Text:** {claim["text"]}')
        lines.append(f'**Confidence:** {claim["confidence"]:.1%}')
        lines.append(f'**Explanation:** {claim["explanation"]}')
        lines.append('')

        if claim['supporting_evidence']:
            lines.append('**Supporting Evidence:**')
            for evidence in claim['supporting_evidence']:
                lines.append(f'- {evidence}')
            lines.append('')

        if claim['contradicting_evidence']:
            lines.append('**Contradicting Evidence:**')
            for evidence in claim['contradicting_evidence']:
                lines.append(f'- {evidence}')
            lines.append('')

        if claim['sources']:
            lines.append('**Sources:**')
            for source in claim['sources']:
                lines.append(f'- {source.get("title", source["content"])}')
            lines.append('')

    lines.append('')
    lines.append('---')
    lines.append('*Generated by ProofPilot AI - Real-Time AI Reliability Lab*')

    return '\n'.join(lines)


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
