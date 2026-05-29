from dataclasses import dataclass, field


@dataclass
class MarketConfig:
    name: str
    platform: str
    max_proposal_length: int
    tone: str
    key_sections: list[str]
    tips: list[str]
    currency: str = "USD"


MARKETS: dict[str, MarketConfig] = {
    "upwork": MarketConfig(
        name="Upwork",
        platform="upwork",
        max_proposal_length=5000,
        tone="professional and results-driven",
        key_sections=[
            "hook",
            "relevant_experience",
            "approach",
            "timeline",
            "call_to_action",
        ],
        tips=[
            "Address the client by name if available",
            "Reference specific details from the job post",
            "Include relevant portfolio links",
            "State your rate clearly",
            "Keep it under 300 words for better response rates",
        ],
    ),
    "fiverr": MarketConfig(
        name="Fiverr",
        platform="fiverr",
        max_proposal_length=1200,
        tone="friendly and service-oriented",
        key_sections=[
            "hook",
            "what_you_offer",
            "delivery_promise",
            "call_to_action",
        ],
        tips=[
            "Lead with what the buyer gets, not your credentials",
            "Mention delivery time upfront",
            "Keep it short and punchy",
            "End with a question to encourage reply",
        ],
    ),
    "freelancer": MarketConfig(
        name="Freelancer.com",
        platform="freelancer",
        max_proposal_length=3000,
        tone="confident and solution-focused",
        key_sections=[
            "hook",
            "understanding_of_project",
            "proposed_solution",
            "experience",
            "bid_justification",
            "call_to_action",
        ],
        tips=[
            "Show you've read and understood the project brief",
            "Justify your bid with value, not just hours",
            "Mention past similar projects",
            "Be specific about milestones",
        ],
    ),
    "toptal": MarketConfig(
        name="Toptal",
        platform="toptal",
        max_proposal_length=2000,
        tone="expert and highly technical",
        key_sections=[
            "technical_fit",
            "relevant_experience",
            "approach",
            "availability",
        ],
        tips=[
            "Emphasize depth of expertise and seniority",
            "Reference specific technologies mentioned",
            "Be precise about availability and timezone",
            "Quantify past impact with metrics",
        ],
    ),
    "linkedin": MarketConfig(
        name="LinkedIn",
        platform="linkedin",
        max_proposal_length=2000,
        tone="professional and relationship-focused",
        key_sections=[
            "connection_opener",
            "value_proposition",
            "relevant_background",
            "next_step",
        ],
        tips=[
            "Mention any mutual connections or shared interests",
            "Focus on long-term value and partnership",
            "Keep the first message brief — save detail for the follow-up",
            "End with a low-friction ask (a call, not a commitment)",
        ],
    ),
}

DEFAULT_MARKET = "upwork"


def get_market(platform: str) -> MarketConfig:
    key = platform.lower().strip()
    if key not in MARKETS:
        raise ValueError(f"Unknown market '{platform}'. Available: {list(MARKETS.keys())}")
    return MARKETS[key]
