// ProofPilot AI - Frontend JavaScript

// State
let currentAnalysisId = null;

// DOM Elements
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const analyzeForm = document.getElementById('analyze-form');
const clearBtn = document.getElementById('clear-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const loadingDiv = document.getElementById('loading');
const resultsDiv = document.getElementById('results');
const errorDiv = document.getElementById('error');
const statusMessage = document.getElementById('status-message');
const metricsGrid = document.getElementById('metrics-grid');
const claimsContainer = document.getElementById('claims-container');
const exportMdBtn = document.getElementById('export-md-btn');
const exportJsonBtn = document.getElementById('export-json-btn');
const refreshHistoryBtn = document.getElementById('refresh-history-btn');
const refreshMetricsBtn = document.getElementById('refresh-metrics-btn');
const historyContainer = document.getElementById('history-container');
const metricsSummaryContainer = document.getElementById('metrics-summary-container');

// Tab Navigation
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.dataset.tab;

        // Update active tab
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update active content
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === tabId) {
                content.classList.add('active');
            }
        });

        // Load data when switching tabs
        if (tabId === 'history') {
            loadHistory();
        } else if (tabId === 'metrics') {
            loadMetrics();
        }
    });
});

// Form Submission
analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const question = document.getElementById('question').value.trim();
    const answer = document.getElementById('answer').value.trim();
    const evidenceText = document.getElementById('evidence-text').value.trim();
    const evidenceUrlsStr = document.getElementById('evidence-urls').value.trim();

    // Parse URLs
    const evidenceUrls = evidenceUrlsStr
        .split(',')
        .map(url => url.trim())
        .filter(url => url.length > 0);

    // Validate
    if (!answer) {
        showError('Please provide an answer to analyze.');
        return;
    }

    // Show loading
    loadingDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    analyzeBtn.disabled = true;

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question,
                answer,
                evidence_text: evidenceText,
                evidence_urls: evidenceUrls
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        currentAnalysisId = data.analysis_id;
        displayResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        loadingDiv.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
});

// Clear Form
clearBtn.addEventListener('click', () => {
    document.getElementById('question').value = '';
    document.getElementById('answer').value = '';
    document.getElementById('evidence-text').value = '';
    document.getElementById('evidence-urls').value = '';
    resultsDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    currentAnalysisId = null;
});

// Export Buttons
exportMdBtn.addEventListener('click', () => {
    if (!currentAnalysisId) {
        showError('No analysis to export.');
        return;
    }
    window.location.href = `/api/export/${currentAnalysisId}?format=markdown`;
});

exportJsonBtn.addEventListener('click', () => {
    if (!currentAnalysisId) {
        showError('No analysis to export.');
        return;
    }
    window.location.href = `/api/export/${currentAnalysisId}?format=json`;
});

// Refresh History
refreshHistoryBtn.addEventListener('click', loadHistory);

// Refresh Metrics
refreshMetricsBtn.addEventListener('click', loadMetrics);

// Display Results
function displayResults(data) {
    // Status message
    statusMessage.textContent = `✅ Analysis complete! Found ${data.claims.length} claims.`;

    // Metrics
    displayMetrics(data.metrics);

    // Claims
    displayClaims(data.claims);

    // Show results
    resultsDiv.classList.remove('hidden');
}

// Display Metrics
function displayMetrics(metrics) {
    metricsGrid.innerHTML = `
        <div class="metric-card">
            <div class="metric-value">${metrics.total_claims}</div>
            <div class="metric-label">Total Claims</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${metrics.supported_claims}</div>
            <div class="metric-label">Supported</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${metrics.contradicted_claims}</div>
            <div class="metric-label">Contradicted</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${metrics.insufficient_evidence_claims}</div>
            <div class="metric-label">Insufficient Evidence</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${metrics.evidence_support_rate}%</div>
            <div class="metric-label">Support Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${metrics.contradiction_rate}%</div>
            <div class="metric-label">Contradiction Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${metrics.source_coverage}</div>
            <div class="metric-label">Source Coverage</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${(metrics.average_confidence * 100).toFixed(0)}%</div>
            <div class="metric-label">Avg Confidence</div>
        </div>
    `;
}

// Display Claims
function displayClaims(claims) {
    if (claims.length === 0) {
        claimsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📝</div>
                <p>No claims found in the answer.</p>
            </div>
        `;
        return;
    }

    claimsContainer.innerHTML = claims.map((claim, index) => {
        const statusEmoji = {
            'supported': '✅',
            'contradicted': '❌',
            'insufficient_evidence': '⚠️'
        }[claim.status] || '❓';

        const statusClass = claim.status.replace('_', ' ');

        let supportingEvidenceHtml = '';
        if (claim.supporting_evidence && claim.supporting_evidence.length > 0) {
            supportingEvidenceHtml = `
                <div class="evidence-label">Supporting Evidence:</div>
                <ul class="evidence-list">
                    ${claim.supporting_evidence.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
                </ul>
            `;
        }

        let contradictingEvidenceHtml = '';
        if (claim.contradicting_evidence && claim.contradicting_evidence.length > 0) {
            contradictingEvidenceHtml = `
                <div class="evidence-label contradicting">Contradicting Evidence:</div>
                <ul class="evidence-list">
                    ${claim.contradicting_evidence.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
                </ul>
            `;
        }

        let sourcesHtml = '';
        if (claim.sources && claim.sources.length > 0) {
            sourcesHtml = `
                <div class="sources-label">Sources:</div>
                <ul class="evidence-list">
                    ${claim.sources.map(s => `<li>${escapeHtml(s.title || s.content)}</li>`).join('')}
                </ul>
            `;
        }

        return `
            <div class="claim-card">
                <div class="claim-header">
                    <span>${statusEmoji}</span>
                    <span class="claim-status ${statusClass}">${claim.status.replace('_', ' ')}</span>
                    <span class="claim-confidence">Confidence: ${(claim.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="claim-text"><strong>Claim ${index + 1}:</strong> ${escapeHtml(claim.text)}</div>
                <div class="claim-explanation"><strong>Explanation:</strong> ${escapeHtml(claim.explanation)}</div>
                ${supportingEvidenceHtml}
                ${contradictingEvidenceHtml}
                ${sourcesHtml}
            </div>
        `;
    }).join('');
}

// Load History
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load history');
        }

        displayHistory(data.history);
    } catch (error) {
        historyContainer.innerHTML = `
            <div class="error">
                Failed to load history: ${error.message}
            </div>
        `;
    }
}

// Display History
function displayHistory(history) {
    if (history.length === 0) {
        historyContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <p>No evaluation history yet.</p>
            </div>
        `;
        return;
    }

    historyContainer.innerHTML = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Question</th>
                    <th>Total Claims</th>
                    <th>Supported</th>
                    <th>Contradicted</th>
                    <th>Insufficient</th>
                </tr>
            </thead>
            <tbody>
                ${history.map(entry => `
                    <tr>
                        <td>${new Date(entry.timestamp).toLocaleString()}</td>
                        <td>${escapeHtml(entry.question.substring(0, 50))}${entry.question.length > 50 ? '...' : ''}</td>
                        <td>${entry.total_claims}</td>
                        <td>${entry.supported_claims}</td>
                        <td>${entry.contradicted_claims}</td>
                        <td>${entry.insufficient_evidence_claims}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Load Metrics
async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load metrics');
        }

        displayMetricsSummary(data);
    } catch (error) {
        metricsSummaryContainer.innerHTML = `
            <div class="error">
                Failed to load metrics: ${error.message}
            </div>
        `;
    }
}

// Display Metrics Summary
function displayMetricsSummary(metrics) {
    metricsSummaryContainer.innerHTML = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">${metrics.total_evaluations}</div>
                <div class="metric-label">Total Evaluations</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.total_claims}</div>
                <div class="metric-label">Total Claims Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.average_support_rate}%</div>
                <div class="metric-label">Avg Support Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.average_contradiction_rate}%</div>
                <div class="metric-label">Avg Contradiction Rate</div>
            </div>
        </div>
    `;
}

// Show Error
function showError(message) {
    errorDiv.textContent = `❌ ${message}`;
    errorDiv.classList.remove('hidden');
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Load history on initial load
    loadHistory();
});
