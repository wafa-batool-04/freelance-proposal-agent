from __future__ import annotations

from tools.llm_client import LLMClient
from utils.json_utils import parse_llm_json

SYSTEM = """You are an expert freelance job analyst. Extract structured insights from job postings.
Always respond with valid JSON only — no markdown, no explanation."""

PROMPT = """Analyze this job posting and return a JSON object with these keys:
- client_needs: list of 3-5 strings describing what the client needs
- required_skills: list of specific skills mentioned or implied
- budget_timeline: string summarizing budget and/or timeline info (or "Not specified")
- tone: string describing the client's communication tone (e.g. "casual", "corporate", "urgent")
- key_selling_points: list of 3-5 points a freelancer should highlight to win this job

Job posting:
{job_post}"""


class JobAnalyzer:
    def __init__(self, client: LLMClient):
        self.client = client

    def analyze(self, job_post: str) -> dict:
        response = self.client.complete(
            prompt=PROMPT.format(job_post=job_post),
            system=SYSTEM,
            max_tokens=1024,
            temperature=0.3,
        )
        return parse_llm_json(response)
