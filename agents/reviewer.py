from __future__ import annotations

from config.markets import MarketConfig
from tools.llm_client import LLMClient
from utils.json_utils import parse_llm_json

SYSTEM = """You are a senior freelance coach who has reviewed thousands of proposals across all major platforms.
You give brutally honest, specific feedback — no sugarcoating, no generic advice.
You always rewrite weak proposals into stronger ones.
Always respond with valid JSON only — no markdown, no explanation."""

PROMPT = """Review this freelance proposal and return a detailed critique.

=== CONTEXT ===
Platform: {platform_name}
Expected tone: {tone}
Client needs: {client_needs}
Key selling points that should appear: {key_selling_points}

=== PROPOSAL ===
{proposal}

Return a JSON object with these keys:
- score: integer 1-10 (10 = send immediately, 1 = start over)
- verdict: string — one sentence summary of the proposal's overall quality
- strengths: list of 2-4 specific things that work well (quote from the proposal where possible)
- improvements: list of 2-4 specific, actionable improvements with examples
- missing_elements: list of any required selling points or sections that are absent
- tone_match: boolean — true if the tone matches the platform expectation
- refined_proposal: a fully rewritten, improved version that addresses all improvements"""


class ProposalReviewer:
    def __init__(self, client: LLMClient):
        self.client = client

    def review(
        self,
        proposal: str,
        analysis: dict,
        market: MarketConfig,
    ) -> dict:
        prompt = PROMPT.format(
            platform_name=market.name,
            tone=market.tone,
            client_needs=", ".join(analysis.get("client_needs", [])),
            key_selling_points=", ".join(analysis.get("key_selling_points", [])),
            proposal=proposal,
        )
        response = self.client.complete(
            prompt=prompt,
            system=SYSTEM,
            max_tokens=2048,
            temperature=0.3,
        )
        return parse_llm_json(response)
