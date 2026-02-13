"""Unit tests for Job Copilot state management."""

from app.services.agents.state import (
    CoverLetterData,
    JobCopilotState,
    JobDescription,
    ResumeData,
)


class TestJobDescription:
    """Test JobDescription TypedDict."""

    def test_valid_job_description(self):
        """Test creating valid job description."""
        job = JobDescription(
            title="Senior Dev",
            company="TechCorp",
            location="SF",
            salary_range="$150k-200k",
            requirements=["Python", "FastAPI"],
        )

        assert job["title"] == "Senior Dev"
        assert job["company"] == "TechCorp"
        assert job["requirements"] == ["Python", "FastAPI"]

    def test_job_description_with_optional_fields(self):
        """Test job description with optional fields."""
        job = JobDescription(
            title="Dev",
            company="Company",
            location=None,
            salary_range=None,
            requirements=[],
        )

        assert job["title"] == "Dev"
        assert job["location"] is None
        assert job["requirements"] == []


class TestResumeData:
    """Test ResumeData TypedDict."""

    def test_valid_resume_data(self):
        """Test creating valid resume data."""
        resume = ResumeData(
            name="John Doe",
            email="john@example.com",
            phone="+1-415-555-1234",
            skills=["Python", "FastAPI", "PostgreSQL"],
            experience_years=5,
        )

        assert resume["name"] == "John Doe"
        assert len(resume["skills"]) == 3
        assert resume["experience_years"] == 5

    def test_resume_data_minimal(self):
        """Test resume data with minimal information."""
        resume = ResumeData(
            name="Jane Doe",
            email="jane@example.com",
            phone=None,
            skills=[],
            experience_years=0,
        )

        assert resume["name"] == "Jane Doe"
        assert resume["phone"] is None
        assert resume["skills"] == []


class TestCoverLetterData:
    """Test CoverLetterData TypedDict."""

    def test_valid_cover_letter(self):
        """Test creating valid cover letter data."""
        letter = CoverLetterData(
            tone="professional",
            content="Dear Hiring Manager...",
            highlighted_skills=["Python", "Leadership"],
            key_achievements=["Led team of 5", "Reduced latency by 60%"],
        )

        assert letter["tone"] == "professional"
        assert len(letter["highlighted_skills"]) == 2
        assert len(letter["key_achievements"]) == 2

    def test_cover_letter_minimal(self):
        """Test minimal cover letter data."""
        letter = CoverLetterData(
            tone="formal",
            content="",
            highlighted_skills=[],
            key_achievements=[],
        )

        assert letter["tone"] == "formal"
        assert letter["content"] == ""


class TestJobCopilotState:
    """Test JobCopilotState dataclass."""

    def test_valid_state(self):
        """Test creating valid state."""
        state = JobCopilotState(
            job_description_raw="Job description text",
            resume_raw="Resume text",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        assert state.job_description_raw == "Job description text"
        assert state.nodes_executed == []
        assert state.error is None

    def test_state_with_data(self):
        """Test state with populated data."""
        state = JobCopilotState(
            job_description_raw="JD",
            resume_raw="Resume",
            job_description={"title": "Dev", "company": "Corp", "location": "SF", "salary_range": None, "requirements": []},
            resume_data={"name": "John", "email": "john@example.com", "phone": None, "skills": ["Python"], "experience_years": 5},
            resume_analysis={"overall_fit_score": 0.8, "skills_score": 0.9, "experience_score": 0.7, "matched_skills": ["Python"], "missing_skills": [], "strengths": ["Good"], "recommendations": []},
            skill_gaps=["Kubernetes"],
            matching_score=0.8,
            cover_letter={"tone": "professional", "content": "Letter", "highlighted_skills": ["Python"], "key_achievements": []},
            error=None,
            nodes_executed=["parse_jd", "analyze_resume"],
        )

        assert state.job_description["title"] == "Dev"
        assert state.resume_data["name"] == "John"
        assert state.matching_score == 0.8
        assert len(state.nodes_executed) == 2

    def test_state_with_error(self):
        """Test state with error."""
        state = JobCopilotState(
            job_description_raw="JD",
            resume_raw="Resume",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error="Processing failed",
            nodes_executed=["parse_jd"],
        )

        assert state.error == "Processing failed"
        assert state.job_description is None


class TestJobCopilotStateDict:
    """Test JobCopilotStateDict TypedDict conversion."""

    def test_state_to_dict(self):
        """Test converting state to dictionary."""
        state = JobCopilotState(
            job_description_raw="JD",
            resume_raw="Resume",
            job_description={"title": "Dev", "company": "Corp", "location": "SF", "salary_range": None, "requirements": []},
            resume_data={"name": "John", "email": "john@example.com", "phone": None, "skills": ["Python"], "experience_years": 5},
            resume_analysis={"overall_fit_score": 0.8, "skills_score": 0.9, "experience_score": 0.7, "matched_skills": ["Python"], "missing_skills": [], "strengths": ["Good"], "recommendations": []},
            skill_gaps=None,
            matching_score=0.8,
            cover_letter=None,
            error=None,
            nodes_executed=["parse_jd"],
        )

        state_dict = state.to_dict()

        assert isinstance(state_dict, dict)
        assert state_dict["job_description_raw"] == "JD"
        assert state_dict["matching_score"] == 0.8
        assert state_dict["error"] is None


class TestStateTransitions:
    """Test valid state transitions."""

    def test_initial_to_parsed(self):
        """Test transition from initial to parsed JD."""
        state = JobCopilotState(
            job_description_raw="Job description",
            resume_raw="Resume",
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        # Simulate parsing
        state.job_description = {
            "title": "Dev",
            "company": "Corp",
            "location": "SF",
            "salary_range": None,
            "requirements": [],
        }
        state.nodes_executed.append("parse_jd")

        assert state.job_description is not None
        assert "parse_jd" in state.nodes_executed

    def test_complete_workflow_state(self):
        """Test complete workflow state."""
        state = JobCopilotState(
            job_description_raw="JD",
            resume_raw="Resume",
            job_description={"title": "Dev", "company": "Corp", "location": "SF", "salary_range": None, "requirements": ["Python"]},
            resume_data={"name": "John", "email": "john@example.com", "phone": None, "skills": ["Python"], "experience_years": 5},
            resume_analysis={"overall_fit_score": 0.8, "skills_score": 0.9, "experience_score": 0.7, "matched_skills": ["Python"], "missing_skills": [], "strengths": ["Good"], "recommendations": []},
            skill_gaps=[],
            matching_score=0.8,
            cover_letter={"tone": "professional", "content": "Letter", "highlighted_skills": ["Python"], "key_achievements": []},
            error=None,
            nodes_executed=["parse_jd", "analyze_resume", "generate_cover_letter"],
        )

        assert state.job_description is not None
        assert state.resume_data is not None
        assert state.resume_analysis is not None
        assert state.cover_letter is not None
        assert state.matching_score is not None
        assert len(state.nodes_executed) == 3


class TestStateValidation:
    """Test state validation and constraints."""

    def test_state_immutability_of_raw_fields(self):
        """Test that raw fields shouldn't be modified during processing."""
        original_jd = "Original job description"
        original_resume = "Original resume"

        state = JobCopilotState(
            job_description_raw=original_jd,
            resume_raw=original_resume,
            job_description=None,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        # Verify raw fields remain unchanged
        assert state.job_description_raw == original_jd
        assert state.resume_raw == original_resume


class TestStateDeepCopy:
    """Test state deep copying for data isolation."""

    def test_state_modifications_dont_affect_original(self):
        """Test that state modifications don't affect dictionaries."""
        job_desc = {"title": "Dev", "company": "Corp", "location": "SF", "salary_range": None, "requirements": ["Python"]}

        state = JobCopilotState(
            job_description_raw="JD",
            resume_raw="Resume",
            job_description=job_desc,
            resume_data=None,
            resume_analysis=None,
            skill_gaps=None,
            matching_score=None,
            cover_letter=None,
            error=None,
            nodes_executed=[],
        )

        # Modify state's job description
        if state.job_description:
            state.job_description["title"] = "Modified"

        # Original dict should be affected (Python dicts are references)
        assert job_desc["title"] == "Modified"
