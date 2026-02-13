"""
Resume Analysis Node
Analyzes resume against job description and identifies matching skills and gaps.
"""

import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..llm import get_llm

logger = logging.getLogger(__name__)


class ResumeAnalysis(BaseModel):
    """Pydantic model for resume analysis output."""
    matched_skills: list[str] = Field(description="Skills that match job requirements")
    missing_skills: list[str] = Field(description="Required skills not present in resume")
    nice_to_have_matches: list[str] = Field(description="Nice-to-have skills present in resume")
    experience_match: str = Field(description="How well experience aligns with job")
    experience_score: float = Field(ge=0.0, le=1.0, description="Match score for experience")
    skills_score: float = Field(ge=0.0, le=1.0, description="Match score for skills")
    overall_fit_score: float = Field(ge=0.0, le=1.0, description="Overall fit percentage")
    strengths: list[str] = Field(description="Key strengths for this position")
    weaknesses: list[str] = Field(description="Areas to address in cover letter")
    recommendations: list[str] = Field(description="Recommendations for application")


RESUME_ANALYSIS_PROMPT = ChatPromptTemplate.from_template("""
You are an expert recruiter and resume analyst. Analyze the following resume against the job description.

Job Description:
Title: {job_title}
Company: {company}
Requirements: {requirements}
Nice to Have: {nice_to_have}

Resume:
{resume_raw}

Provide a detailed analysis including:
1. Skills from the resume that match the job requirements
2. Required skills that are missing from the resume
3. Nice-to-have skills present in the resume
4. How well the candidate's experience aligns with the role
5. Match scores for experience (0-1), skills (0-1), and overall fit (0-1)
6. Key strengths that should be highlighted in a cover letter
7. Weaknesses or gaps to address
8. Strategic recommendations for the application

Provide the output as a valid JSON object:
{{
    "matched_skills": [...],
    "missing_skills": [...],
    "nice_to_have_matches": [...],
    "experience_match": "...",
    "experience_score": 0.8,
    "skills_score": 0.75,
    "overall_fit_score": 0.78,
    "strengths": [...],
    "weaknesses": [...],
    "recommendations": [...]
}}

Be realistic and constructive in your analysis. Scores should reflect actual alignment.
""")


async def analyze_resume(state: dict[str, object]) -> dict[str, object]:
    """
    Analyze resume against job description.

    Args:
        state: Current workflow state

    Returns:
        Updated state with resume analysis
    """
    try:
        # Check prerequisites
        job_description = state.get("job_description")
        resume_raw = state.get("resume_raw", "")

        if not job_description:
            state["error"] = "Job description must be parsed first"
            logger.warning("analyze_resume: Missing job description")
            return state

        if not resume_raw:
            state["error"] = "No resume provided"
            logger.warning("analyze_resume: Empty resume")
            return state

        # Initialize LLM and parser
        llm = get_llm()
        parser = JsonOutputParser(pydantic_object=ResumeAnalysis)

        # Create chain
        chain = RESUME_ANALYSIS_PROMPT | llm | parser

        # Perform analysis
        logger.info("Analyzing resume against job description...")
        analysis_result = await chain.ainvoke({
            "job_title": job_description.get("title", ""),
            "company": job_description.get("company", ""),
            "requirements": ", ".join(job_description.get("requirements", [])),
            "nice_to_have": ", ".join(job_description.get("nice_to_have", [])),
            "resume_raw": resume_raw,
        })

        # Update state
        state["resume_analysis"] = analysis_result
        state["skill_gaps"] = analysis_result.get("missing_skills", [])
        state["matching_score"] = analysis_result.get("overall_fit_score", 0.0)
        state["nodes_executed"] = state.get("nodes_executed", []) + ["analyze_resume"]

        logger.info(
            f"Resume analysis complete. Overall fit: {state['matching_score']:.1%}. "
            f"Matched skills: {len(analysis_result.get('matched_skills', []))}, "
            f"Missing skills: {len(analysis_result.get('missing_skills', []))}"
        )

    except Exception as e:
        error_msg = f"Error analyzing resume: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["error"] = error_msg

    return state
