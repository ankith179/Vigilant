# Independent review still required

The current handoff bundle has a detailed reviewer procedure and agreement
summarizer in `docs/REVIEWER_WORKFLOW.md` and
`scripts/summarize_reviewer_agreement.py`. The existing 32-case pilot is
development material only; use neither it nor its reviewers to claim the
independent 95% gate has passed.

The project does not claim semantic grounding or hallucination accuracy from
schema checks. The ablation summarizer generates `reports/ablation/review-packets.json`
with actual prompts, evidence and model outputs, alongside blank review fields.
The separate `review-key.json` maps observations to variants and authored labels.
No independent reviewer has filled or approved these materials.

Give the packets to a reviewer without the key where practical. A packet omits the
variant name and expected label, although prompt content can reveal which evidence
is available. This is reduced label exposure, not guaranteed experimental blinding.

For each observation, record whether the supplied evidence is sufficient to decide,
whether it entails the validated decision, and whether the model makes an unsupported
claim. Record the reviewer's status and a short evidence-based rationale. Leave a
field unknown when it cannot be assessed. Do not infer semantic correctness from
an exact quote, valid JSON, a confidence value or a citation identifier alone.

Review scenario ground truth separately using the baseline and changed repository
versions. Establish complete relevant affected-artifact sets before reporting impact
precision or false-positive rates. Seeded baseline traces and correlated mutations
must stay explicit. Independent reviewers should not simply copy authored labels.

Prefer two reviewers, a recorded agreement measure and a documented disagreement
resolution process before publication. This is a proposed procedure; no agreement
score, reviewed label set, plagiarism result or external approval is claimed.
