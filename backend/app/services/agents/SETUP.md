"""
Job Copilot Setup and Configuration Guide
Quick start and configuration options for the agent system.

Files:
- state.py: State management and data models
- llm.py: LLM provider and configuration
- nodes/: Individual workflow nodes
- job_copilot_graph.py: Main graph orchestrator
- fastapi_integration.py: FastAPI API endpoints
- celery_tasks.py: Async task processing (optional)
- utils.py: Utility functions
"""

import os
import sys
from pathlib import Path
from typing import Optional

from app.services.agents import init_llm, LLMConfig, get_job_copilot_graph


def setup_environment() -> None:
    """Setup environment variables for Job Copilot."""
    
    required_vars = {
        "OPENAI_API_KEY": "Your OpenAI API key",
    }
    
    optional_vars = {
        "LLM_MODEL": "gpt-4-turbo (default)",
        "LLM_TEMPERATURE": "0.7 (default)",
    }
    
    print("=" * 60)
    print("Job Copilot Environment Setup")
    print("=" * 60)
    
    missing_required = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_required.append(f"  ✗ {var}: {description}")
        else:
            masked = value[:10] + "..." if len(str(value)) > 10 else value
            print(f"  ✓ {var}: {masked}")
    
    for var, description in optional_vars.items():
        value = os.getenv(var, description.split("(")[0].strip())
        print(f"  ℹ {var}: {value}")
    
    if missing_required:
        print("\n⚠️  Missing required environment variables:")
        for var in missing_required:
            print(var)
        sys.exit(1)
    
    print("\n✅ Environment setup complete")


def initialize_system(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> dict:
    """
    Initialize the Job Copilot system.
    
    Args:
        api_key: OpenAI API key (if not in env)
        model: Model name (default: gpt-4-turbo)
        temperature: Temperature for LLM (default: 0.7)
        
    Returns:
        Dictionary with initialization status
    """
    
    try:
        # Create LLM config
        config = LLMConfig(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            model_name=model or os.getenv("LLM_MODEL", "gpt-4-turbo"),
            temperature=float(temperature or os.getenv("LLM_TEMPERATURE", 0.7)),
        )
        
        # Initialize LLM
        init_llm(config)
        
        # Get graph
        graph = get_job_copilot_graph()
        
        return {
            "success": True,
            "llm_initialized": True,
            "graph_initialized": bool(graph),
            "model": config.model_name,
            "temperature": config.temperature,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def print_quick_start() -> None:
    """Print quick start guide."""
    
    guide = """
╔════════════════════════════════════════════════════════════╗
║           Job Copilot Quick Start Guide                   ║
╚════════════════════════════════════════════════════════════╝

1. SETUP ENVIRONMENT
   
   export OPENAI_API_KEY="sk-your-key-here"
   export LLM_MODEL="gpt-4-turbo"
   export LLM_TEMPERATURE="0.7"

2. BASIC USAGE (Python)
   
   from app.services.agents import init_llm, init_job_copilot_graph
   
   # Initialize
   init_llm()
   graph = init_job_copilot_graph()
   
   # Execute
   result = await graph.execute(
       job_description="...",
       resume="..."
   )
   
   # Access results
   cover_letter = result["cover_letter"]["content"]
   score = result["matching_score"]

3. FASTAPI INTEGRATION
   
   from app.api.job_copilot import router
   
   app = FastAPI()
   app.include_router(router)
   
   # POST /api/v1/job-copilot/analyze
   # GET  /api/v1/job-copilot/health

4. ASYNC/CELERY (Optional)
   
   # Install: pip install celery[redis]
   # Start worker: celery -A app.services.agents.celery_tasks worker
   
   from app.services.agents.celery_tasks import analyze_application_task
   
   task = analyze_application_task.delay(
       job_description="...",
       resume="...",
       user_id="user123"
   )

5. EXAMPLE RUN
   
   python -m app.services.agents.example_usage

╔════════════════════════════════════════════════════════════╗
║              System Components                             ║
╚════════════════════════════════════════════════════════════╝

STATE MANAGEMENT
  ├── job_description_raw: Input job posting
  ├── resume_raw: Input resume
  ├── job_description: Parsed JD
  ├── resume_analysis: Analysis results
  ├── matching_score: Fit score (0-1)
  └── cover_letter: Generated letter

WORKFLOW NODES
  1. parse_job_description - Extract & structure JD
  2. analyze_resume - Match skills & calculate scores
  3. generate_cover_letter - Create tailored letter

FEATURES
  ✓ LangGraph agentic workflow
  ✓ Async/await execution
  ✓ Streaming support
  ✓ Error handling & recovery
  ✓ Type-safe with Pydantic
  ✓ FastAPI integration ready
  ✓ Celery task support
  ✓ Comprehensive logging

EXECUTION FLOW
  
  Input (JD + Resume)
         ↓
  Parse Job Description
         ↓
  Analyze Resume
         ↓
  Generate Cover Letter
         ↓
  Output (Results + Letter)

╔════════════════════════════════════════════════════════════╗
║              Performance Expectations                      ║
╚════════════════════════════════════════════════════════════╝

Typical execution: 2-5 seconds
  • JD parsing: ~1-2 seconds
  • Resume analysis: ~1-2 seconds
  • Cover letter generation: ~1-2 seconds

Memory usage: ~100-200 MB
Redis (optional): ~10 MB per cached result

╔════════════════════════════════════════════════════════════╗
║              Configuration Options                         ║
╚════════════════════════════════════════════════════════════╝

LLM Models (OpenAI):
  - gpt-4-turbo (recommended) - Fastest, best quality
  - gpt-4 - Slower, highest quality
  - gpt-3.5-turbo - Fastest, decent quality

Temperature:
  - 0.0: Deterministic
  - 0.7: Balanced (recommended)
  - 1.0+: Creative (not recommended for this task)

╔════════════════════════════════════════════════════════════╗
║              Debugging & Monitoring                        ║
╚════════════════════════════════════════════════════════════╝

Logging:
  import logging
  logger = logging.getLogger("app.services.agents")
  logger.setLevel(logging.DEBUG)

Health check:
  GET /api/v1/job-copilot/health

Graph structure:
  GET /api/v1/job-copilot/graph/structure

Task monitoring (Celery):
  celery -A app.services.agents.celery_tasks inspect active
  celery -A app.services.agents.celery_tasks inspect stats
"""
    
    print(guide)


if __name__ == "__main__":
    print_quick_start()
