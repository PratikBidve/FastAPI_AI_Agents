"""
Example usage of the Job Copilot agent workflow.
Demonstrates how to initialize and execute the agentic workflow.
"""

import asyncio
import logging

from app.services.agents import (
    LLMConfig,
    get_job_copilot_graph,
    init_job_copilot_graph,
    init_llm,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Example documents
SAMPLE_JOB_DESCRIPTION = """
Senior Backend Engineer (Python/FastAPI)
Company: TechCorp Solutions

About the Role:
We're looking for an experienced Backend Engineer to join our platform team.
You'll be responsible for designing and implementing scalable microservices
in Python/FastAPI, managing databases, and mentoring junior developers.

Requirements:
- 5+ years of backend development experience
- Expert-level Python and FastAPI knowledge
- PostgreSQL database design and optimization
- Redis/caching systems experience
- Experience with Docker and Kubernetes
- Microservices architecture understanding
- RESTful API design patterns
- Unit and integration testing expertise
- Git version control proficiency
- SQL query optimization

Nice to Have:
- GraphQL experience
- Message queue systems (RabbitMQ, Kafka)
- AWS cloud experience
- CI/CD pipeline experience
- Open-source contributions
- Technical writing/documentation skills

Salary: $150,000 - $180,000 USD
Location: San Francisco, CA (Remote possible)
"""

SAMPLE_RESUME = """
John Developer
Email: john@example.com | Phone: (555) 123-4567

Summary:
Experienced Backend Engineer with 6 years of software development experience.
Specialized in building scalable Python applications and cloud infrastructure.
Proven track record of leading technical projects and mentoring teams.

Experience:

Senior Backend Developer - StartupXYZ (2022 - Present)
- Led development of microservices architecture in Python/FastAPI
- Designed and implemented PostgreSQL database schemas
- Implemented Redis caching layer, reducing API response time by 60%
- Managed deployment using Docker and Kubernetes on AWS
- Mentored 3 junior developers
- Established CI/CD pipeline using GitHub Actions

Backend Engineer - DataCorp Inc (2020 - 2022)
- Developed REST APIs using Python/FastAPI for data processing platform
- Optimized slow SQL queries, improving dashboard performance by 45%
- Implemented comprehensive unit and integration testing (90% coverage)
- Contributed to open-source projects (active on GitHub)

Junior Backend Developer - WebServices Ltd (2018 - 2020)
- Built backend features for customer-facing applications
- Wrote clean, maintainable code following SOLID principles
- Participated in code reviews and tech discussions

Education:
Bachelor of Science in Computer Science
University of Technology (2018)

Skills:
Backend: Python, FastAPI, Flask, Django
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS (EC2, S3, RDS), Docker, Kubernetes
DevOps: CI/CD, GitHub Actions, Jenkins
Testing: Pytest, Unit Testing, Integration Testing
Other: Git, Linux, RESTful APIs

Certifications:
- AWS Certified Solutions Architect (2023)
"""


async def main():
    """Main example execution."""

    try:
        # Step 1: Initialize LLM with custom config
        llm_config = LLMConfig(
            model_name="gpt-4-turbo",
            temperature=0.7,
        )
        init_llm(llm_config)
        logger.info("✓ LLM initialized")

        # Step 2: Initialize or get graph
        graph = init_job_copilot_graph()
        logger.info("✓ Job Copilot graph initialized")

        # Step 3: Display graph structure
        graph_structure = graph.get_graph_structure()
        logger.info(f"Graph structure: {graph_structure}")

        # Step 4: Execute the workflow
        logger.info("\n" + "="*60)
        logger.info("EXECUTING JOB COPILOT WORKFLOW")
        logger.info("="*60 + "\n")

        result = await graph.execute(
            job_description=SAMPLE_JOB_DESCRIPTION,
            resume=SAMPLE_RESUME,
        )

        # Step 5: Display results
        logger.info("\n" + "="*60)
        logger.info("WORKFLOW RESULTS")
        logger.info("="*60 + "\n")

        # Parsed Job Description
        if result.get("job_description"):
            jd = result["job_description"]
            logger.info(f"📋 Job Title: {jd.get('title')}")
            logger.info(f"🏢 Company: {jd.get('company')}")
            logger.info(f"📍 Location: {jd.get('location')}")
            logger.info(f"💰 Salary: {jd.get('salary_range')}")
            logger.info(f"Requirements ({len(jd.get('requirements', []))}): {', '.join(jd.get('requirements', [])[:3])}...")
            logger.info(f"Nice to Have ({len(jd.get('nice_to_have', []))}): {', '.join(jd.get('nice_to_have', [])[:2])}...")

        # Resume Analysis
        if result.get("resume_analysis"):
            analysis = result["resume_analysis"]
            logger.info("\n📊 Resume Analysis:")
            logger.info(f"  Overall Fit: {analysis.get('overall_fit_score', 0):.1%}")
            logger.info(f"  Skills Score: {analysis.get('skills_score', 0):.1%}")
            logger.info(f"  Experience Score: {analysis.get('experience_score', 0):.1%}")
            logger.info(f"  Matched Skills: {len(analysis.get('matched_skills', []))}")
            logger.info(f"    {', '.join(analysis.get('matched_skills', [])[:3])}...")
            logger.info(f"  Missing Skills: {len(analysis.get('missing_skills', []))}")
            if analysis.get('missing_skills'):
                logger.info(f"    {', '.join(analysis.get('missing_skills', [])[:3])}...")
            logger.info("  Strengths:")
            for strength in analysis.get('strengths', [])[:2]:
                logger.info(f"    • {strength}")
            logger.info("  Recommendations:")
            for rec in analysis.get('recommendations', [])[:2]:
                logger.info(f"    • {rec}")

        # Cover Letter
        if result.get("cover_letter"):
            cl = result["cover_letter"]
            logger.info("\n💌 Cover Letter Generated:")
            logger.info(f"  Tone: {cl.get('tone')}")
            logger.info(f"  Highlighted Skills: {', '.join(cl.get('highlighted_skills', []))}")
            logger.info(f"  Key Achievements: {len(cl.get('key_achievements', []))}")
            logger.info("\n--- Cover Letter Preview ---")
            preview = cl.get('content', '')[:300] + "..."
            logger.info(preview)

        # Metadata
        logger.info("\n✅ Workflow completed")
        logger.info(f"  Nodes executed: {result.get('nodes_executed', [])}")
        logger.info(f"  Error: {result.get('error', 'None')}")

        return result

    except Exception as e:
        logger.error(f"Error in workflow: {str(e)}", exc_info=True)
        raise


async def stream_example():
    """Example of streaming execution."""
    logger.info("\n" + "="*60)
    logger.info("STREAMING EXECUTION EXAMPLE")
    logger.info("="*60 + "\n")

    graph = get_job_copilot_graph()

    async for event in graph.stream_execution(
        job_description=SAMPLE_JOB_DESCRIPTION,
        resume=SAMPLE_RESUME,
    ):
        logger.info(f"Event: {event}")


if __name__ == "__main__":
    # Run basic example
    result = asyncio.run(main())

    # Uncomment to run streaming example
    # asyncio.run(stream_example())
