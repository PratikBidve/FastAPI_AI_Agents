"""Tests for Job Copilot workflow nodes."""

from app.services.agents.nodes.analyze_resume import ResumeAnalysis
from app.services.agents.nodes.generate_cover_letter import CoverLetterOutput
from app.services.agents.nodes.parse_jd import ParsedJobDescription


class TestParseJDNode:
    """Test job description parsing node."""

    def test_parsed_job_description_structure(self):
        """Test ParsedJobDescription structure."""
        parsed = ParsedJobDescription(
            title="Senior Backend Engineer",
            company="TechCorp",
            location="San Francisco",
            salary_range="$150k-200k",
            requirements=["Python", "FastAPI", "PostgreSQL"],
        )

        assert parsed["title"] == "Senior Backend Engineer"
        assert parsed["company"] == "TechCorp"
        assert parsed["location"] == "San Francisco"
        assert len(parsed["requirements"]) == 3

    def test_parsed_job_description_with_no_salary(self):
        """Test ParsedJobDescription without salary range."""
        parsed = ParsedJobDescription(
            title="Developer",
            company="Company",
            location="Remote",
            salary_range=None,
            requirements=["Python"],
        )

        assert parsed["title"] == "Developer"
        assert parsed["salary_range"] is None
        assert parsed["location"] == "Remote"

    def test_parsed_job_description_with_no_location(self):
        """Test ParsedJobDescription without location."""
        parsed = ParsedJobDescription(
            title="Developer",
            company="Company",
            location=None,
            salary_range="$100k",
            requirements=["Python"],
        )

        assert parsed["company"] == "Company"
        assert parsed["location"] is None
        assert parsed["salary_range"] == "$100k"

    def test_parsed_job_description_with_many_requirements(self):
        """Test ParsedJobDescription with many requirements."""
        requirements = [
            "Python", "FastAPI", "PostgreSQL", "Redis", "Docker",
            "Kubernetes", "AWS", "Git", "REST APIs", "async/await",
        ]

        parsed = ParsedJobDescription(
            title="Senior Engineer",
            company="Company",
            location="SF",
            salary_range="$150k+",
            requirements=requirements,
        )

        assert len(parsed["requirements"]) == 10
        assert "Python" in parsed["requirements"]
        assert "Kubernetes" in parsed["requirements"]

    def test_parsed_job_description_empty_requirements(self):
        """Test ParsedJobDescription with empty requirements."""
        parsed = ParsedJobDescription(
            title="Developer",
            company="Company",
            location="Remote",
            salary_range=None,
            requirements=[],
        )

        assert parsed["requirements"] == []


class TestResumeAnalysisNode:
    """Test resume analysis node."""

    def test_resume_analysis_structure(self):
        """Test ResumeAnalysis structure."""
        analysis = ResumeAnalysis(
            overall_fit_score=0.85,
            skills_score=0.9,
            experience_score=0.8,
            matched_skills=["Python", "FastAPI"],
            missing_skills=["Kubernetes"],
            strengths=["Strong architecture knowledge", "Team lead experience"],
            recommendations=["Learn Kubernetes", "Improve DevOps"],
        )

        assert analysis["overall_fit_score"] == 0.85
        assert analysis["skills_score"] == 0.9
        assert analysis["experience_score"] == 0.8
        assert len(analysis["matched_skills"]) == 2
        assert len(analysis["missing_skills"]) == 1

    def test_resume_analysis_perfect_match(self):
        """Test ResumeAnalysis for perfect match."""
        analysis = ResumeAnalysis(
            overall_fit_score=1.0,
            skills_score=1.0,
            experience_score=1.0,
            matched_skills=["Python", "FastAPI", "PostgreSQL"],
            missing_skills=[],
            strengths=["Perfect match", "Excellent experience"],
            recommendations=[],
        )

        assert analysis["overall_fit_score"] == 1.0
        assert len(analysis["missing_skills"]) == 0
        assert len(analysis["recommendations"]) == 0

    def test_resume_analysis_poor_match(self):
        """Test ResumeAnalysis for poor match."""
        analysis = ResumeAnalysis(
            overall_fit_score=0.2,
            skills_score=0.1,
            experience_score=0.3,
            matched_skills=["Basic Python"],
            missing_skills=["FastAPI", "PostgreSQL", "Redis", "Docker"],
            strengths=[],
            recommendations=["Major upskilling needed", "Consider junior roles"],
        )

        assert analysis["overall_fit_score"] == 0.2
        assert analysis["skills_score"] == 0.1
        assert len(analysis["missing_skills"]) == 4

    def test_resume_analysis_scores_in_valid_range(self):
        """Test that analysis scores are in valid range."""
        analysis = ResumeAnalysis(
            overall_fit_score=0.75,
            skills_score=0.8,
            experience_score=0.7,
            matched_skills=["Python"],
            missing_skills=[],
            strengths=["Good skills"],
            recommendations=[],
        )

        assert 0 <= analysis["overall_fit_score"] <= 1
        assert 0 <= analysis["skills_score"] <= 1
        assert 0 <= analysis["experience_score"] <= 1


class TestCoverLetterNode:
    """Test cover letter generation node."""

    def test_cover_letter_output_structure(self):
        """Test CoverLetterOutput structure."""
        letter = CoverLetterOutput(
            tone="professional",
            content="Dear Hiring Manager...",
            highlighted_skills=["Python", "Leadership"],
            key_achievements=["Led team of 5", "Reduced latency by 60%"],
        )

        assert letter["tone"] == "professional"
        assert "Dear Hiring Manager" in letter["content"]
        assert len(letter["highlighted_skills"]) == 2
        assert len(letter["key_achievements"]) == 2

    def test_cover_letter_formal_tone(self):
        """Test cover letter with formal tone."""
        letter = CoverLetterOutput(
            tone="formal",
            content="To the Hiring Manager...",
            highlighted_skills=["Professional skills"],
            key_achievements=[],
        )

        assert letter["tone"] == "formal"
        assert "Hiring Manager" in letter["content"]

    def test_cover_letter_casual_tone(self):
        """Test cover letter with casual tone."""
        letter = CoverLetterOutput(
            tone="casual",
            content="Hi there...",
            highlighted_skills=["Communication"],
            key_achievements=["Great team fit"],
        )

        assert letter["tone"] == "casual"
        assert "Hi there" in letter["content"]

    def test_cover_letter_empty_content(self):
        """Test cover letter with empty content (edge case)."""
        letter = CoverLetterOutput(
            tone="professional",
            content="",
            highlighted_skills=[],
            key_achievements=[],
        )

        assert letter["tone"] == "professional"
        assert letter["content"] == ""
        assert letter["highlighted_skills"] == []

    def test_cover_letter_long_content(self):
        """Test cover letter with long content."""
        long_content = "Dear Hiring Manager, " * 100

        letter = CoverLetterOutput(
            tone="professional",
            content=long_content,
            highlighted_skills=["Python", "Leadership", "Communication"],
            key_achievements=["Achievement 1", "Achievement 2", "Achievement 3"],
        )

        assert len(letter["content"]) > 1000
        assert len(letter["highlighted_skills"]) == 3
        assert len(letter["key_achievements"]) == 3


class TestNodeDataTypes:
    """Test node data type validation."""

    def test_score_values_valid_range(self):
        """Test that score values are validated."""
        # Test minimum
        analysis = ResumeAnalysis(
            overall_fit_score=0,
            skills_score=0,
            experience_score=0,
            matched_skills=[],
            missing_skills=[],
            strengths=[],
            recommendations=[],
        )
        assert analysis["overall_fit_score"] == 0

        # Test maximum
        analysis = ResumeAnalysis(
            overall_fit_score=1.0,
            skills_score=1.0,
            experience_score=1.0,
            matched_skills=[],
            missing_skills=[],
            strengths=[],
            recommendations=[],
        )
        assert analysis["overall_fit_score"] == 1.0

    def test_list_fields_accept_lists(self):
        """Test that list fields properly handle lists."""
        analysis = ResumeAnalysis(
            overall_fit_score=0.5,
            skills_score=0.5,
            experience_score=0.5,
            matched_skills=["Skill1", "Skill2", "Skill3"],
            missing_skills=["Missing1"],
            strengths=["Strength1"],
            recommendations=["Rec1", "Rec2"],
        )

        assert isinstance(analysis["matched_skills"], list)
        assert isinstance(analysis["missing_skills"], list)
        assert isinstance(analysis["strengths"], list)
        assert isinstance(analysis["recommendations"], list)
        assert len(analysis["matched_skills"]) == 3
        assert len(analysis["missing_skills"]) == 1

    def test_string_fields_accept_strings(self):
        """Test that string fields properly handle strings."""
        parsed = ParsedJobDescription(
            title="Job Title",
            company="Company Name",
            location="Location",
            salary_range="$100k-150k",
            requirements=["Requirement"],
        )

        assert isinstance(parsed["title"], str)
        assert isinstance(parsed["company"], str)
        assert isinstance(parsed["location"], str)
        assert isinstance(parsed["salary_range"], str)
