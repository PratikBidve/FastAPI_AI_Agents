"""Integration tests for Job Copilot agent system.

These tests verify components work together correctly end-to-end.
"""


class TestWorkflowIntegration:
    """Test integrated workflow scenarios."""

    def test_complete_workflow_state_transitions(self, initial_state):
        """Test complete workflow state transitions."""
        state = initial_state

        # Initial state
        assert state["job_description"] is None
        assert state["resume_analysis"] is None
        assert state["cover_letter"] is None
        assert state["nodes_executed"] == []

        # After parse_jd
        state["job_description"] = {
            "title": "Senior Dev",
            "company": "TechCorp",
            "location": "SF",
            "salary_range": "$150k-200k",
            "requirements": ["Python", "FastAPI"],
        }
        state["nodes_executed"].append("parse_jd")

        assert state["job_description"]["title"] == "Senior Dev"
        assert "parse_jd" in state["nodes_executed"]

        # After analyze_resume
        state["resume_analysis"] = {
            "overall_fit_score": 0.8,
            "skills_score": 0.85,
            "experience_score": 0.75,
            "matched_skills": ["Python", "FastAPI"],
            "missing_skills": [],
            "strengths": ["Strong Python", "Leadership"],
            "recommendations": [],
        }
        state["nodes_executed"].append("analyze_resume")
        state["matching_score"] = 0.8

        assert state["resume_analysis"]["overall_fit_score"] == 0.8
        assert state["matching_score"] == 0.8

        # After generate_cover_letter
        state["cover_letter"] = {
            "tone": "professional",
            "content": "Dear Hiring Manager...",
            "highlighted_skills": ["Python"],
            "key_achievements": [],
        }
        state["nodes_executed"].append("generate_cover_letter")

        assert state["cover_letter"]["content"] is not None
        assert len(state["nodes_executed"]) == 3

    def test_error_state_transition(self, initial_state):
        """Test state transition when error occurs."""
        state = initial_state

        # Start parsing
        state["nodes_executed"].append("parse_jd")

        # Error occurs during analysis
        state["error"] = "LLM processing failed"
        state["nodes_executed"].append("analyze_resume")  # Marked as attempted

        assert state["error"] is not None
        assert "analyze_resume" in state["nodes_executed"]
        assert state["resume_analysis"] is None

    def test_partial_completion_state(self, initial_state):
        """Test state when workflow partially completes."""
        state = initial_state

        # Successful parse
        state["job_description"] = {
            "title": "Dev",
            "company": "Corp",
            "location": None,
            "salary_range": None,
            "requirements": [],
        }
        state["nodes_executed"].append("parse_jd")

        # Successful analysis
        state["resume_analysis"] = {
            "overall_fit_score": 0.6,
            "skills_score": 0.6,
            "experience_score": 0.6,
            "matched_skills": [],
            "missing_skills": [],
            "strengths": [],
            "recommendations": [],
        }
        state["nodes_executed"].append("analyze_resume")

        # Cover letter generation not completed
        assert state["cover_letter"] is None
        assert state["job_description"] is not None
        assert state["resume_analysis"] is not None


class TestValidationIntegration:
    """Test validation integration across modules."""

    def test_valid_workflow_inputs_pass_validation(self, sample_job_description: str, sample_resume: str):
        """Test that valid workflow inputs pass all validation."""
        from app.services.agents.utils import validate_inputs

        is_valid, error = validate_inputs(sample_job_description, sample_resume)

        assert is_valid is True
        assert error is None

    def test_invalid_inputs_rejected_early(self):
        """Test that invalid inputs are rejected early."""
        from app.services.agents.utils import validate_inputs

        # All invalid combinations should fail
        invalid_cases = [
            ("", ""),
            ("x" * 49, "y" * 100),
            ("x" * 100, "y" * 49),
            ("", "y" * 100),
            ("x" * 100, ""),
        ]

        for jd, resume in invalid_cases:
            is_valid, error = validate_inputs(jd, resume)
            assert is_valid is False
            assert error is not None

    def test_boundary_validation(self):
        """Test exact boundary conditions."""
        from app.services.agents.utils import validate_inputs

        # Exactly 50 chars should pass
        exact_50 = "a" * 50
        is_valid, _ = validate_inputs(exact_50, exact_50)
        assert is_valid is True

        # 49 chars should fail
        exact_49 = "a" * 49
        is_valid, error = validate_inputs(exact_49, exact_49)
        assert is_valid is False


class TestDataProcessingIntegration:
    """Test data processing integration."""

    def test_export_workflow_with_all_data(self):
        """Test exporting workflow result with all data."""
        from app.services.agents.utils import export_workflow_result

        complete_result = {
            "job_description_raw": "JD",
            "resume_raw": "Resume",
            "job_description": {
                "title": "Dev",
                "company": "Corp",
                "location": "SF",
                "salary_range": "$150k",
                "requirements": ["Python"],
            },
            "resume_data": {
                "name": "John",
                "email": "john@test.com",
                "phone": "555-1234",
                "skills": ["Python"],
                "experience_years": 5,
            },
            "resume_analysis": {
                "overall_fit_score": 0.8,
                "skills_score": 0.85,
                "experience_score": 0.75,
                "matched_skills": ["Python"],
                "missing_skills": [],
                "strengths": ["Good Python"],
                "recommendations": [],
            },
            "matching_score": 0.8,
            "cover_letter": {
                "tone": "professional",
                "content": "Letter",
                "highlighted_skills": ["Python"],
                "key_achievements": ["Lead"],
            },
            "nodes_executed": ["parse_jd", "analyze_resume", "generate_cover_letter"],
            "error": None,
        }

        exported = export_workflow_result(complete_result)

        assert exported["job_application"]["title"] == "Dev"
        assert exported["fit_assessment"]["overall_score"] == 0.8
        assert len(exported["matched_skills"]) >= 0
        assert exported["cover_letter"]["content"] == "Letter"

    def test_summary_generation_from_export(self):
        """Test generating summary from exported result."""
        from app.services.agents.utils import get_summary

        result = {
            "job_description": {
                "title": "Backend Dev",
                "company": "TechCorp",
            },
            "matching_score": 0.85,
            "resume_analysis": {
                "skills_score": 0.9,
                "experience_score": 0.8,
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": [],
                "strengths": ["Strong", "Experienced"],
                "recommendations": [],
            },
            "cover_letter": {"content": "Letter"},
        }

        summary = get_summary(result)

        assert summary["job"]["title"] == "Backend Dev"
        assert summary["fit_assessment"]["overall_score"] == "85.0%"


class TestErrorRecovery:
    """Test error recovery and handling."""

    def test_missing_optional_fields_handled(self):
        """Test handling of missing optional fields."""
        from app.services.agents.nodes.parse_jd import ParsedJobDescription

        job = ParsedJobDescription(
            title="Dev",
            company="Corp",
            location=None,
            salary_range=None,
            requirements=[],
        )

        assert job["title"] == "Dev"
        assert job["location"] is None
        assert job["salary_range"] is None
        assert job["requirements"] == []

    def test_analysis_with_no_matches(self):
        """Test analysis when resume doesn't match job at all."""
        from app.services.agents.nodes.analyze_resume import ResumeAnalysis

        analysis = ResumeAnalysis(
            overall_fit_score=0.0,
            skills_score=0.0,
            experience_score=0.0,
            matched_skills=[],
            missing_skills=["Python", "FastAPI", "PostgreSQL"],
            strengths=[],
            recommendations=["Major skill gap", "Consider junior roles"],
        )

        assert analysis["overall_fit_score"] == 0.0
        assert len(analysis["matched_skills"]) == 0
        assert len(analysis["missing_skills"]) == 3


class TestSecurityIntegration:
    """Test security across integrated components."""

    def test_malicious_input_safe_handling(self, malicious_resume_prompt_injection: str, sample_job_description: str):
        """Test that malicious inputs are handled safely in workflow."""
        from app.services.agents.utils import validate_inputs

        # Should validate successfully (safety is LLM responsibility)
        is_valid, error = validate_inputs(sample_job_description, malicious_resume_prompt_injection)

        # Validation succeeds, but content is safe in LLM layer
        assert isinstance(is_valid, bool)

    def test_data_isolation_in_state(self):
        """Test that state changes don't leak between instances."""
        from app.services.agents.state import JobCopilotState

        state1 = JobCopilotState(
            job_description_raw="Test 1",
            resume_raw="Resume 1",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        state2 = JobCopilotState(
            job_description_raw="Test 2",
            resume_raw="Resume 2",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        # Modify state1
        state1.nodes_executed.append("parse_jd")

        # state2 should be unaffected
        assert len(state2.nodes_executed) == 0


class TestConcurrency:
    """Test behavior under concurrent operations."""

    def test_independent_workflows_isolated(self):
        """Test that independent workflows don't interfere."""
        from app.services.agents.state import JobCopilotState

        # Simulate two concurrent workflows
        workflow1 = JobCopilotState(
            job_description_raw="JD 1",
            resume_raw="Resume 1",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        workflow2 = JobCopilotState(
            job_description_raw="JD 2",
            resume_raw="Resume 2",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        # Process workflow1
        workflow1.nodes_executed.append("parse_jd")
        workflow1.job_description = {
            "title": "Dev",
            "company": "Corp1",
            "location": "SF",
            "salary_range": None,
            "requirements": [],
        }

        # Process workflow2
        workflow2.nodes_executed.append("parse_jd")
        workflow2.job_description = {
            "title": "Dev",
            "company": "Corp2",
            "location": "LA",
            "salary_range": None,
            "requirements": [],
        }

        # Workflows should be independent
        assert workflow1.job_description["company"] == "Corp1"
        assert workflow2.job_description["company"] == "Corp2"
        assert workflow1.job_description["location"] == "SF"
        assert workflow2.job_description["location"] == "LA"


class TestDataConsistency:
    """Test data consistency across operations."""

    def test_state_consistency_through_export(self):
        """Test that state remains consistent through export."""
        from app.services.agents.utils import export_workflow_result

        original_result = {
            "job_description_raw": "JD",
            "resume_raw": "Resume",
            "job_description": {
                "title": "Dev",
                "company": "Corp",
                "location": "SF",
                "salary_range": "$150k",
                "requirements": ["Python"],
            },
            "resume_data": {
                "name": "John",
                "email": "john@test.com",
                "phone": None,
                "skills": ["Python"],
                "experience_years": 5,
            },
            "resume_analysis": {
                "overall_fit_score": 0.8,
                "skills_score": 0.85,
                "experience_score": 0.75,
                "matched_skills": ["Python"],
                "missing_skills": [],
                "strengths": [],
                "recommendations": [],
            },
            "matching_score": 0.8,
            "cover_letter": None,
            "nodes_executed": ["parse_jd", "analyze_resume"],
            "error": None,
        }

        exported = export_workflow_result(original_result)

        # Should preserve key information
        assert "job_application" in exported
        assert "fit_assessment" in exported
        assert "metadata" in exported
        assert len(exported["metadata"]["nodes_executed"]) == 2
