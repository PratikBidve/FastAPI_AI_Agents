# Job Copilot Agent System - Test Documentation

## Overview

This directory contains comprehensive, production-grade tests for the Job Copilot agent system. All tests are designed to validate functionality, security, and reliability.

## Test Coverage

### 1. **test_utils.py** (Input Validation & Export)
- `TestValidateInputs`: Validates input length, empty values, edge cases
- `TestExportWorkflowResult`: Tests result serialization and export
- `TestGetSummary`: Tests summary generation from results  
- `TestFormatForJson`: Tests JSON serialization with datetime handling
- `TestMergeResults`: Tests merging workflow results

**Coverage**: Input validation, data serialization, transformations

### 2. **test_state.py** (State Management)
- `TestJobDescription`: Job description TypedDict validation
- `TestResumeData`: Resume data structure validation
- `TestCoverLetterData`: Cover letter data validation
- `TestJobCopilotState`: State dataclass validation
- `TestStateTransitions`: Valid state flow transitions
- `TestStateValidation`: State constraints and immutability
- `TestStateDeepCopy`: Data isolation verification

**Coverage**: State schema, data structure, workflow transitions

### 3. **test_security.py** (Security Testing)
- `TestInputSanitization`: SQL injection, XSS, prompt injection
- `TestDataExposure`: Information disclosure prevention
- `TestInputValidationBoundaries`: Boundary testing
- `TestNovelAttackVectors`: Null bytes, control characters
- `TestResourceLimits`: Large input handling
- `TestInfoDisclosure`: Error message safety
- `TestInputTypeHandling`: Type coercion and handling
- `TestReproducibility`: Determinism verification

**Coverage**: Security vulnerabilities, attack vectors, resource limits, privacy

### 4. **test_fastapi_integration.py** (API Endpoints)
- `TestHealthEndpoint`: Health check validation
- `TestAnalyzeEndpoint`: Application analysis endpoint
- `TestBatchAnalyzeEndpoint`: Batch analysis with rate limits
- `TestGraphStructureEndpoint`: Workflow graph endpoint
- `TestWorkflowDocumentationEndpoint`: Documentation endpoint
- `TestErrorHandling`: Error responses and validation
- `TestRateLimitingAndSecurity`: Security headers
- `TestCORSHeaders`: CORS handling
- `TestInputValidation`: Input validation on API
- `TestRequestResponse`: Request/response patterns

**Coverage**: API endpoints, validation, error handling, security

### 5. **test_llm.py** (LLM Integration)
- `TestLLMProvider`: Singleton pattern verification
- `TestLLMProviderWithMocks`: Mocked LLM initialization
- `TestLLMIntegration`: LLM workflow integration
- `TestLLMCaching`: Instance caching
- `TestLLMProviderThreadSafety`: Concurrent access handling

**Coverage**: LLM provider, initialization, caching, thread safety

### 6. **test_nodes.py** (Workflow Nodes)
- `TestParseJDNode`: Job description parsing validation
- `TestResumeAnalysisNode`: Resume analysis data validation
- `TestCoverLetterNode`: Cover letter generation validation
- `TestNodeDataTypes`: Type validation for node outputs
- `TestScoreValidation`: Score range validation

**Coverage**: Node outputs, data schemas, type validation

## Running Tests

### Setup (One-time)

```bash
# Navigate to project root
cd /Users/prateekbidve/Desktop/full_stack

# Create and configure .env file
cp .env.example .env

# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-...your_key_here...

# Or set environment variable
export OPENAI_API_KEY="your_openai_api_key_here"

# Install dependencies with uv
uv pip install -e ".[dev]"

# Or using traditional pip
pip install -e ".[dev]"
```

### Run All Tests

```bash
# Run all agent tests
uv run pytest backend/tests/agents/ -v

# Run with coverage report
uv run pytest backend/tests/agents/ --cov=app.services.agents --cov-report=html

# Run with detailed output
uv run pytest backend/tests/agents/ -vv --tb=long
```

### Run Specific Test Suites

```bash
# Validation tests only
uv run pytest backend/tests/agents/test_utils.py -v

# State management tests
uv run pytest backend/tests/agents/test_state.py -v

# Security tests
uv run pytest backend/tests/agents/test_security.py -v

# API endpoint tests
uv run pytest backend/tests/agents/test_fastapi_integration.py -v

# LLM tests (requires OPENAI_API_KEY)
uv run pytest backend/tests/agents/test_llm.py -v

# Node tests
uv run pytest backend/tests/agents/test_nodes.py -v
```

### Run Specific Test Classes

```bash
pytest backend/tests/agents/test_utils.py::TestValidateInputs -v
pytest backend/tests/agents/test_security.py::TestInputSanitization -v
pytest backend/tests/agents/test_fastapi_integration.py::TestAnalyzeEndpoint -v
```

### Run with Markers

```bash
# Run only fast tests
pytest backend/tests/agents/ -m "not slow" -v

# Run only security tests
pytest backend/tests/agents/test_security.py -v
```

## Test Fixtures

Common fixtures defined in `conftest.py`:

- `sample_job_description`: Realistic job description (50+ chars)
- `sample_resume`: Realistic resume (50+ chars)
- `empty_job_description`: Empty string for invalid input testing
- `short_job_description`: <50 char JD for validation testing
- `empty_resume`: Empty string for invalid input testing
- `short_resume`: <50 char resume for validation testing
- `initial_state`: Fresh JobCopilotState for workflow testing
- `malicious_jd_sql_injection`: SQL injection attempt (security)
- `malicious_resume_xss`: XSS attack attempt (security)
- `malicious_resume_prompt_injection`: Prompt injection attempt (security)

## Test Organization

All tests follow pytest conventions:

```
backend/tests/agents/
├── conftest.py                      # Shared fixtures
├── test_utils.py                    # Utility function tests
├── test_state.py                    # State management tests
├── test_security.py                 # Security tests
├── test_fastapi_integration.py      # API endpoint tests
├── test_llm.py                      # LLM integration tests
├── test_nodes.py                    # Workflow node tests
└── test_README.md                   # This file
```

## Test Naming Conventions

- `TestXxx`: Test class grouping related tests
- `test_xyz`: Individual test function
- `sample_xyz`: Fixture providing sample data
- `malicious_xyz`: Fixture providing attack payloads for security

## Expected Test Results

All tests should pass in production:

- ✅ **100+ unit tests** covering core functionality
- ✅ **Security tests** validating input safety
- ✅ **Integration tests** for API endpoints
- ✅ **Type validation** for all data structures
- ✅ **Error handling** and edge cases

## Coverage Goals

Target coverage metrics:

- **Statements**: 85%+
- **Branches**: 80%+
- **Functions**: 90%+
- **Lines**: 85%+

Check coverage:

```bash
pytest backend/tests/agents/ --cov=app.services.agents --cov-report=term-missing --cov-report=html
open htmlcov/index.html  # View detailed report
```

## Continuous Integration

These tests are designed for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Agent Tests
  run: |
    pytest backend/tests/agents/ -v --junitxml=report.xml --cov=app.services.agents
```

## Security Testing

Special attention to security vectors:

1. **Input Injection**
   - SQL injection attempts
   - XSS/JavaScript injection
   - Prompt injection attacks
   - Command injection patterns

2. **Data Exposure**
   - Sensitive information leakage
   - Error message disclosure
   - Stack trace exposure

3. **Resource Exhaustion**
   - Large input handling
   - Deep nesting handling
   - Memory stability

4. **Boundary Conditions**
   - Minimum/maximum lengths
   - Type coercion
   - Unicode handling

## Mocking Strategy

Tests use `unittest.mock` for external dependencies:

- LLM API calls are mocked
- Database operations are mocked
- External service calls are mocked
- Internal state is tested directly

## Performance Testing

Tests verify reasonable performance:

```bash
pytest backend/tests/agents/ --durations=10  # Top 10 slowest tests
```

Slow tests should be marked accordingly:

```python
@pytest.mark.slow
def test_heavy_operation():
    pass
```

## Debugging Failed Tests

```bash
# Show print statements
pytest backend/tests/agents/ -v -s

# Drop into debugger on failure
pytest backend/tests/agents/ --pdb

# Show local variables in tracebacks
pytest backend/tests/agents/ -v --tb=long

# Run single test with debugging
pytest backend/tests/agents/test_utils.py::TestValidateInputs::test_valid_inputs -vv --tb=long
```

## Production Deployment

Before production deployment:

```bash
# Full test suite with coverage
pytest backend/tests/agents/ -v --cov=app.services.agents --cov-report=term-missing

# Security-focused tests
pytest backend/tests/agents/test_security.py -v

# Integration tests
pytest backend/tests/agents/test_fastapi_integration.py -v
```

## Maintenance

### Adding New Tests

1. Create test in appropriate file
2. Ensure it uses existing fixtures
3. Add fixtures to `conftest.py` if needed
4. Follow naming conventions
5. Add docstring to test function
6. Run full test suite to verify

### Updating Tests

When code changes:

1. Run full test suite
2. Update failing tests
3. Add new test cases for new features
4. Maintain coverage above targets
5. Test edge cases and error paths

## Known Limitations

- External LLM calls are mocked (tests don't use real OpenAI API)
- Celery tasks are not executed (integration testing differs)
- Database is mocked or in-memory during tests
- Network calls are mocked

These are intentional for fast, reliable, reproducible tests.

## Support

For test issues or questions:

1. Check this documentation
2. Review specific test file docstrings
3. Check pytest documentation: https://docs.pytest.org/
4. Review test fixtures in `conftest.py`

## Test Quality Metrics

Our test suite ensures:

✅ Comprehensive input validation testing  
✅ Security vulnerability coverage  
✅ Edge case handling  
✅ Type safety verification  
✅ Error message appropriateness  
✅ Resource limit testing  
✅ Deterministic/reproducible tests  
✅ Clear test documentation  
✅ Production-ready assertions  
✅ Fast test execution  

---

**Last Updated**: February 13, 2026
**Python Version**: 3.10+
**Pytest Version**: 7.4.3+
**Status**: Production-Ready ✅
