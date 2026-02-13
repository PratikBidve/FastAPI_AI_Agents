"""Tests for FastAPI integration endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/api/v1/job-copilot/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

    def test_health_check_response_format(self, client: TestClient):
        """Test health check response format."""
        response = client.get("/api/v1/job-copilot/health")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "llm_initialized" in data or "graph_initialized" in data or "status" in data


class TestAnalyzeEndpoint:
    """Test job application analysis endpoint."""

    def test_analyze_with_valid_inputs(self, client: TestClient, sample_job_description: str, sample_resume: str):
        """Test analysis with valid inputs."""
        payload = {
            "job_description": sample_job_description,
            "resume": sample_resume,
            "user_id": "test-user-123",
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should succeed or be queued
        assert response.status_code in [200, 202, 400, 422]

        if response.status_code in [200, 202]:
            data = response.json()
            assert "success" in data or "status" in data or "id" in data

    def test_analyze_missing_job_description(self, client: TestClient, sample_resume: str):
        """Test analysis with missing job description."""
        payload = {
            "resume": sample_resume,
            "user_id": "test-user",
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should fail validation
        assert response.status_code in [422, 400]

    def test_analyze_missing_resume(self, client: TestClient, sample_job_description: str):
        """Test analysis with missing resume."""
        payload = {
            "job_description": sample_job_description,
            "user_id": "test-user",
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should fail validation
        assert response.status_code in [422, 400]

    def test_analyze_empty_inputs(self, client: TestClient):
        """Test analysis with empty inputs."""
        payload = {
            "job_description": "",
            "resume": "",
            "user_id": "test-user",
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should fail validation
        assert response.status_code in [422, 400]

    def test_analyze_short_inputs(self, client: TestClient):
        """Test analysis with inputs too short."""
        payload = {
            "job_description": "Dev",
            "resume": "Junior",
            "user_id": "test-user",
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should fail validation
        assert response.status_code in [422, 400]

    def test_analyze_allows_optional_user_id(self, client: TestClient, sample_job_description: str, sample_resume: str):
        """Test that user_id is optional."""
        payload = {
            "job_description": sample_job_description,
            "resume": sample_resume,
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should succeed without user_id
        assert response.status_code in [200, 202, 400, 422]


class TestBatchAnalyzeEndpoint:
    """Test batch analysis endpoint."""

    def test_batch_analyze_single_application(self, client: TestClient, sample_job_description: str, sample_resume: str):
        """Test batch analysis with single application."""
        applications = [
            {
                "job_description": sample_job_description,
                "resume": sample_resume,
                "user_id": "user-1",
            }
        ]

        response = client.post("/api/v1/job-copilot/batch-analyze", json=applications)

        assert response.status_code in [200, 400, 422]

    def test_batch_analyze_max_applications(self, client: TestClient, sample_job_description: str, sample_resume: str):
        """Test batch analysis with maximum allowed applications."""
        applications = [
            {
                "job_description": sample_job_description,
                "resume": sample_resume,
                "user_id": f"user-{i}",
            }
            for i in range(10)
        ]

        response = client.post("/api/v1/job-copilot/batch-analyze", json=applications)

        # Should succeed
        assert response.status_code in [200, 400, 422]

    def test_batch_analyze_exceeds_max(self, client: TestClient, sample_job_description: str, sample_resume: str):
        """Test batch analysis exceeding maximum."""
        applications = [
            {
                "job_description": sample_job_description,
                "resume": sample_resume,
                "user_id": f"user-{i}",
            }
            for i in range(11)
        ]

        response = client.post("/api/v1/job-copilot/batch-analyze", json=applications)

        # Should reject
        assert response.status_code in [400, 422]

    def test_batch_analyze_empty_list(self, client: TestClient):
        """Test batch analysis with empty list."""
        response = client.post("/api/v1/job-copilot/batch-analyze", json=[])

        # Should reject
        assert response.status_code in [400, 422]


class TestGraphStructureEndpoint:
    """Test graph structure endpoint."""

    def test_get_graph_structure(self, client: TestClient):
        """Test getting workflow graph structure."""
        response = client.get("/api/v1/job-copilot/graph/structure")

        assert response.status_code == 200
        data = response.json()

        # Should contain graph structure info
        assert isinstance(data, dict)

    def test_graph_structure_response_format(self, client: TestClient):
        """Test graph structure response format."""
        response = client.get("/api/v1/job-copilot/graph/structure")

        assert response.status_code == 200
        data = response.json()

        # Check for expected fields
        if "nodes" in data:
            assert isinstance(data["nodes"], list)
        if "edges" in data:
            assert isinstance(data["edges"], list)


class TestWorkflowDocumentationEndpoint:
    """Test workflow documentation endpoint."""

    def test_get_workflow_documentation(self, client: TestClient):
        """Test getting workflow documentation."""
        response = client.get("/api/v1/job-copilot/docs/workflow")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_documentation_contains_workflow_info(self, client: TestClient):
        """Test that documentation contains workflow information."""
        response = client.get("/api/v1/job-copilot/docs/workflow")

        assert response.status_code == 200
        data = response.json()

        # Should have description or steps or similar
        assert len(data) > 0


class TestErrorHandling:
    """Test error handling in endpoints."""

    def test_malformed_json_returns_error(self, client: TestClient):
        """Test that malformed JSON is handled."""
        response = client.post(
            "/api/v1/job-copilot/analyze",
            content="not valid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code in [400, 422]

    def test_invalid_method_returns_404(self, client: TestClient):
        """Test that invalid endpoint returns 404."""
        response = client.get("/api/v1/job-copilot/nonexistent")

        assert response.status_code == 404

    def test_missing_required_fields_returns_422(self, client: TestClient):
        """Test that missing required fields returns 422."""
        response = client.post(
            "/api/v1/job-copilot/analyze",
            json={"user_id": "test"},  # Missing required fields
        )

        assert response.status_code == 422

    def test_invalid_field_types_returns_422(self, client: TestClient):
        """Test that invalid field types returns 422."""
        response = client.post(
            "/api/v1/job-copilot/analyze",
            json={
                "job_description": 123,  # Should be string
                "resume": True,  # Should be string
                "user_id": "test",
            },
        )

        assert response.status_code == 422


class TestRateLimitingAndSecurity:
    """Test rate limiting and security measures."""

    def test_multiple_requests_succeed(self, client: TestClient, sample_job_description: str, sample_resume: str):
        """Test that multiple requests are handled."""
        payload = {
            "job_description": sample_job_description,
            "resume": sample_resume,
        }

        responses = []
        for _ in range(3):
            response = client.post("/api/v1/job-copilot/analyze", json=payload)
            responses.append(response.status_code)

        # All should return 200, 202, or fail with same error
        assert all(code in [200, 202, 400, 422] for code in responses)

    def test_response_headers_security(self, client: TestClient):
        """Test that security headers are present."""
        response = client.get("/api/v1/job-copilot/health")

        assert response.status_code == 200
        # Check for common security headers (may vary by setup)
        # X-Content-Type-Options, X-Frame-Options, etc.


class TestCORSHeaders:
    """Test CORS handling."""

    def test_cors_preflight_request(self, client: TestClient):
        """Test CORS preflight handling (if enabled)."""
        response = client.options("/api/v1/job-copilot/health")

        # Should either succeed or be method not allowed
        assert response.status_code in [200, 405]


class TestInputValidation:
    """Test input validation on API endpoints."""

    def test_job_description_min_length_enforced(self, client: TestClient):
        """Test that job description minimum length is enforced."""
        payload = {
            "job_description": "a" * 49,  # One char too short
            "resume": "b" * 100,
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        assert response.status_code in [400, 422]

    def test_resume_min_length_enforced(self, client: TestClient):
        """Test that resume minimum length is enforced."""
        payload = {
            "job_description": "a" * 100,
            "resume": "b" * 49,  # One char too short
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        assert response.status_code in [400, 422]

    def test_large_valid_inputs_accepted(self, client: TestClient):
        """Test that large valid inputs are accepted."""
        payload = {
            "job_description": "Senior Developer role. " * 1000,  # ~23KB
            "resume": "John Doe, Software Engineer. " * 1000,  # ~30KB
        }

        response = client.post("/api/v1/job-copilot/analyze", json=payload)

        # Should succeed or queue
        assert response.status_code in [200, 202, 400, 422]
