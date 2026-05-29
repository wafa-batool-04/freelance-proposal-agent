from __future__ import annotations

from config.markets import MarketConfig
from tools.llm_client import LLMClient

SYSTEM = """You are an expert freelance proposal writer with a 95% win rate.
You write compelling, personalized proposals that get responses.
Write in a natural human tone — never robotic or generic."""

PROMPT = """Write a freelance proposal for the following job.

Platform: {platform_name}
Tone: {tone}
Max length: {max_length} characters
Required sections: {sections}

Platform tips:
{tips}

Job analysis:
- Client needs: {client_needs}
- Required skills: {required_skills}
- Budget/timeline: {budget_timeline}
- Key selling points to highlight: {key_selling_points}

Freelancer profile:
- Name: {name}
- Skills & experience: {skills}
- Rate: {rate}

Write the full proposal now. Do not include section headers — write it as flowing, natural prose."""


class ProposalWriter:
    def __init__(self, client: LLMClient):
        self.client = client

    def write(
        self,
        analysis: dict,
        market: MarketConfig,
        freelancer_name: str = "",
        skills: str = "",
        rate: str = "",
    ) -> str:
        prompt = PROMPT.format(
            platform_name=market.name,
            tone=market.tone,
            max_length=market.max_proposal_length,
            sections=", ".join(market.key_sections),
            tips="\n".join(f"- {t}" for t in market.tips),
            client_needs=", ".join(analysis.get("client_needs", [])),
            required_skills=", ".join(analysis.get("required_skills", [])),
            budget_timeline=analysis.get("budget_timeline", "Not specified"),
            key_selling_points=", ".join(analysis.get("key_selling_points", [])),
            name=freelancer_name or "the freelancer",
            skills=skills or "relevant experience",
            rate=rate or "competitive rate",
        )
        return self.client.complete(
            prompt=prompt,
            system=SYSTEM,
            max_tokens=market.max_proposal_length // 3,
            temperature=0.75,
        )
