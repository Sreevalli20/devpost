"""Automated tests for ProofPilot AI."""
import unittest
import json
import os
import tempfile
from app import app
from core.analyzer import ClaimAnalyzer
from core.storage import Storage
from core.metrics import MetricsCalculator
from core.schemas import Claim, VerificationStatus, EvidenceSource


class TestClaimAnalyzer(unittest.TestCase):
    """Test the claim analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ClaimAnalyzer()

    def test_extract_claims(self):
        """Test claim extraction from text."""
        text = "Paris is the capital of France. It has a population of 2.1 million."
        claims = self.analyzer.extract_claims(text)
        self.assertGreater(len(claims), 0)
        self.assertTrue(any("Paris" in claim for claim in claims))

    def test_extract_claims_filters_questions(self):
        """Test that questions are filtered out."""
        text = "What is the capital? Paris is the capital."
        claims = self.analyzer.extract_claims(text)
        self.assertFalse(any("capital?" in claim for claim in claims))

    def test_verify_claim_with_evidence(self):
        """Test claim verification with supporting evidence."""
        claim = "Paris is the capital of France"
        evidence = "Paris is the capital and most populous city of France."
        result = self.analyzer.verify_claim(claim, evidence, [])
        self.assertIn(result.status, [VerificationStatus.SUPPORTED, VerificationStatus.INSUFFICIENT_EVIDENCE])

    def test_verify_claim_no_evidence(self):
        """Test claim verification without evidence."""
        claim = "Paris is the capital of France"
        result = self.analyzer.verify_claim(claim, "", [])
        self.assertEqual(result.status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_verify_claim_contradicted(self):
        """Test claim verification with contradicting evidence."""
        claim = "Paris is the capital of France"
        evidence = "Lyon is the capital of France, not Paris."
        result = self.analyzer.verify_claim(claim, evidence, [])
        self.assertEqual(result.status, VerificationStatus.CONTRADICTED)
        # Ensure supporting evidence is cleared when contradicted
        self.assertEqual(len(result.supporting_evidence), 0)

    def test_analyze_complete(self):
        """Test complete analysis workflow."""
        question = "What is the capital of France?"
        answer = "Paris is the capital of France."
        evidence = "Paris is the capital of France."
        claims, metrics = self.analyzer.analyze(question, answer, evidence, [])
        self.assertGreater(len(claims), 0)
        self.assertIn('total_claims', metrics)
        self.assertIn('evidence_support_rate', metrics)


class TestMetricsCalculator(unittest.TestCase):
    """Test the metrics calculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MetricsCalculator()

    def test_calculate_with_claims(self):
        """Test metrics calculation with claims."""
        claims = [
            Claim(
                text="Test claim 1",
                status=VerificationStatus.SUPPORTED,
                explanation="Test",
                confidence=0.8
            ),
            Claim(
                text="Test claim 2",
                status=VerificationStatus.CONTRADICTED,
                explanation="Test",
                confidence=0.7
            )
        ]
        metrics = self.calculator.calculate(claims)
        self.assertEqual(metrics['total_claims'], 2)
        self.assertEqual(metrics['supported_claims'], 1)
        self.assertEqual(metrics['contradicted_claims'], 1)
        self.assertEqual(metrics['evidence_support_rate'], 50.0)

    def test_calculate_empty(self):
        """Test metrics calculation with no claims."""
        metrics = self.calculator.calculate([])
        self.assertEqual(metrics['total_claims'], 0)
        self.assertEqual(metrics['evidence_support_rate'], 0.0)


class TestStorage(unittest.TestCase):
    """Test the storage layer."""

    def setUp(self):
        """Set up test fixtures with temporary database."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.storage = Storage(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_save_and_retrieve(self):
        """Test saving and retrieving an evaluation."""
        analysis_id = "test-123"
        self.storage.save_evaluation(
            analysis_id=analysis_id,
            question="Test question",
            answer="Test answer",
            evidence_text="Test evidence",
            evidence_urls=[],
            claims=[],
            metrics={'total_claims': 0},
            processing_time=1.0
        )
        retrieved = self.storage.get_evaluation(analysis_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['question'], "Test question")

    def test_get_history(self):
        """Test retrieving evaluation history."""
        self.storage.save_evaluation(
            analysis_id="test-1",
            question="Question 1",
            answer="Answer 1",
            evidence_text="",
            evidence_urls=[],
            claims=[],
            metrics={'total_claims': 1, 'supported_claims': 1, 'contradicted_claims': 0, 'insufficient_evidence_claims': 0},
            processing_time=1.0
        )
        history = self.storage.get_history(limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].question, "Question 1")

    def test_get_metrics_summary(self):
        """Test retrieving metrics summary."""
        self.storage.save_evaluation(
            analysis_id="test-1",
            question="Question 1",
            answer="Answer 1",
            evidence_text="",
            evidence_urls=[],
            claims=[],
            metrics={'total_claims': 1, 'evidence_support_rate': 100.0, 'contradiction_rate': 0.0},
            processing_time=1.0
        )
        summary = self.storage.get_metrics_summary()
        self.assertEqual(summary['total_evaluations'], 1)
        self.assertEqual(summary['total_claims'], 1)

    def test_clear_all_evaluations(self):
        """Test clearing all evaluations."""
        self.storage.save_evaluation(
            analysis_id="test-1",
            question="Question 1",
            answer="Answer 1",
            evidence_text="",
            evidence_urls=[],
            claims=[],
            metrics={'total_claims': 1},
            processing_time=1.0
        )
        self.storage.clear_all_evaluations()
        history = self.storage.get_history(limit=10)
        self.assertEqual(len(history), 0)


class TestFlaskApp(unittest.TestCase):
    """Test the Flask application."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_index_page(self):
        """Test the index page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ProofPilot AI', response.data)

    def test_analyze_endpoint(self):
        """Test the analyze endpoint."""
        response = self.client.post('/api/analyze',
            data=json.dumps({
                'question': 'Test question',
                'answer': 'Paris is the capital of France.',
                'evidence_text': 'Paris is the capital of France.',
                'evidence_urls': []
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('claims', data)
        self.assertIn('metrics', data)
        self.assertIn('analysis_id', data)

    def test_analyze_missing_answer(self):
        """Test analyze endpoint with missing answer."""
        response = self.client.post('/api/analyze',
            data=json.dumps({
                'question': 'Test question',
                'answer': '',
                'evidence_text': '',
                'evidence_urls': []
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_history_endpoint(self):
        """Test the history endpoint."""
        response = self.client.get('/api/history')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('history', data)

    def test_metrics_endpoint(self):
        """Test the metrics endpoint."""
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_evaluations', data)

    def test_clear_history_endpoint(self):
        """Test the clear history endpoint."""
        response = self.client.delete('/api/history')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)


if __name__ == '__main__':
    unittest.main()
