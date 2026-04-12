from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app


class APIEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_should_return_health_status(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "0.1.0")

    @patch("api.main.run_weekly_workflow")
    def test_should_trigger_weekly_workflow(self, mock_workflow: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.ai_review_packet_path = Path("reports/ai-review/test.json")
        mock_result.weekly_report_path = Path("reports/weekly/test.md")
        mock_result.promoted_config_path = None
        mock_result.error = None
        mock_result.details = ["Step 1", "Step 2"]
        mock_workflow.return_value = mock_result

        response = self.client.post("/api/v1/weekly-workflow")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["ai_review_packet_path"])
        self.assertIsNotNone(data["weekly_report_path"])
        self.assertEqual(len(data["details"]), 2)

    @patch("api.main.summarize_parameter_change_registry")
    def test_should_return_governance_summary(self, mock_summarize: MagicMock) -> None:
        mock_summarize.return_value = {
            "total": 5,
            "pending": 2,
            "approved": 2,
            "rejected": 1,
            "ready_to_promote": 2,
        }

        response = self.client.get("/api/v1/governance/summary")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 5)
        self.assertEqual(data["approved"], 2)
        self.assertEqual(data["ready_to_promote"], 2)

    @patch("api.main.load_parameter_change_requests")
    def test_should_list_governance_requests(self, mock_load: MagicMock) -> None:
        mock_load.return_value = [
            {
                "request_id": "req-001",
                "status": "pending",
                "validation": {"is_valid": True},
                "promoted": False,
            },
            {
                "request_id": "req-002",
                "status": "approved",
                "validation": {"is_valid": True},
                "promoted": False,
            },
        ]

        response = self.client.get("/api/v1/governance/requests")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["request_id"], "req-001")
        self.assertEqual(data[1]["status"], "approved")

    @patch("api.main.update_request_status_by_id")
    def test_should_approve_request(self, mock_update: MagicMock) -> None:
        mock_update.return_value = True

        response = self.client.post(
            "/api/v1/governance/approve",
            json={"request_id": "req-001", "status": "approved"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["updated"])
        self.assertEqual(data["status"], "approved")

    def test_should_reject_invalid_approval_status(self) -> None:
        response = self.client.post(
            "/api/v1/governance/approve",
            json={"request_id": "req-001", "status": "invalid_status"},
        )

        self.assertEqual(response.status_code, 400)

    @patch("api.main.promote_approved_requests")
    def test_should_promote_requests_when_approved_exist(self, mock_promote: MagicMock) -> None:
        mock_promote.return_value = Path(
            "reports/strategy-configs/v1-abc123.json")

        response = self.client.post("/api/v1/governance/promote")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["promoted"])
        self.assertIsNotNone(data["config_path"])

    @patch("api.main.promote_approved_requests")
    def test_should_handle_no_approved_requests(self, mock_promote: MagicMock) -> None:
        mock_promote.return_value = None

        response = self.client.post("/api/v1/governance/promote")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["promoted"])
        self.assertEqual(data["reason"], "no-approved-valid-requests")


if __name__ == "__main__":
    unittest.main()
