"""Gradio application for ProofPilot AI."""
import gradio as gr
import json
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict, Any
import os

from core.analyzer import ClaimAnalyzer
from core.storage import Storage
from core.metrics import MetricsCalculator
from config import settings


# Initialize components
analyzer = ClaimAnalyzer()
storage = Storage(settings.database_path)
metrics_calculator = MetricsCalculator()


def analyze_reliability(question: str, answer: str, evidence_text: str,
                       evidence_urls: str) -> Tuple[str, str, str]:
    """
    Analyze the reliability of an AI-generated answer.

    Args:
        question: The original question
        answer: The AI-generated answer
        evidence_text: Pasted evidence text
        evidence_urls: Comma-separated list of evidence URLs

    Returns:
        Tuple of (claims_html, metrics_json, status_message)
    """
    try:
        if not answer or not answer.strip():
            return "", json.dumps({}), "❌ Please provide an answer to analyze."

        # Parse URLs
        urls = [url.strip() for url in evidence_urls.split(',') if url.strip()] if evidence_urls else []

        # Perform analysis
        claims, metrics = analyzer.analyze(
            question=question,
            answer=answer,
            evidence_text=evidence_text,
            evidence_urls=urls
        )

        # Save to storage
        import uuid
        analysis_id = str(uuid.uuid4())
        try:
            storage.save_evaluation(
                analysis_id=analysis_id,
                question=question,
                answer=answer,
                evidence_text=evidence_text,
                evidence_urls=urls,
                claims=[c.model_dump() for c in claims],
                metrics=metrics,
                processing_time=metrics.get('processing_time_seconds', 0)
            )
        except Exception as e:
            # Continue even if storage fails
            pass

        # Generate claims HTML
        claims_html = generate_claims_html(claims)

        # Format metrics
        metrics_json = json.dumps(metrics, indent=2)

        return claims_html, metrics_json, f"✅ Analysis complete! Found {len(claims)} claims."

    except Exception as e:
        return "", json.dumps({}), f"❌ Error during analysis: {str(e)}"


def generate_claims_html(claims: List) -> str:
    """Generate HTML display for claims."""
    if not claims:
        return "<div class='empty-state'><div class='empty-state-icon'>📝</div><p>No claims found in the answer.</p></div>"

    html = "<div style='display: flex; flex-direction: column; gap: 1rem;'>"

    for i, claim in enumerate(claims, 1):
        status_class = f"status-{claim.status.value}"
        status_emoji = {
            'supported': '✅',
            'contradicted': '❌',
            'insufficient_evidence': '⚠️'
        }.get(claim.status.value, '❓')

        html += f"""
        <div style='background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.5rem;'>
            <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;'>
                <span style='font-size: 1.5rem;'>{status_emoji}</span>
                <span class='{status_class}' style='text-transform: capitalize;'>
                    {claim.status.value.replace('_', ' ')}
                </span>
                <span style='color: var(--text-secondary); margin-left: auto;'>
                    Confidence: {claim.confidence:.1%}
                </span>
            </div>

            <div style='margin-bottom: 1rem;'>
                <strong style='color: var(--accent-cyan);'>Claim {i}:</strong>
                <p style='color: var(--text-primary); margin-top: 0.5rem;'>{claim.text}</p>
            </div>

            <div style='margin-bottom: 1rem;'>
                <strong style='color: var(--text-secondary);'>Explanation:</strong>
                <p style='color: var(--text-primary); margin-top: 0.5rem;'>{claim.explanation}</p>
            </div>
        """

        if claim.supporting_evidence:
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <strong style='color: var(--success);'>Supporting Evidence:</strong>
                <ul style='margin-top: 0.5rem; padding-left: 1.5rem;'>
            """
            for evidence in claim.supporting_evidence:
                html += f"<li style='color: var(--text-primary); margin-bottom: 0.25rem;'>{evidence}</li>"
            html += "</ul></div>"

        if claim.contradicting_evidence:
            html += f"""
            <div style='margin-bottom: 1rem;'>
                <strong style='color: var(--error);'>Contradicting Evidence:</strong>
                <ul style='margin-top: 0.5rem; padding-left: 1.5rem;'>
            """
            for evidence in claim.contradicting_evidence:
                html += f"<li style='color: var(--text-primary); margin-bottom: 0.25rem;'>{evidence}</li>"
            html += "</ul></div>"

        if claim.sources:
            html += f"""
            <div>
                <strong style='color: var(--accent-violet);'>Sources:</strong>
                <ul style='margin-top: 0.5rem; padding-left: 1.5rem;'>
            """
            for source in claim.sources:
                html += f"<li style='color: var(--text-primary); margin-bottom: 0.25rem;'>{source.title or source.content}</li>"
            html += "</ul></div>"

        html += "</div>"

    html += "</div>"
    return html


def get_history() -> str:
    """Get evaluation history as HTML table."""
    try:
        history = storage.get_history(limit=20)

        if not history:
            return "<div class='empty-state'><div class='empty-state-icon'>📊</div><p>No evaluation history yet.</p></div>"

        # Create DataFrame
        data = []
        for entry in history:
            data.append({
                'Timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M'),
                'Question': entry.question[:50] + '...' if len(entry.question) > 50 else entry.question,
                'Total Claims': entry.total_claims,
                'Supported': entry.supported_claims,
                'Contradicted': entry.contradicted_claims,
                'Insufficient': entry.insufficient_evidence_claims
            })

        df = pd.DataFrame(data)
        return df.to_html(index=False, classes='gr-dataframe')

    except Exception as e:
        return f"<p style='color: var(--error);'>Error loading history: {str(e)}</p>"


def get_metrics_summary() -> str:
    """Get metrics summary as HTML."""
    try:
        summary = storage.get_metrics_summary()

        html = """
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;'>
        """

        metrics = [
            ('Total Evaluations', summary['total_evaluations'], '📊'),
            ('Total Claims Analyzed', summary['total_claims'], '📝'),
            ('Avg Support Rate', f"{summary['average_support_rate']}%", '✅'),
            ('Avg Contradiction Rate', f"{summary['average_contradiction_rate']}%", '❌')
        ]

        for label, value, emoji in metrics:
            html += f"""
            <div class='metric-card'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{emoji}</div>
                <div class='metric-value'>{value}</div>
                <div class='metric-label'>{label}</div>
            </div>
            """

        html += "</div>"
        return html

    except Exception as e:
        return f"<p style='color: var(--error);'>Error loading metrics: {str(e)}</p>"


def export_report(claims_html: str, metrics_json: str) -> str:
    """Generate a downloadable report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report = f"""
# ProofPilot AI Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics
{metrics_json}

## Claims
{claims_html.replace('<div', '\n<div').replace('</div>', '</div>\n')}
    """
    return report


# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), 'ui', 'theme.css')
try:
    with open(css_path, 'r') as f:
        custom_css = f.read()
except FileNotFoundError:
    # Fallback if CSS file is not found
    custom_css = ""


# Sample data for first-run demonstration
SAMPLE_QUESTION = "What is the capital of France?"
SAMPLE_ANSWER = "The capital of France is Paris. It is located in the northern part of the country and has a population of approximately 2.1 million people in the city proper."
SAMPLE_EVIDENCE = "Paris is the capital and most populous city of France. With an official estimated population of 2,102,650 residents as of 1 January 2023 in an area of more than 105 km², Paris is the 30th most densely populated city in the world in 2020."


# Create Gradio interface
with gr.Blocks(title="ProofPilot AI - Real-Time AI Reliability Lab") as demo:
    gr.Markdown("""
    # ProofPilot AI
    ## Real-Time AI Reliability Lab
    **Test AI answers. Verify evidence. Measure reliability.**
    """)

    with gr.Tabs():
        # Tab 1: Analysis
        with gr.Tab("🔍 Analyze"):
            gr.Markdown("""
            ### Verify AI-Generated Answers
            Enter a question and AI-generated answer, then provide evidence to verify the claims.

            **Try the example** below to see how it works!
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    question_input = gr.Textbox(
                        label="Question",
                        placeholder="Enter the original question...",
                        lines=2,
                        value=SAMPLE_QUESTION
                    )

                    answer_input = gr.Textbox(
                        label="AI-Generated Answer",
                        placeholder="Paste the AI-generated answer here...",
                        lines=5,
                        value=SAMPLE_ANSWER
                    )

                with gr.Column(scale=1):
                    evidence_text_input = gr.Textbox(
                        label="Evidence Text (Optional)",
                        placeholder="Paste trusted evidence text here...",
                        lines=5,
                        value=SAMPLE_EVIDENCE
                    )

                    evidence_urls_input = gr.Textbox(
                        label="Evidence URLs (Optional, comma-separated)",
                        placeholder="https://example.com/source1, https://example.com/source2"
                    )

            clear_btn = gr.Button("🗑️ Clear", variant="secondary")
            analyze_btn = gr.Button("🚀 Analyze Reliability", variant="primary", size="lg")

            with gr.Row():
                status_output = gr.Textbox(label="Status", interactive=False)
                metrics_output = gr.Code(label="Metrics", language="json", interactive=False)

            claims_output = gr.HTML(label="Analysis Results")

            with gr.Row():
                export_btn = gr.Button("📥 Export Report", variant="secondary")
                report_output = gr.Code(label="Report", language="markdown", visible=False)

            # Clear button functionality
            clear_btn.click(
                fn=lambda: ("", "", "", "", "", json.dumps({}), ""),
                outputs=[question_input, answer_input, evidence_text_input, evidence_urls_input,
                        status_output, metrics_output, claims_output]
            )

            analyze_btn.click(
                fn=analyze_reliability,
                inputs=[question_input, answer_input, evidence_text_input, evidence_urls_input],
                outputs=[claims_output, metrics_output, status_output]
            )

            export_btn.click(
                fn=export_report,
                inputs=[claims_output, metrics_output],
                outputs=[report_output]
            )

        # Tab 2: History
        with gr.Tab("📊 History"):
            gr.Markdown("### Evaluation History")
            history_output = gr.HTML()
            refresh_history_btn = gr.Button("🔄 Refresh", variant="secondary")

            refresh_history_btn.click(
                fn=get_history,
                outputs=[history_output]
            )

            # Load history on tab open
            demo.load(get_history, outputs=[history_output])

        # Tab 3: Metrics
        with gr.Tab("📈 Metrics"):
            gr.Markdown("### Aggregated Metrics")
            metrics_summary_output = gr.HTML()
            refresh_metrics_btn = gr.Button("🔄 Refresh", variant="secondary")

            refresh_metrics_btn.click(
                fn=get_metrics_summary,
                outputs=[metrics_summary_output]
            )

            # Load metrics on tab open
            demo.load(get_metrics_summary, outputs=[metrics_summary_output])

        # Tab 4: About
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## About ProofPilot AI

            ProofPilot AI is a professional AI evaluation tool that verifies AI-generated claims against user-supplied evidence.

            ### Features

            - **Claim Extraction**: Automatically extracts checkable claims from AI-generated answers
            - **Evidence Verification**: Compares claims against trusted evidence sources
            - **Transparent Classification**: Clear support, contradiction, and insufficient-evidence labels
            - **Real-Time Metrics**: Evidence support rate, contradiction rate, source coverage, and more
            - **Exportable Reports**: Download detailed evaluation reports

            ### How It Works

            1. Enter a question and AI-generated answer
            2. Provide evidence as text or URLs
            3. Click "Analyze Reliability"
            4. Review the verification results for each claim
            5. Export a detailed report if needed

            ### Limitations

            - Baseline verification uses heuristic matching; it may miss nuanced relationships
            - URL retrieval depends on network accessibility and website availability
            - Evidence similarity scores are not proof of factual correctness
            - **Data Persistence**: This Space uses ephemeral storage. Evaluation history will be lost when the Space restarts or rebuilds.
            - For production use, consider integrating with advanced NLI models or LLM APIs and deploying to a cloud VM with persistent storage

            ### Technology Stack

            - **Frontend & Backend**: Gradio 4.7.1 with custom CSS
            - **Storage**: SQLite (ephemeral in Hugging Face Spaces)
            - **Evaluation**: Heuristic text matching (extensible for NLI models)
            - **Dependencies**: httpx, BeautifulSoup4, lxml, pandas

            ### Version

            **ProofPilot AI v1.0.0**

            Built for technology competitions and portfolio demonstrations.
            """)

    gr.Markdown("""
    ---
    **ProofPilot AI** - Real-Time AI Reliability Lab
    This is a demonstration project. For critical decision-making, ensure proper validation and extension for your specific use case.

    **Hosted on Hugging Face Spaces** | Data is stored temporarily and may be cleared on Space restart.
    """)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=settings.gradio_port,
        share=False,  # Set to True to generate a public share link
        css=custom_css
    )
