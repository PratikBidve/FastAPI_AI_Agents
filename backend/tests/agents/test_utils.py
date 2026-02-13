"""Unit tests for Job Copilot utilities."""

from app.services.agents.utils import (
    export_workflow_result,
    format_for_json,
    get_summary,
    merge_results,
    validate_inputs,
)


class TestValidateInputs:
    """Test input validation."""

    def test_valid_inputs(self, sample_job_description: str, sample_resume: str):
        """Test that valid inputs pass validation."""
        is_valid, error = validate_inputs(sample_job_description, sample_resume)
        assert is_valid is True
        assert error is None

    def test_empty_job_description(self, empty_job_description: str, sample_resume: str):
        """Test that empty job description fails validation."""
        is_valid, error = validate_inputs(empty_job_description, sample_resume)
        assert is_valid is False
        assert error is not None
        assert "required" in error.lower()

    def test_empty_resume(self, sample_job_description: str, empty_resume: str):
        """Test that empty resume fails validation."""
        is_valid, error = validate_inputs(sample_job_description, empty_resume)
        assert is_valid is False
        assert error is not None
        assert "required" in error.lower()

    def test_short_job_description(self, short_job_description: str, sample_resume: str):
        """Test that short job description fails validation."""
        is_valid, error = validate_inputs(short_job_description, sample_resume)
        assert is_valid is False
        assert error is not None
        assert "50 characters" in error

    def test_short_resume(self, sample_job_description: str, short_resume: str):
        """Test that short resume fails validation."""
        is_valid, error = validate_inputs(sample_job_description, short_resume)
        assert is_valid is False
        assert error is not None
        assert "50 characters" in error

    def test_both_empty(self, empty_job_description: str, empty_resume: str):
        """Test that both empty fails with job description error first."""
        is_valid, error = validate_inputs(empty_job_description, empty_resume)
        assert is_valid is False
        assert error is not None


class TestExportWorkflowResult:
    """Test workflow result exporting."""

    def test_export_complete_result(self):
        """Test exporting a complete workflow result."""
        result = {
            "job_description_raw": "Sample JD",
            "resume_raw": "Sample Resume",
            "job_description": {
                "title": "Senior Dev",
                "company": "TechCorp",
                "location": "SF",
                "salary_range": "$150-200k",
                "requirements": ["Python", "FastAPI"],
            },
            "resume_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python", "FastAPI"],
                "experience_years": 5,
            },
            "resume_analysis": {
                "overall_fit_score": 0.85,
                "skills_score": 0.9,
                "experience_score": 0.8,
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": [],
                "strengths": ["Strong Python skills"],
                "recommendations": ["Learn Kubernetes"],
            },
            "matching_score": 0.85,
            "cover_letter": {
                "tone": "professional",
                "content": "Dear Hiring Manager...",
                "highlighted_skills": ["Python"],
                "key_achievements": ["Led team of 3"],
            },
            "nodes_executed": ["parse_jd", "analyze_resume", "generate_cover_letter"],
            "error": None,
        }

        exported = export_workflow_result(result)

        assert exported["success"] is True
        assert exported["job_application"]["title"] == "Senior Dev"
        assert exported["job_application"]["company"] == "TechCorp"
        assert exported["fit_assessment"]["overall_score"] == 0.85
        assert len(exported["matched_skills"]) == 2
        assert len(exported["missing_skills"]) == 0
        assert exported["cover_letter"]["content"] == "Dear Hiring Manager..."
        assert len(exported["metadata"]["nodes_executed"]) == 3

    def test_export_partial_result(self):
        """Test exporting result with missing fields."""
        result = {
            "job_description_raw": "Sample JD",
            "resume_raw": "Sample Resume",
            "job_description": {"title": "Dev"},
            "resume_data": None,
            "resume_analysis": None,
            "matching_score": None,
            "cover_letter": None,
            "nodes_executed": ["parse_jd"],
            "error": "Analysis failed",
        }

        exported = export_workflow_result(result)

        assert exported["success"] is True
        assert exported["job_application"]["title"] == "Dev"
        assert exported["fit_assessment"]["overall_score"] is None
        assert exported["cover_letter"]["content"] is None

    def test_export_empty_result(self):
        """Test exporting an empty result."""
        result = {
            "job_description_raw": "",
            "resume_raw": "",
            "job_description": None,
            "resume_data": None,
            "resume_analysis": None,
            "matching_score": None,
            "cover_letter": None,
            "nodes_executed": [],
            "error": None,
        }

        exported = export_workflow_result(result)

        assert isinstance(exported, dict)
        assert exported["metadata"]["nodes_executed"] == []


class TestGetSummary:
    """Test summary generation."""

    def test_summary_with_complete_data(self):
        """Test generating summary from complete result."""
        result = {
            "job_description": {
                "title": "Senior Backend Engr",
                "company": "TechCorp",
            },
            "matching_score": 0.85,
            "resume_analysis": {
                "skills_score": 0.9,
                "experience_score": 0.8,
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["Kubernetes"],
                "strengths": ["Strong architecture", "Team lead experience"],
                "recommendations": ["Learn K8s", "Improve DevOps"],
            },
            "cover_letter": {"content": "Letter here"},
        }

        summary = get_summary(result)

        assert summary["job"]["title"] == "Senior Backend Engr"
        assert summary["job"]["company"] == "TechCorp"
        assert summary["fit_assessment"]["overall_score"] == "85.0%"
        assert len(summary["matched_skills"]) == 2
        assert len(summary["key_strengths"]) == 2
        assert summary["cover_letter_ready"] is True

    def test_summary_with_minimal_data(self):
        """Test generating summary from minimal result."""
        result = {
            "job_description": {},
            "matching_score": 0,
            "resume_analysis": {},
            "cover_letter": None,
        }

        summary = get_summary(result)

        assert summary["job"]["title"] is None
        assert summary["fit_assessment"]["overall_score"] == "0.0%"
        assert summary["cover_letter_ready"] is False


class TestFormatForJson:
    """Test JSON serialization formatting."""

    def test_format_datetime(self):
        """Test formatting datetime objects."""
        from datetime import datetime

        dt = datetime(2024, 2, 13, 15, 30, 0)
        formatted = format_for_json(dt)

        assert isinstance(formatted, str)
        assert "2024-02-13T15:30:00" in formatted

    def test_format_nested_dict(self):
        """Test formatting nested dictionaries."""
        from datetime import datetime

        obj = {
            "name": "John",
            "created": datetime(2024, 2, 13),
            "nested": {"inner": datetime(2024, 2, 12)},
        }

        formatted = format_for_json(obj)

        assert isinstance(formatted, dict)
        assert formatted["name"] == "John"
        assert "2024-02-13" in formatted["created"]
        assert "2024-02-12" in formatted["nested"]["inner"]

    def test_format_list(self):
        """Test formatting lists."""
        from datetime import datetime

        obj = [1, "string", datetime(2024, 2, 13), {"key": datetime(2024, 2, 12)}]

        formatted = format_for_json(obj)

        assert isinstance(formatted, list)
        assert formatted[0] == 1
        assert formatted[1] == "string"
        assert "2024-02-13" in formatted[2]
        assert "2024-02-12" in formatted[3]["key"]

    def test_format_primitives(self):
        """Test formatting primitive types."""
        assert format_for_json(42) == 42
        assert format_for_json("string") == "string"
        assert format_for_json(3.14) == 3.14
        assert format_for_json(True) is True
        assert format_for_json(None) is None


class TestMergeResults:
    """Test result merging."""

    def test_merge_two_results(self):
        """Test merging two workflow results."""
        result1 = {
            "job_description": {"title": "Dev"},
            "matching_score": 0.8,
            "metadata": {"source": "api"},
        }
        result2 = {
            "resume_analysis": {"skills": ["Python"]},
            "cover_letter": {"content": "Letter"},
        }

        merged = merge_results(result1, result2)

        assert merged["job_description"]["title"] == "Dev"
        assert merged["resume_analysis"]["skills"] == ["Python"]
        assert merged["matching_score"] == 0.8
        assert merged["cover_letter"]["content"] == "Letter"

    def test_merge_overwrites_keys(self):
        """Test that merge overwrites duplicate keys with result2."""
        result1 = {"score": 0.5, "name": "Result1"}
        result2 = {"score": 0.9, "extra": "field"}

        merged = merge_results(result1, result2)

        assert merged["score"] == 0.9
        assert merged["name"] == "Result1"
        assert merged["extra"] == "field"

    def test_merge_empty_results(self):
        """Test merging empty results."""
        result1 = {}
        result2 = {}

        merged = merge_results(result1, result2)

        assert isinstance(merged, dict)
        assert len(merged) == 0
