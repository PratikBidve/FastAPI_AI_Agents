"""
Cover Letter Generation Node
Generates a tailored cover letter based on job description and resume analysis.
"""

import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..llm import get_llm
from ..state import CoverLetterData

logger = logging.getLogger(__name__)


class CoverLetterOutput(BaseModel):
    """Pydantic model for cover letter generation output."""
    content: str = Field(description="Full cover letter content")
    tone: str = Field(description="Tone of the letter")
    highlighted_skills: list = Field(description="Key skills highlighted in the letter")
    key_achievements: list = Field(description="Achievements emphasized in the letter")


COVER_LETTER_PROMPT = ChatPromptTemplate.from_template("""
You are an expert cover letter writer and career coach. Generate a compelling,
personalized cover letter based on the following information.

Candidate Information (from resume):
{resume_raw}

Job Description:
Position: {job_title}
Company: {company}
Description: {job_description}
Requirements: {requirements}

Resume Analysis:
- Matched Skills: {matched_skills}
- Missing Skills: {missing_skills}
- Key Strengths: {strengths}
- Overall Fit Score: {overall_fit_score}%

Generate a professional cover letter that:
1. Opens with a compelling hook showing genuine interest in the role
2. Highlights 3-4 key matched skills with specific examples
3. Addresses any skill gaps strategically (if any)
4. Demonstrates knowledge of the company
5. Includes quantifiable achievements and metrics
6. Shows cultural fit and enthusiasm
7. Ends with a strong call to action

Format the output as JSON:
{{
    "content": "Dear Hiring Manager,\\n\\n...[full letter]...\\n\\nBest regards",
    "tone": "professional",
    "highlighted_skills": ["skill1", "skill2", ...],
    "key_achievements": ["achievement1", "achievement2", ...]
}}

The letter should be 3-4 paragraphs, well-structured, and ready to use.
Keep it to around 250-300 words.
""")


async def generate_cover_letter(state: dict[str, object]) -> dict[str, object]:
    """
    Generate a tailored cover letter.

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated cover letter
    """
    try:
        # Check prerequisites
        job_description = state.get("job_description")
        resume_raw = state.get("resume_raw", "")
        resume_analysis = state.get("resume_analysis")

        if not job_description:
            state["error"] = "Job description must be parsed first"
            logger.warning("generate_cover_letter: Missing job description")
            return state

        if not resume_raw:
            state["error"] = "No resume provided"
            logger.warning("generate_cover_letter: Empty resume")
            return state

        if not resume_analysis:
            state["error"] = "Resume analysis must be completed first"
            logger.warning("generate_cover_letter: Missing resume analysis")
            return state

        # Initialize LLM and parser
        llm = get_llm()
        parser = JsonOutputParser(pydantic_object=CoverLetterOutput)

        # Create chain
        chain = COVER_LETTER_PROMPT | llm | parser

        # Generate cover letter
        logger.info("Generating tailored cover letter...")
        cover_letter_result = await chain.ainvoke({
            "resume_raw": resume_raw,
            "job_title": job_description.get("title", ""),
            "company": job_description.get("company", ""),
            "job_description": job_description.get("description", ""),
            "requirements": ", ".join(job_description.get("requirements", [])),
            "matched_skills": ", ".join(resume_analysis.get("matched_skills", [])),
            "missing_skills": ", ".join(resume_analysis.get("missing_skills", [])),
            "strengths": ", ".join(resume_analysis.get("strengths", [])),
            "overall_fit_score": int(resume_analysis.get("overall_fit_score", 0) * 100),
        })

        # Convert to CoverLetterData TypedDict
        cover_letter: CoverLetterData = {
            "content": cover_letter_result.get("content", ""),
            "tone": cover_letter_result.get("tone", "professional"),
            "highlighted_skills": cover_letter_result.get("highlighted_skills", []),
            "key_achievements": cover_letter_result.get("key_achievements", []),
        }

        state["cover_letter"] = cover_letter
        state["nodes_executed"] = state.get("nodes_executed", []) + ["generate_cover_letter"]

        logger.info(
            f"Cover letter generated successfully. "
            f"Highlighted skills: {len(cover_letter['highlighted_skills'])}, "
            f"Key achievements: {len(cover_letter['key_achievements'])}"
        )

    except Exception as e:
        error_msg = f"Error generating cover letter: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["error"] = error_msg

    return state
