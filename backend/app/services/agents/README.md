# Job Copilot Agent System

A production-ready LangGraph-based agentic workflow for intelligent job application assistance. Uses LLM agents to analyze job descriptions, match resumes, and generate tailored cover letters.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           Job Copilot Agentic Workflow                  │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Parse Job Description Node                             │
│  - Extract title, company, requirements                 │
│  - Identify nice-to-have skills                         │
│  - Structure unstructured data                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Analyze Resume Node                                    │
│  - Match skills against job requirements               │
│  - Calculate fit scores                                │
│  - Identify skill gaps                                 │
│  - Highlight strengths                                 │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Generate Cover Letter Node                             │
│  - Create tailored cover letter                         │
│  - Highlight relevant achievements                      │
│  - Address skill gaps strategically                     │
│  - Professional, compelling tone                        │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. **state.py** - State Management
Defines shared state that flows through all nodes:
- `JobDescription`: Parsed job posting data
- `ResumeData`: Candidate resume information
- `CoverLetterData`: Generated output
- `JobCopilotState`: Main state container with metadata

### 2. **llm.py** - LLM Configuration
Singleton LLM provider for consistent model access:
- `LLMProvider`: Manages ChatOpenAI instances
- `LLMConfig`: Configuration management
- Functions: `get_llm()`, `init_llm()`

### 3. **nodes/** - Workflow Nodes

#### parse_jd.py
Parses raw job descriptions using LLM:
- Extracts: title, company, requirements, salary, location
- Validates and structures data
- Handles malformed input gracefully

#### analyze_resume.py
Analyzes resume fit against job description:
- Matches skills with job requirements
- Calculates matching scores (0-1)
- Identifies skill gaps
- Provides recommendations

#### generate_cover_letter.py
Generates personalized cover letters:
- Leverages job description and resume analysis
- Highlights relevant achievements
- Professional, compelling tone
- 250-300 words, ready to use

### 4. **job_copilot_graph.py** - Graph Orchestration
Main LangGraph workflow coordinator:
- `JobCopilotGraph`: Core orchestrator class
- Graph management and execution
- Async execution support
- Streaming capabilities
- Error handling

## Usage

### Basic Execution

```python
from app.services.agents import init_llm, init_job_copilot_graph

# Initialize LLM
init_llm()

# Get graph and execute
graph = init_job_copilot_graph()
result = await graph.execute(
    job_description="Job posting text...",
    resume="Resume text..."
)

# Access results
parsed_jd = result["job_description"]
analysis = result["resume_analysis"]
cover_letter = result["cover_letter"]
```

### With Custom LLM Config

```python
from app.services.agents import LLMConfig, init_llm

config = LLMConfig(
    model_name="gpt-4-turbo",
    temperature=0.7,
    max_tokens=2000,
)
init_llm(config)
```

### Streaming Execution

```python
graph = get_job_copilot_graph()

async for event in graph.stream_execution(job_description, resume):
    print(f"Event: {event}")
```

## State Structure

```python
{
    "job_description_raw": str,           # Input: raw job posting
    "resume_raw": str,                    # Input: raw resume
    "job_description": JobDescription,    # Parsed job data
    "resume_data": ResumeData,            # Parsed resume (optional)
    "resume_analysis": Dict,              # Analysis results
    "skill_gaps": List[str],              # Missing skills
    "matching_score": float,              # Overall fit (0-1)
    "cover_letter": CoverLetterData,      # Generated output
    "error": Optional[str],               # Error messages
    "nodes_executed": List[str],          # Execution tracking
}
```

## Features

✅ **LangGraph-based Agentic Workflow** - Modern async-first architecture  
✅ **Production Ready** - Error handling, logging, state management  
✅ **Type-Safe** - Full type hints throughout  
✅ **Structured Output** - Uses Pydantic for validation  
✅ **Extensible** - Easy to add new nodes or branches  
✅ **Streaming Support** - Real-time execution monitoring  
✅ **Singleton Pattern** - Efficient resource management  
✅ **Comprehensive Logging** - Debug and production logging  

## Environment Setup

```bash
export OPENAI_API_KEY="sk-..."
export LLM_MODEL="gpt-4-turbo"
export LLM_TEMPERATURE="0.7"
```

## Dependencies

- `langchain` - LLM framework
- `langgraph` - Agentic workflow
- `langchain-openai` - OpenAI integration
- `pydantic` - Data validation

Install with:
```bash
uv add langchain langgraph langchain-openai pydantic
```

## Running Examples

```bash
# Basic example
python -m app.services.agents.example_usage

# With streaming
# Uncomment stream_example() in example_usage.py
```

## Future Enhancements (Celery + Redis)

Once integrated with Celery and Redis:
- Async job queueing for multiple applications
- Distributed processing
- Result caching
- Rate limiting
- Long-running workflow support

### Example Celery Task

```python
from celery import shared_task

@shared_task
def generate_application(job_id, resume_id):
    graph = get_job_copilot_graph()
    job = Job.objects.get(id=job_id)
    resume = Resume.objects.get(id=resume_id)
    
    result = await graph.execute(
        job_description=job.content,
        resume=resume.content
    )
    
    Application.objects.create(
        job=job,
        resume=resume,
        cover_letter=result["cover_letter"]["content"],
        match_score=result["matching_score"]
    )
```

## Error Handling

All nodes include comprehensive error handling:
- Validates prerequisites before execution
- Graceful degradation
- Detailed logging
- Error tracking in state

## Logging

Access workflow logs:
```python
import logging

logger = logging.getLogger("app.services.agents")
logger.setLevel(logging.DEBUG)
```

## Performance Considerations

- Each node uses async/await for non-blocking execution
- LLM calls are the bottleneck (typically 2-5 seconds per workflow)
- Caching opportunities at each node boundary
- Can batch multiple applications with proper infrastructure

## Directory Structure

```
agents/
├── __init__.py
├── state.py                    # State definitions
├── llm.py                      # LLM configuration
├── job_copilot_graph.py        # Main graph orchestrator
├── example_usage.py            # Usage examples
├── nodes/
│   ├── __init__.py
│   ├── parse_jd.py            # Job description parser
│   ├── analyze_resume.py       # Resume analyzer
│   └── generate_cover_letter.py # Cover letter generator
└── README.md                   # This file
```

## Contributing

When adding new nodes:
1. Follow the node signature: `async def node_name(state: Dict[str, Any]) -> Dict[str, Any]`
2. Add comprehensive type hints
3. Include logging
4. Handle errors gracefully
5. Update state tracking (`nodes_executed`)
6. Add tests

## License

Same as parent project.
