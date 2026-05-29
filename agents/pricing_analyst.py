from __future__ import annotations

from config.markets import MarketConfig
from tools.llm_client import LLMClient
from utils.json_utils import parse_llm_json

SYSTEM = """You are a freelance pricing strategist with deep knowledge of market rates across platforms and niches.
You analyze job postings and freelancer profiles to recommend optimal pricing strategies.
Always respond with valid JSON only — no markdown, no explanation."""

PROMPT = """Analyze this freelance opportunity and recommend a pricing strategy.

=== JOB ANALYSIS ===
Client needs: {client_needs}
Required skills: {required_skills}
Budget / timeline: {budget_timeline}
Client tone: {client_tone}

=== FREELANCER PROFILE ===
Skills & experience: {skills}
Desired rate: {desired_rate}

=== PLATFORM ===
{platform_name} — currency: {currency}

Return a JSON object with these keys:
- recommended_rate: string (e.g. "$65/hr" or "$1,200 fixed")
- rate_type: "hourly" or "fixed"
- low_estimate: string — conservative floor rate for this job
- high_estimate: string — premium ceiling rate for this job
- justification: string (2-3 sentences explaining the recommendation)
- negotiation_tips: list of 3 actionable tips for negotiating this rate
- red_flags: list of any pricing red flags spotted in the job post (empty list if none)
- value_adds: list of 2-3 deliverables or extras to justify a higher rate"""


class PricingAnalyst:
    def __init__(self, client: LLMClient):
        self.client = client

    def analyze(
        self,
        analysis: dict,
        market: MarketConfig,
        skills: str = "",
        desired_rate: str = "",
    ) -> dict:
        prompt = PROMPT.format(
            client_needs=", ".join(analysis.get("client_needs", [])),
            required_skills=", ".join(analysis.get("required_skills", [])),
            budget_timeline=analysis.get("budget_timeline", "Not specified"),
            client_tone=analysis.get("tone", "professional"),
            skills=skills or "general freelance skills",
            desired_rate=desired_rate or "market rate",
            platform_name=market.name,
            currency=market.currency,
        )
        response = self.client.complete(
            prompt=prompt,
            system=SYSTEM,
            max_tokens=1024,
            temperature=0.3,
        )
        return parse_llm_json(response)
