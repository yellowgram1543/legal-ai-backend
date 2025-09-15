import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import requests

# Add the project root to the Python path to allow importing from `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Functions to test from the new background workflow
from app.routes.analyze import analyze_text, trigger_analysis

class TestAnalysisWorkflow(unittest.TestCase):

    # --- Tests for analyze_text (the Gemini interaction) --- #

    @patch('app.routes.analyze._get_access_token', return_value="dummy_token")
    @patch('app.routes.analyze.requests.post')
    def test_analyze_text_success(self, mock_post, mock_token):
        """Tests the success case where the Gemini API returns a valid JSON response."""
        mock_response = MagicMock()
        api_output = {"summary": "S", "pros": ["P"], "cons": ["C"], "loopholes": ["L"]}
        mock_response.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(api_output)}]}}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = analyze_text("Some legal document text.")
        self.assertEqual(result, api_output)

    @patch('app.routes.analyze._get_access_token', return_value="dummy_token")
    @patch('app.routes.analyze.requests.post')
    def test_analyze_text_api_failure(self, mock_post, mock_token):
        """Tests the failure case where the API call raises an exception."""
        mock_post.side_effect = requests.exceptions.RequestException("API is down")

        expected_error_output = {"summary": "Failed to analyze document.", "pros": [], "cons": [], "loopholes": []}
        result = analyze_text("Some legal document text.")
        self.assertEqual(result, expected_error_output)

    def test_analyze_text_empty_input(self):
        """Tests that empty input returns a default structure without an API call."""
        expected_output = {"summary": "Document is empty.", "pros": [], "cons": [], "loopholes": []}
        result = analyze_text("   ")
        self.assertEqual(result, expected_output)

    # --- Tests for trigger_analysis (the background task orchestrator) --- #

    @patch('app.routes.analyze._update_status_in_db')
    @patch('app.routes.analyze._save_analysis_to_gcs')
    @patch('app.routes.analyze.analyze_text')
    @patch('app.routes.analyze.extract_text_with_docai')
    @patch('app.routes.analyze.RAW_BUCKET', 'test-bucket') # Mock the bucket name
    def test_trigger_analysis_success_workflow(self, mock_extract, mock_analyze, mock_save, mock_update_db):
        """Tests the entire successful background workflow orchestration."""
        # Setup mock return values
        doc_id_with_ext = "test-uuid.pdf"
        doc_id = "test-uuid"
        mime_type = "application/pdf"
        mock_extract.return_value = "Extracted text from document."
        mock_analyze.return_value = {"summary": "Analysis complete"}

        # Execute the orchestrator
        trigger_analysis(doc_id_with_ext, mime_type)

        # Assert that each step was called correctly
        mock_extract.assert_called_once_with('test-bucket', f"raw/{doc_id_with_ext}", mime_type)
        mock_analyze.assert_called_once_with("Extracted text from document.")
        mock_save.assert_called_once()
        # Check that status was updated multiple times
        self.assertEqual(mock_update_db.call_count, 3)
        mock_update_db.assert_has_calls([
            call(doc_id, "extracting_text"),
            call(doc_id, "analyzing"),
            call(doc_id, "processed"),
        ])

    @patch('app.routes.analyze._update_status_in_db')
    @patch('app.routes.analyze.extract_text_with_docai')
    @patch('app.routes.analyze.RAW_BUCKET', 'test-bucket')
    def test_trigger_analysis_empty_extraction(self, mock_extract, mock_update_db):
        """Tests that the workflow aborts if text extraction yields nothing."""
        doc_id_with_ext = "test-uuid.pdf"
        doc_id = "test-uuid"
        mime_type = "application/pdf"
        mock_extract.return_value = ""  # Simulate empty document

        trigger_analysis(doc_id_with_ext, mime_type)

        # Assert that the process stopped after extraction and updated status
        mock_extract.assert_called_once()
        mock_update_db.assert_has_calls([
            call(doc_id, "extracting_text"),
            call(doc_id, "error_empty_document"),
        ])

    @patch('app.routes.analyze._update_status_in_db')
    @patch('app.routes.analyze.extract_text_with_docai')
    @patch('app.routes.analyze.RAW_BUCKET', 'test-bucket')
    def test_trigger_analysis_fatal_error(self, mock_extract, mock_update_db):
        """Tests that a fatal error during the process is caught and status is updated."""
        doc_id_with_ext = "test-uuid.pdf"
        doc_id = "test-uuid"
        mime_type = "application/pdf"
        mock_extract.side_effect = Exception("Something went very wrong")

        trigger_analysis(doc_id_with_ext, mime_type)

        mock_update_db.assert_has_calls([
            call(doc_id, "extracting_text"),
            call(doc_id, "error_processing_failed"),
        ])

if __name__ == '__main__':
    unittest.main()
