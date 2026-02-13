"""
Job Copilot Graph - Main agentic workflow orchestration using LangGraph.
Defines the workflow graph with nodes, edges, and execution logic.
"""

import logging

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from .nodes.analyze_resume import analyze_resume
from .nodes.generate_cover_letter import generate_cover_letter
from .nodes.parse_jd import parse_job_description
from .state import JobCopilotStateDict

logger = logging.getLogger(__name__)


class JobCopilotGraph:
    """
    Main orchestrator for the Job Copilot agentic workflow.
    Manages graph construction, execution, and state management.
    """

    def __init__(self):
        """Initialize the graph."""
        self.graph = self._build_graph()
        logger.info("JobCopilotGraph initialized")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow graph.

        Workflow:
        START -> Parse Job Description -> Analyze Resume -> Generate Cover Letter -> END

        Returns:
            Constructed StateGraph
        """
        # Create the graph
        workflow = StateGraph(JobCopilotStateDict)

        # Add nodes
        workflow.add_node("parse_job_description", parse_job_description)
        workflow.add_node("analyze_resume", analyze_resume)
        workflow.add_node("generate_cover_letter", generate_cover_letter)

        # Define edges (workflow flow)
        workflow.add_edge(START, "parse_job_description")
        workflow.add_edge("parse_job_description", "analyze_resume")
        workflow.add_edge("analyze_resume", "generate_cover_letter")
        workflow.add_edge("generate_cover_letter", END)

        logger.debug("Graph workflow edges configured")

        return workflow

    @property
    def compiled_graph(self):
        """Get the compiled graph ready for execution."""
        return self.graph.compile()

    async def execute(
        self,
        job_description: str,
        resume: str,
        config: RunnableConfig | None = None,
    ) -> dict[str, object]:
        """
        Execute the complete Job Copilot workflow.

        Args:
            job_description: Raw job description text
            resume: Raw resume text
            config: Optional RunnableConfig for execution

        Returns:
            Final state containing all workflow outputs
        """
        try:
            # Prepare initial state
            initial_state: JobCopilotStateDict = {
                "job_description_raw": job_description,
                "resume_raw": resume,
                "job_description": None,
                "resume_data": None,
                "resume_analysis": None,
                "skill_gaps": None,
                "matching_score": None,
                "cover_letter": None,
                "error": None,
                "nodes_executed": [],
            }

            logger.info("Starting Job Copilot workflow execution")
            logger.debug(f"Input resume length: {len(resume)} chars, JD length: {len(job_description)} chars")

            # Execute graph
            compiled = self.compiled_graph
            final_state = await compiled.ainvoke(initial_state, config=config)

            logger.info(
                f"Workflow completed. Nodes executed: {final_state.get('nodes_executed', [])}. "
                f"Matching score: {final_state.get('matching_score')}"
            )

            return final_state

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "job_description_raw": job_description,
                "resume_raw": resume,
                "error": error_msg,
                "nodes_executed": [],
            }

    async def stream_execution(
        self,
        job_description: str,
        resume: str,
        config: RunnableConfig | None = None,
    ):
        """
        Stream execution events for real-time monitoring.

        Args:
            job_description: Raw job description text
            resume: Raw resume text
            config: Optional RunnableConfig for execution

        Yields:
            Streaming events during execution
        """
        try:
            initial_state: JobCopilotStateDict = {
                "job_description_raw": job_description,
                "resume_raw": resume,
                "job_description": None,
                "resume_data": None,
                "resume_analysis": None,
                "skill_gaps": None,
                "matching_score": None,
                "cover_letter": None,
                "error": None,
                "nodes_executed": [],
            }

            logger.info("Starting streaming workflow execution")
            compiled = self.compiled_graph

            # Stream events
            async for event in compiled.astream_events(initial_state, config=config, version="v2"):
                logger.debug(f"Stream event: {event.get('event')} from {event.get('name')}")
                yield event

        except Exception as e:
            error_msg = f"Streaming execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                "event": "error",
                "data": {"error": error_msg}
            }

    def get_graph_structure(self) -> dict[str, object]:
        """
        Get the structure of the workflow graph for visualization/debugging.

        Returns:
            Dictionary describing the graph structure
        """
        return {
            "nodes": ["parse_job_description", "analyze_resume", "generate_cover_letter"],
            "edges": [
                {"from": "START", "to": "parse_job_description"},
                {"from": "parse_job_description", "to": "analyze_resume"},
                {"from": "analyze_resume", "to": "generate_cover_letter"},
                {"from": "generate_cover_letter", "to": "END"},
            ],
            "description": "Linear workflow: parse JD -> analyze resume -> generate cover letter"
        }


# Singleton instance
_job_copilot_graph: JobCopilotGraph | None = None


def get_job_copilot_graph() -> JobCopilotGraph:
    """Get or create the singleton JobCopilotGraph instance."""
    global _job_copilot_graph
    if _job_copilot_graph is None:
        _job_copilot_graph = JobCopilotGraph()
    return _job_copilot_graph


def init_job_copilot_graph() -> JobCopilotGraph:
    """Initialize a fresh JobCopilotGraph instance."""
    global _job_copilot_graph
    _job_copilot_graph = JobCopilotGraph()
    return _job_copilot_graph
