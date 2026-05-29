from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator

from config.markets import MarketConfig, get_market
from tools.llm_client import LLMClient, get_client
from agents.analyzer import JobAnalyzer
from agents.proposal_writer import ProposalWriter
from agents.pricing_analyst import PricingAnalyst
from agents.reviewer import ProposalReviewer


@dataclass
class FreelancerProfile:
    name: str = ""
    skills: str = ""
    rate: str = ""


@dataclass
class PipelineResult:
    analysis: dict = field(default_factory=dict)
    pricing: dict = field(default_factory=dict)
    proposal: str = ""
    review: dict = field(default_factory=dict)
    refined_proposal: str = ""

    @property
    def score(self) -> int:
        return self.review.get("score", 0)

    @property
    def final_proposal(self) -> str:
        return self.refined_proposal or self.proposal


StepCallback = Callable[[str, str], None]


class ProposalOrchestrator:
    """Coordinates all agents to produce a reviewed, ready-to-send proposal."""

    def __init__(
        self,
        provider: str = "anthropic",
        client: LLMClient | None = None,
    ):
        self.client = client or get_client(provider)
        self._analyzer = JobAnalyzer(self.client)
        self._writer = ProposalWriter(self.client)
        self._pricing = PricingAnalyst(self.client)
        self._reviewer = ProposalReviewer(self.client)

    def run(
        self,
        job_post: str,
        platform: str,
        profile: FreelancerProfile,
        on_step: StepCallback | None = None,
        skip_pricing: bool = False,
        skip_review: bool = False,
    ) -> PipelineResult:
        """Run the full pipeline and return a PipelineResult.

        on_step(step_name, status) is called before and after each stage
        so callers can update progress indicators.
        """
        result = PipelineResult()
        market = get_market(platform)

        def notify(step: str, status: str) -> None:
            if on_step:
                on_step(step, status)

        # ── Step 1: Analyze ──────────────────────────────────────────────────
        notify("analyze", "running")
        result.analysis = self._analyzer.analyze(job_post)
        notify("analyze", "done")

        # ── Step 2: Pricing ──────────────────────────────────────────────────
        if not skip_pricing:
            notify("pricing", "running")
            result.pricing = self._pricing.analyze(
                analysis=result.analysis,
                market=market,
                skills=profile.skills,
                desired_rate=profile.rate,
            )
            notify("pricing", "done")

        # ── Step 3: Write ────────────────────────────────────────────────────
        notify("write", "running")
        effective_rate = (
            result.pricing.get("recommended_rate", profile.rate)
            if result.pricing
            else profile.rate
        )
        result.proposal = self._writer.write(
            analysis=result.analysis,
            market=market,
            freelancer_name=profile.name,
            skills=profile.skills,
            rate=effective_rate,
        )
        notify("write", "done")

        # ── Step 4: Review ───────────────────────────────────────────────────
        if not skip_review:
            notify("review", "running")
            result.review = self._reviewer.review(
                proposal=result.proposal,
                analysis=result.analysis,
                market=market,
            )
            result.refined_proposal = result.review.get("refined_proposal", "")
            notify("review", "done")

        return result

    def stream_proposal(
        self,
        job_post: str,
        platform: str,
        profile: FreelancerProfile,
        on_step: StepCallback | None = None,
    ) -> tuple[PipelineResult, Iterator[str]]:
        """Analyze and price first (blocking), then stream the proposal text.

        Returns (partial_result, chunk_iterator). Caller iterates chunks to
        build the proposal string, then calls review() manually if needed.
        """
        result = PipelineResult()
        market = get_market(platform)

        def notify(step: str, status: str) -> None:
            if on_step:
                on_step(step, status)

        notify("analyze", "running")
        result.analysis = self._analyzer.analyze(job_post)
        notify("analyze", "done")

        notify("pricing", "running")
        result.pricing = self._pricing.analyze(
            analysis=result.analysis,
            market=market,
            skills=profile.skills,
            desired_rate=profile.rate,
        )
        notify("pricing", "done")

        effective_rate = result.pricing.get("recommended_rate", profile.rate)

        notify("write", "running")
        raw_chunks = self._writer.stream(
            analysis=result.analysis,
            market=market,
            freelancer_name=profile.name,
            skills=profile.skills,
            rate=effective_rate,
        )

        def _with_done() -> Iterator[str]:
            yield from raw_chunks
            notify("write", "done")

        return result, _with_done()

    def review_proposal(
        self,
        proposal: str,
        analysis: dict,
        platform: str,
    ) -> dict:
        market = get_market(platform)
        return self._reviewer.review(
            proposal=proposal,
            analysis=analysis,
            market=market,
        )
