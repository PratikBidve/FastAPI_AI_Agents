"""
FastAPI integration for Job Copilot agent system.
Example API endpoints for the agentic workflow.

Integration into FastAPI app:
1. Import this module in your main.py or routes
2. Include the router in your FastAPI app
3. Ensure OPENAI_API_KEY is set in environment
"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.services.agents import get_job_copilot_graph, init_llm
from app.services.agents.utils import get_summary, validate_inputs

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/job-copilot", tags=["Job Copilot"])


class JobApplicationRequest(BaseModel):
    """Request model for job application analysis."""
    job_description: str = Field(..., min_length=50, description="Job posting text")
    resume: str = Field(..., min_length=50, description="Resume text")
    user_id: str | None = Field(None, description="User identifier")


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""
    success: bool
    matching_score: float | None = None
    job_title: str | None = None
    company: str | None = None
    cover_letter: str | None = None
    analysis_summary: dict[str, object] | None = None
    error: str | None = None
    execution_nodes: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    llm_initialized: bool
    graph_initialized: bool


@router.on_event("startup")
async def startup_event():
    """Initialize LLM on application startup."""
    try:
        init_llm()
        logger.info("Job Copilot LLM initialized on startup")
    except Exception as e:
        logger.error(f"Failed to initialize LLM on startup: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for Job Copilot system.

    Returns:
        HealthResponse with system status
    """
    try:
        graph = get_job_copilot_graph()
        return HealthResponse(
            status="healthy",
            llm_initialized=True,
            graph_initialized=bool(graph),
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            llm_initialized=False,
            graph_initialized=False,
        )


@router.post("/analyze", response_model=WorkflowExecutionResponse)
async def analyze_job_application(request: JobApplicationRequest) -> WorkflowExecutionResponse:
    """
    Analyze a job posting and resume, generate a tailored cover letter.

    This is the main endpoint for the Job Copilot workflow.

    Args:
        request: Request containing job description and resume

    Returns:
        WorkflowExecutionResponse with analysis results

    Raises:
        HTTPException: If validation fails or workflow execution fails
    """
    try:
        # Validate inputs
        is_valid, error = validate_inputs(request.job_description, request.resume)
        if not is_valid:
            logger.warning(f"Validation failed: {error}")
            raise HTTPException(status_code=400, detail=error)

        logger.info(f"Processing job application (user: {request.user_id})")

        # Get graph and execute workflow
        try:
            graph = get_job_copilot_graph()
        except Exception as e:
            logger.error(f"Failed to initialize graph: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize workflow engine")

        # Execute workflow
        result = await graph.execute(
            job_description=request.job_description,
            resume=request.resume,
        )

        # Check for errors
        if result.get("error"):
            logger.error(f"Workflow error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])

        # Prepare response
        cover_letter = result.get("cover_letter", {})
        job_desc = result.get("job_description", {})

        response = WorkflowExecutionResponse(
            success=True,
            matching_score=result.get("matching_score"),
            job_title=job_desc.get("title"),
            company=job_desc.get("company"),
            cover_letter=cover_letter.get("content") if cover_letter else None,
            analysis_summary=get_summary(result),
            execution_nodes=result.get("nodes_executed", []),
        )

        logger.info(f"Job application analysis complete (score: {response.matching_score:.1%})")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/graph/structure")
async def get_graph_structure() -> dict[str, object]:
    """
    Get the structure of the Job Copilot workflow graph.

    Useful for debugging and visualization.

    Returns:
        Dictionary describing graph structure
    """
    try:
        graph = get_job_copilot_graph()
        return graph.get_graph_structure()
    except Exception as e:
        logger.error(f"Failed to get graph structure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve graph structure")


@router.post("/batch-analyze")
async def batch_analyze_applications(
    applications: list[JobApplicationRequest],
    _background_tasks: BackgroundTasks,
) -> dict[str, object]:
    """
    Analyze multiple job applications in batch.

    For production use with Celery/Redis:
    - Queue each application as a Celery task
    - Return job IDs for polling
    - Store results in cache/database

    Args:
        applications: List of job applications to analyze
        background_tasks: FastAPI background tasks

    Returns:
        Dictionary with batch processing info
    """
    if not applications:
        raise HTTPException(status_code=400, detail="No applications provided")

    if len(applications) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 applications per batch")

    logger.info(f"Queuing batch analysis for {len(applications)} applications")

    results = []

    for app_request in applications:
        # In production, use Celery:
        # from tasks import analyze_application_task
        # task = analyze_application_task.delay(
        #     job_description=app_request.job_description,
        #     resume=app_request.resume,
        # )
        # results.append({"id": app_request.user_id, "task_id": task.id})

        # For now, just validate
        is_valid, error = validate_inputs(app_request.job_description, app_request.resume)
        if is_valid:
            results.append({"id": app_request.user_id, "status": "queued"})
        else:
            results.append({"id": app_request.user_id, "status": "failed", "error": error})

    return {
        "total": len(applications),
        "successful": sum(1 for r in results if r["status"] == "queued"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results,
    }


@router.get("/docs/workflow")
async def get_workflow_documentation() -> dict[str, object]:
    """
    Get documentation about the workflow.

    Returns:
        Dictionary with workflow documentation
    """
    return {
        "name": "Job Copilot",
        "description": "Agentic workflow for job application analysis",
        "nodes": [
            {
                "name": "parse_job_description",
                "description": "Extract and structure job posting information",
            },
            {
                "name": "analyze_resume",
                "description": "Match resume against job requirements",
            },
            {
                "name": "generate_cover_letter",
                "description": "Create personalized cover letter",
            },
        ],
        "inputs": {
            "job_description": "Raw job posting text (minimum 50 characters)",
            "resume": "Raw resume text (minimum 50 characters)",
        },
        "outputs": {
            "matching_score": "Overall fit score (0-1)",
            "job_title": "Extracted job title",
            "company": "Extracted company name",
            "cover_letter": "Generated cover letter",
            "analysis_summary": "Detailed analysis with strengths, gaps, recommendations",
        },
        "typical_execution_time": "2-5 seconds (depends on LLM response time)",
    }


# Optional: Include this in your FastAPI app
# Example in your main.py:
#
# from fastapi import FastAPI
# from app.api.job_copilot import router as job_copilot_router
#
# app = FastAPI()
# app.include_router(job_copilot_router)
