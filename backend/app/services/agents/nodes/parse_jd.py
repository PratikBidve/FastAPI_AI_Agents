"""
Job Description Parser Node
Extracts and structures information from raw job description text.
"""

import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..llm import get_llm
from ..state import JobDescription

logger = logging.getLogger(__name__)


class ParsedJobDescription(BaseModel):
    """Pydantic model for parsed job description output."""
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    description: str = Field(description="Full job description")
    requirements: list[str] = Field(description="List of required skills/qualifications")
    nice_to_have: list[str] = Field(description="List of nice-to-have skills")
    salary_range: str | None = Field(description="Salary range if mentioned")
    location: str | None = Field(description="Job location")
    seniority_level: str | None = Field(description="Experience level required")
    employment_type: str | None = Field(description="Full-time, contract, etc.")


JOB_DESCRIPTION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert job description analyzer. Extract and structure the following job description.
Be thorough in identifying all requirements and separating them from nice-to-have skills.

Job Description:
{job_description_raw}

Extract the following information:
1. Job Title
2. Company Name
3. Full Description
4. Required Skills/Qualifications (list each separately)
5. Nice-to-Have Skills (list each separately)
6. Salary Range (if mentioned)
7. Location
8. Seniority Level
9. Employment Type

Provide the output as a valid JSON object matching this structure:
{{
    "title": "...",
    "company": "...",
    "description": "...",
    "requirements": [...],
    "nice_to_have": [...],
    "salary_range": "...",
    "location": "...",
    "seniority_level": "...",
    "employment_type": "..."
}}

Important: Requirements and nice_to_have should be lists of individual items, not comma-separated strings.
""")


async def parse_job_description(state: dict[str, object]) -> dict[str, object]:
    """
    Parse and structure job description.

    Args:
        state: Current workflow state

    Returns:
        Updated state with parsed job description
    """
    try:
        job_description_raw = state.get("job_description_raw", "")

        if not job_description_raw:
            state["error"] = "No job description provided"
            logger.warning("parse_job_description: Empty job description")
            return state

        # Initialize LLM and parser
        llm = get_llm()
        parser = JsonOutputParser(pydantic_object=ParsedJobDescription)

        # Create chain
        chain = JOB_DESCRIPTION_PROMPT | llm | parser

        # Parse job description
        logger.info("Parsing job description...")
        parsed_result = await chain.ainvoke({
            "job_description_raw": job_description_raw
        })

        # Convert to JobDescription TypedDict
        job_description: JobDescription = {
            "title": parsed_result.get("title", ""),
            "company": parsed_result.get("company", ""),
            "description": parsed_result.get("description", ""),
            "requirements": parsed_result.get("requirements", []),
            "nice_to_have": parsed_result.get("nice_to_have", []),
            "salary_range": parsed_result.get("salary_range"),
            "location": parsed_result.get("location"),
            "raw_text": job_description_raw,
        }

        state["job_description"] = job_description
        state["nodes_executed"] = state.get("nodes_executed", []) + ["parse_job_description"]

        logger.info(f"Successfully parsed job description: {job_description['title']} at {job_description['company']}")

    except Exception as e:
        error_msg = f"Error parsing job description: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["error"] = error_msg

    return state
