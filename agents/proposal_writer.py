from __future__ import annotations

from config.markets import MarketConfig
from tools.llm_client import LLMClient

SYSTEM = """You are an elite freelance proposal writer with a proven track record across Upwork, Fiverr, Toptal, and LinkedIn.
You craft proposals that feel personal, confident, and laser-focused on the client's specific problem.
Your proposals open with a hook that shows you've read the brief, demonstrate credibility quickly, and close with a clear next step.
Never use filler phrases like "I am writing to express my interest" or "I would be a great fit".
Write like a human expert — direct, warm, and results-oriented."""

PROMPT = """Write a complete freelance proposal for this opportunity.

=== PLATFORM ===
Name: {platform_name}
Expected tone: {tone}
Character limit: {max_length}
Required sections (weave naturally into prose, no headers): {sections}

=== PLATFORM-SPECIFIC TIPS ===
{tips}

=== JOB ANALYSIS ===
Client needs: {client_needs}
Required skills: {required_skills}
Budget / timeline: {budget_timeline}
Client tone: {client_tone}
Key selling points to highlight: {key_selling_points}

=== FREELANCER PROFILE ===
Name: {name}
Skills & experience: {skills}
Rate: {rate}

=== INSTRUCTIONS ===
- Open with a hook that references something specific from the job post
- Show you understand the client's core problem, not just the task
- Weave in 1-2 concrete examples or results from past work
- Keep sentences short and punchy
- End with one clear call to action
- Stay within the character limit
- Output only the proposal text — no labels, no headers, no explanation"""


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
            client_tone=analysis.get("tone", "professional"),
            key_selling_points=", ".join(analysis.get("key_selling_points", [])),
            name=freelancer_name or "the freelancer",
            skills=skills or "relevant experience",
            rate=rate or "competitive rate",
        )
        return self.client.complete(
            prompt=prompt,
            system=SYSTEM,
            max_tokens=max(512, market.max_proposal_length // 3),
            temperature=0.75,
        )

    def stream(
        self,
        analysis: dict,
        market: MarketConfig,
        freelancer_name: str = "",
        skills: str = "",
        rate: str = "",
    ):
        """Yields proposal text in chunks for live display."""
        prompt = PROMPT.format(
            platform_name=market.name,
            tone=market.tone,
            max_length=market.max_proposal_length,
            sections=", ".join(market.key_sections),
            tips="\n".join(f"- {t}" for t in market.tips),
            client_needs=", ".join(analysis.get("client_needs", [])),
            required_skills=", ".join(analysis.get("required_skills", [])),
            budget_timeline=analysis.get("budget_timeline", "Not specified"),
            client_tone=analysis.get("tone", "professional"),
            key_selling_points=", ".join(analysis.get("key_selling_points", [])),
            name=freelancer_name or "the freelancer",
            skills=skills or "relevant experience",
            rate=rate or "competitive rate",
        )
        yield from self.client.stream(
            prompt=prompt,
            system=SYSTEM,
            max_tokens=max(512, market.max_proposal_length // 3),
            temperature=0.75,
        )
