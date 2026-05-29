import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Freelance Proposal Agent",
    page_icon="📝",
    layout="wide",
)

from config.markets import MARKETS
from agents.orchestrator import ProposalOrchestrator, FreelancerProfile
from utils.exporter import export_proposal


def init_session_state():
    defaults = {
        "analysis": None,
        "pricing": None,
        "proposal": None,
        "review": None,
        "step": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset():
    for key in ["analysis", "pricing", "proposal", "review"]:
        st.session_state[key] = None
    st.session_state.step = 0


def make_orchestrator(provider: str) -> ProposalOrchestrator:
    return ProposalOrchestrator(provider=provider)


def main():
    init_session_state()

    st.title("📝 Freelance Proposal Agent")
    st.caption("AI-powered proposals tailored to your target platform.")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Settings")

        provider = st.selectbox("LLM Provider", options=["anthropic", "groq"], index=0)
        platform = st.selectbox(
            "Target Platform",
            options=list(MARKETS.keys()),
            format_func=lambda k: MARKETS[k].name,
        )
        skip_pricing = st.checkbox("Skip pricing analysis", value=False)
        skip_review = st.checkbox("Skip review & refine", value=False)

        st.divider()
        st.subheader("Your Profile")
        freelancer_name = st.text_input("Your Name", placeholder="Jane Doe")
        skills = st.text_area(
            "Skills & Experience",
            placeholder="5 years React/Node.js, built 20+ SaaS products, ...",
            height=120,
        )
        hourly_rate = st.text_input("Rate / Budget", placeholder="$50/hr or $500 fixed")

        st.divider()
        if st.button("🔄 Start Over", use_container_width=True):
            reset()
            st.rerun()

    # ── Job Input ─────────────────────────────────────────────────────────────
    job_post = st.text_area(
        "Paste the Job Posting",
        placeholder="Paste the full job description here...",
        height=200,
    )

    profile = FreelancerProfile(
        name=freelancer_name,
        skills=skills,
        rate=hourly_rate,
    )

    # ── Run Pipeline ──────────────────────────────────────────────────────────
    if st.button(
        "🚀 Generate Proposal",
        use_container_width=True,
        disabled=not job_post,
        type="primary",
    ):
        orchestrator = make_orchestrator(provider)

        status_area = st.empty()
        progress = st.progress(0)

        steps = ["analyze", "pricing", "write", "review"]
        active_steps = [s for s in steps if not (
            (s == "pricing" and skip_pricing) or (s == "review" and skip_review)
        )]
        step_count = len(active_steps)
        step_index = [0]

        def on_step(step: str, status: str) -> None:
            if status == "running":
                labels = {
                    "analyze": "Analyzing job posting...",
                    "pricing": "Analyzing pricing...",
                    "write": "Writing proposal...",
                    "review": "Reviewing & refining...",
                }
                status_area.info(labels.get(step, f"{step}..."))
            elif status == "done":
                step_index[0] += 1
                progress.progress(step_index[0] / step_count)

        try:
            result = orchestrator.run(
                job_post=job_post,
                platform=platform,
                profile=profile,
                on_step=on_step,
                skip_pricing=skip_pricing,
                skip_review=skip_review,
            )
            st.session_state.analysis = result.analysis
            st.session_state.pricing = result.pricing
            st.session_state.proposal = result.proposal
            st.session_state.review = result.review
            st.session_state.step = 3 if not skip_review else (2 if not skip_pricing else 1)
            status_area.success("Done!")
            progress.progress(1.0)
        except Exception as e:
            status_area.error(f"Pipeline failed: {e}")
            progress.empty()

    st.divider()

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.analysis:
        with st.expander("🔍 Job Analysis", expanded=st.session_state.step == 1):
            a = st.session_state.analysis
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Client Needs**")
                for need in a.get("client_needs", []):
                    st.markdown(f"- {need}")
                st.markdown("**Required Skills**")
                for skill in a.get("required_skills", []):
                    st.markdown(f"- {skill}")
            with col_b:
                st.markdown("**Budget / Timeline**")
                st.info(a.get("budget_timeline", "Not specified"))
                st.markdown("**Tone**")
                st.info(a.get("tone", "Professional"))
                st.markdown("**Key Selling Points**")
                for point in a.get("key_selling_points", []):
                    st.markdown(f"- {point}")

    if st.session_state.pricing:
        with st.expander("💰 Pricing Analysis", expanded=False):
            p = st.session_state.pricing
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("Recommended Rate", p.get("recommended_rate", "—"))
            with col_p2:
                st.metric("Low Estimate", p.get("low_estimate", "—"))
            with col_p3:
                st.metric("High Estimate", p.get("high_estimate", "—"))

            st.markdown("**Justification**")
            st.write(p.get("justification", ""))

            col_p4, col_p5 = st.columns(2)
            with col_p4:
                if p.get("negotiation_tips"):
                    st.markdown("**Negotiation Tips**")
                    for tip in p["negotiation_tips"]:
                        st.markdown(f"- {tip}")
                if p.get("value_adds"):
                    st.markdown("**Value-Adds to Justify Higher Rate**")
                    for va in p["value_adds"]:
                        st.markdown(f"- {va}")
            with col_p5:
                if p.get("red_flags"):
                    st.markdown("**Red Flags**")
                    for flag in p["red_flags"]:
                        st.warning(flag)

    if st.session_state.proposal:
        with st.expander("✍️ Generated Proposal", expanded=st.session_state.step == 2):
            proposal_text = st.text_area(
                "Edit your proposal:",
                value=st.session_state.proposal,
                height=400,
                key="proposal_editor",
            )
            st.session_state.proposal = proposal_text

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "⬇️ Download .txt",
                    data=st.session_state.proposal,
                    file_name="proposal.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col_dl2:
                docx_bytes = export_proposal(st.session_state.proposal, fmt="docx")
                if docx_bytes:
                    st.download_button(
                        "⬇️ Download .docx",
                        data=docx_bytes,
                        file_name="proposal.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

    if st.session_state.review:
        with st.expander("✅ Review & Suggestions", expanded=st.session_state.step == 3):
            r = st.session_state.review
            score = r.get("score", 0)

            col_rv1, col_rv2 = st.columns([1, 3])
            with col_rv1:
                st.metric("Score", f"{score}/10")
                st.progress(score / 10)
            with col_rv2:
                st.markdown("**Verdict**")
                st.write(r.get("verdict", ""))

            col_rv3, col_rv4 = st.columns(2)
            with col_rv3:
                st.markdown("**Strengths**")
                for s in r.get("strengths", []):
                    st.success(s)
            with col_rv4:
                st.markdown("**Improvements**")
                for i in r.get("improvements", []):
                    st.warning(i)
                if r.get("missing_elements"):
                    st.markdown("**Missing Elements**")
                    for m in r["missing_elements"]:
                        st.error(m)

            if r.get("refined_proposal"):
                st.markdown("**Refined Proposal**")
                refined = st.text_area(
                    "Refined version:",
                    value=r["refined_proposal"],
                    height=400,
                    key="refined_editor",
                )
                col_dl3, col_dl4 = st.columns(2)
                with col_dl3:
                    st.download_button(
                        "⬇️ Download Refined .txt",
                        data=refined,
                        file_name="proposal_refined.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with col_dl4:
                    docx_refined = export_proposal(refined, fmt="docx")
                    if docx_refined:
                        st.download_button(
                            "⬇️ Download Refined .docx",
                            data=docx_refined,
                            file_name="proposal_refined.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )


if __name__ == "__main__":
    main()
