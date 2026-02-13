# Job Copilot Agent System - Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client Layer                                │
│  (FastAPI, Celery, WebClient, CLI)                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                 API Integration Layer                            │
│  (fastapi_integration.py)                                        │
│  - Request validation                                            │
│  - Response formatting                                           │
│  - Error handling                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│               Async Task Processing Layer                        │
│  (celery_tasks.py - Optional)                                   │
│  - Job queuing                                                   │
│  - Retry logic                                                   │
│  - Redis backend                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Orchestration Layer                       │
│  (job_copilot_graph.py)                                         │
│  - Graph construction                                            │
│  - Workflow execution                                            │
│  - State management                                              │
│  - Error recovery                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────┬───────────┬───────────┐
        ↓           ↓           ↓           ↓
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Node 1 │  │ Node 2 │  │ Node 3 │
    │ Parse  │→ │Analyze │→ │Generate│
    │   JD   │  │Resume  │  │   CL   │
    └────────┘  └────────┘  └────────┘
        ↓           ↓           ↓
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Extract│  │ Match  │  │ Create │
    │ Data   │  │Skills  │  │ Letter │
    └────────┘  └────────┘  └────────┘
        ↓           ↓           ↓
┌─────────────────────────────────────────────────────────────────┐
│              LLM Processing Layer                                │
│  (llm.py)                                                        │
│  - LLMProvider (Singleton)                                       │
│  - OpenAI ChatGPT-4 integration                                  │
│  - Prompt management                                             │
│  - Output parsing                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                 External Services                                │
│  - OpenAI API                                                    │
│  - Redis (cache/queue)                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Path
```
Input (JD + Resume)
  ↓ [Validation: utils.validate_inputs()]
  ↓
FastAPI Endpoint [fastapi_integration.py]
  ↓ [Queue or Direct]
  ↓
Celery Task (optional) [celery_tasks.py]
  ↓
LangGraph Workflow [job_copilot_graph.py]
  ├→ Parse JD [nodes/parse_jd.py]
  │   ├→ LLM call with structured prompt
  │   ├→ JSON parsing
  │   └→ State update
  │
  ├→ Analyze Resume [nodes/analyze_resume.py]
  │   ├→ LLM call with context from JD
  │   ├→ Skill matching
  │   ├→ Score calculation
  │   └→ State update
  │
  └→ Generate Cover Letter [nodes/generate_cover_letter.py]
      ├→ LLM call with full context
      ├→ Professional formatting
      ├→ Achievement highlighting
      └→ State update

Output (Results + CL)
  ↓ [Export: utils.export_workflow_result()]
  ↓
Response to Client [fastapi_integration.py]
```

### State Evolution
```
Initial State:
{
  job_description_raw: "Raw JD text",
  resume_raw: "Raw resume text",
  □ All other fields: null/empty
}

After Node 1 (Parse JD):
{
  job_description: {title, company, requirements, ...},
  nodes_executed: ["parse_job_description"],
  ...
}

After Node 2 (Analyze Resume):
{
  job_description: {...},
  resume_analysis: {matched_skills, missing_skills, scores, ...},
  skill_gaps: [...],
  matching_score: 0.78,
  nodes_executed: ["parse_job_description", "analyze_resume"],
  ...
}

After Node 3 (Generate CL):
{
  job_description: {...},
  resume_analysis: {...},
  cover_letter: {content, tone, skills, achievements},
  nodes_executed: [all 3 nodes],
  ...
}
```

## Component Responsibilities

### state.py
- **Responsibility**: Data structure definition
- **Exports**: JobCopilotState, JobDescription, ResumeData, CoverLetterData
- **Dependencies**: dataclasses, typing
- **Key Features**: Type hints, dataclass with helpers, TypedDict variants

### llm.py
- **Responsibility**: LLM provider management
- **Exports**: LLMProvider, LLMConfig, get_llm(), init_llm()
- **Dependencies**: langchain_openai, pydantic
- **Key Features**: Singleton pattern, lazy initialization, config management

### nodes/parse_jd.py
- **Responsibility**: Job description extraction
- **Input State**: job_description_raw
- **Output State**: job_description, nodes_executed
- **Processing**: LLM → JsonParser → TypedDict conversion
- **Error Handling**: Validates prerequisites, logs errors

### nodes/analyze_resume.py
- **Responsibility**: Resume-job matching
- **Input State**: job_description, resume_raw
- **Output State**: resume_analysis, skill_gaps, matching_score
- **Processing**: LLM → JsonParser → Score calculation
- **Output**: Structured analysis with scores

### nodes/generate_cover_letter.py
- **Responsibility**: Tailored cover letter generation
- **Input State**: job_description, resume_raw, resume_analysis
- **Output State**: cover_letter
- **Processing**: LLM → JsonParser → Professional formatting
- **Output**: 250-300 word ready-to-use letter

### job_copilot_graph.py
- **Responsibility**: Workflow orchestration
- **Exports**: JobCopilotGraph, get_job_copilot_graph()
- **Key Methods**:
  - execute(): Async workflow execution
  - stream_execution(): Real-time event streaming
  - get_graph_structure(): Debug/visualization
- **Features**: Error recovery, logging, singleton

### fastapi_integration.py
- **Responsibility**: HTTP API endpoints
- **Exports**: router (APIRouter)
- **Endpoints**:
  - POST /analyze - Main endpoint
  - GET /health - Health check
  - GET /graph/structure - Debug info
  - POST /batch-analyze - Batch processing
- **Features**: Request validation, response formatting

### celery_tasks.py
- **Responsibility**: Async task processing
- **Tasks**:
  - analyze_application_task() - Individual analysis
  - batch_analyze_applications_task() - Batch queuing
  - get_batch_results_task() - Result collection
- **Features**: Retry logic, timeout handling, callbacks

### utils.py
- **Responsibility**: Utility functions
- **Key Functions**:
  - validate_inputs() - Input validation
  - export_workflow_result() - Result export
  - get_summary() - Summary generation
  - format_cover_letter_for_display() - Formatting
  - format_for_json() - Serialization

## Node Execution Pattern

Each node follows this pattern:

```python
async def my_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # 1. Validate prerequisites
        if not state.get("required_field"):
            state["error"] = "Missing prerequisite"
            return state
        
        # 2. Initialize LLM components
        llm = get_llm()
        
        # 3. Execute main logic
        result = await chain.ainvoke(inputs)
        
        # 4. Update state
        state["output_field"] = result
        state["nodes_executed"].append("my_node")
        
        # 5. Log success
        logger.info("Node completed successfully")
        
    except Exception as e:
        # 6. Error handling
        error_msg = f"Error in node: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["error"] = error_msg
    
    return state
```

## Error Handling Strategy

```
┌─ Input Validation
│   └─ Invalid inputs → Return error immediately
│
├─ Node Prerequisites
│   └─ Missing upstream data → Log warning, return with error flag
│
├─ LLM Processing
│   └─ API error → Log, propagate with details
│
├─ Output Parsing
│   └─ Parse error → Retry or fall back to string
│
└─ Recovery
    ├─ Retry logic (Celery tasks)
    ├─ Graceful degradation
    └─ Complete state tracking
```

## Performance Optimization

1. **LLM Efficiency**
   - Prompt engineering for faster responses
   - Structured outputs reduce retries
   - Temperature tuning

2. **Caching**
   - Redis integration for results
   - LLM response memoization (future)
   - Celery result backend

3. **Concurrency**
   - Async/await throughout
   - Batch processing support
   - Non-blocking I/O

4. **Resource Management**
   - Singleton LLM provider
   - Lazy initialization
   - Connection pooling

## Extensibility Points

1. **Add New Nodes**
   - Create file in nodes/
   - Follow node pattern
   - Update graph.py edges
   - Add to imports

2. **Modify State**
   - Extend JobCopilotState in state.py
   - Update nodes accessing new fields
   - Migration handling for persistence

3. **Add Processing Options**
   - New LLM models in llm.py
   - Custom prompt templates
   - Additional output formats

4. **Integrate Services**
   - Database for persistence
   - Email for notifications
   - Webhooks for updates
   - Analytics/monitoring

## Testing Strategy

```
Unit Tests
  ├─ Node input/output validation
  ├─ State transitions
  ├─ Error scenarios
  └─ Utility functions

Integration Tests
  ├─ Full workflow execution
  ├─ API endpoints
  ├─ Celery tasks
  └─ Database persistence

E2E Tests
  ├─ Real application analysis
  ├─ Output quality
  └─ Performance benchmarks
```

## Deployment Considerations

### Local Development
```bash
# Direct execution
python -m app.services.agents.example_usage

# With FastAPI
uvicorn app.main:app --reload
```

### Production
```bash
# FastAPI worker
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Celery worker
celery -A app.services.agents.celery_tasks worker -l info

# Celery beat (scheduling)
celery -A app.services.agents.celery_tasks beat -l info
```

### Monitoring
- Logs: application/debug logs
- Metrics: LLM costs, latency, success rates
- Health checks: /api/v1/job-copilot/health
- Celery monitoring: flower, prometheus exporters

## Security Considerations

1. **API Keys** - Secure storage, rotation
2. **Rate Limiting** - API throttling
3. **Input Validation** - All user inputs validated
4. **Output Sanitization** - XSS prevention
5. **Data Privacy** - No logging of sensitive info
6. **Access Control** - Auth/authz middleware

## Future Enhancements

- [ ] Multi-modal input (PDF uploads)
- [ ] Cover letter versioning
- [ ] Interview prep integration
- [ ] Skill ontology/graph
- [ ] ML-based personalization
- [ ] Real-time collaboration
- [ ] Mobile app integration
- [ ] Advanced analytics
