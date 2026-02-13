"""
Utility functions for the Job Copilot agent system.
"""

from datetime import datetime


def format_cover_letter_for_display(cover_letter: dict[str, object]) -> str:
    """
    Format cover letter for display/export.

    Args:
        cover_letter: Cover letter data dictionary

    Returns:
        Formatted cover letter text
    """
    if not cover_letter or not cover_letter.get("content"):
        return ""

    return cover_letter["content"]


def export_workflow_result(result: dict[str, object]) -> dict[str, object]:
    """
    Export workflow results in a clean, serializable format.

    Args:
        result: Complete workflow state

    Returns:
        Cleaned export-ready dictionary
    """
    return {
        "job_description": {
            "title": result.get("job_description", {}).get("title"),
            "company": result.get("job_description", {}).get("company"),
            "location": result.get("job_description", {}).get("location"),
            "salary_range": result.get("job_description", {}).get("salary_range"),
            "requirements_count": len(result.get("job_description", {}).get("requirements", [])),
        },
        "analysis": {
            "overall_fit_score": result.get("matching_score"),
            "matched_skills_count": len(result.get("resume_analysis", {}).get("matched_skills", [])),
            "missing_skills_count": len(result.get("resume_analysis", {}).get("missing_skills", [])),
            "experience_score": result.get("resume_analysis", {}).get("experience_score"),
            "skills_score": result.get("resume_analysis", {}).get("skills_score"),
        },
        "cover_letter": {
            "content": result.get("cover_letter", {}).get("content"),
            "tone": result.get("cover_letter", {}).get("tone"),
            "highlighted_skills_count": len(result.get("cover_letter", {}).get("highlighted_skills", [])),
        },
        "metadata": {
            "nodes_executed": result.get("nodes_executed", []),
            "error": result.get("error"),
        }
    }


def get_summary(result: dict[str, object]) -> dict[str, object]:
    """
    Generate a summary of workflow execution.

    Args:
        result: Complete workflow state

    Returns:
        Summary dictionary
    """
    analysis = result.get("resume_analysis", {})

    return {
        "job": {
            "title": result.get("job_description", {}).get("title"),
            "company": result.get("job_description", {}).get("company"),
        },
        "fit_assessment": {
            "overall_score": f"{result.get('matching_score', 0):.1%}",
            "skills_alignment": f"{analysis.get('skills_score', 0):.1%}",
            "experience_alignment": f"{analysis.get('experience_score', 0):.1%}",
        },
        "matched_skills": analysis.get("matched_skills", []),
        "missing_skills": analysis.get("missing_skills", []),
        "key_strengths": analysis.get("strengths", [])[:3],
        "recommendations": analysis.get("recommendations", [])[:3],
        "cover_letter_ready": bool(result.get("cover_letter")),
    }


def validate_inputs(job_description: str, resume: str) -> tuple[bool, str | None]:
    """
    Validate workflow inputs.

    Args:
        job_description: Job description text
        resume: Resume text

    Returns:
        Tuple of (is_valid, error_message)
    """
    min_length = 50

    if not job_description:
        return False, "Job description is required"

    if not resume:
        return False, "Resume is required"

    if len(job_description) < min_length:
        return False, f"Job description must be at least {min_length} characters"

    if len(resume) < min_length:
        return False, f"Resume must be at least {min_length} characters"

    return True, None


def format_for_json(obj: object) -> object:
    """
    Recursively format objects for JSON serialization.

    Args:
        obj: Object to format

    Returns:
        JSON-serializable object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: format_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [format_for_json(item) for item in obj]
    else:
        return obj


def merge_results(result1: dict[str, object], result2: dict[str, object]) -> dict[str, object]:
    """
    Merge two workflow results (for batch processing).

    Args:
        result1: First workflow result
        result2: Second workflow result

    Returns:
        Merged results
    """
    merged = result1.copy()

    # Extend nodes_executed
    merged["nodes_executed"] = list(
        set(result1.get("nodes_executed", []) + result2.get("nodes_executed", []))
    )

    # Keep first result as primary, note alternate
    if result2.get("error") and not result1.get("error"):
        merged["alternate_error"] = result2["error"]

    return merged
