"""
State schema for the Job Copilot agent workflow.
Defines the shared state that flows through all agent nodes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict


class JobDescription(TypedDict):
    """Structured job description data."""
    title: str
    company: str
    description: str
    requirements: list[str]
    nice_to_have: list[str]
    salary_range: str | None
    location: str | None
    raw_text: str


class ResumeData(TypedDict):
    """Structured resume data."""
    name: str
    email: str
    phone: str | None
    experience: list[dict[str, object]]
    skills: list[str]
    education: list[dict[str, object]]
    projects: list[dict[str, object]]
    raw_text: str


class CoverLetterData(TypedDict):
    """Generated cover letter structure."""
    content: str
    tone: str
    highlighted_skills: list[str]
    key_achievements: list[str]


@dataclass
class JobCopilotState:
    """
    Main state for the Job Copilot agentic workflow.
    Flows through all nodes and accumulates results.
    """

    # Input documents
    job_description_raw: str = ""
    resume_raw: str = ""

    # Parsed data
    job_description: JobDescription | None = None
    resume_data: ResumeData | None = None

    # Analysis results
    resume_analysis: dict[str, object] | None = None
    skill_gaps: list[str] | None = None
    matching_score: float | None = None

    # Generated output
    cover_letter: CoverLetterData | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error: str | None = None

    # Node execution tracking
    nodes_executed: list[str] = field(default_factory=list)
    def add_node_execution(self, node_name: str) -> None:
        """Track which nodes have been executed."""
        self.nodes_executed.append(node_name)
        self.update_timestamp()

    def to_dict(self) -> dict[str, object]:
        """Convert state to dictionary for serialization."""
        return {
            "job_description_raw": self.job_description_raw,
            "resume_raw": self.resume_raw,
            "job_description": self.job_description,
            "resume_data": self.resume_data,
            "resume_analysis": self.resume_analysis,
            "skill_gaps": self.skill_gaps,
            "matching_score": self.matching_score,
            "cover_letter": self.cover_letter,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
            "nodes_executed": self.nodes_executed,
        }


# TypedDict version for langgraph compatibility
class JobCopilotStateDict(TypedDict, total=False):
    """TypedDict version of JobCopilotState for langgraph."""
    job_description_raw: str
    resume_raw: str
    job_description: JobDescription | None
    resume_data: ResumeData | None
    resume_analysis: dict[str, object] | None
    skill_gaps: list[str] | None
    matching_score: float | None
    cover_letter: CoverLetterData | None
    error: str | None
    nodes_executed: list[str]
