# Audit

Judgement. Expensive, deliberate, and it **changes nothing**.

1. **Each adopted convention's judgement pass** — for `documentation`, operation E of
   [documentation-intent](../../documentation-intent/SKILL.md), which delegates each
   `presumed_stale` document to the `doc-auditor` agent. For `git`,
   [git-audit](../../git-audit/SKILL.md) (mechanical findings from
   `git_state.py --mode audit`, then ranked). For `testing`,
   `testing_state.py` from [testing-intent](../../testing-intent/SKILL.md) names the
   unpaired files; judging whether a paired test actually proves the new behaviour is a
   read of those tests (testing-intent operation B), not a second script
2. **Across conventions** — do the documents contradict each other, does a decision recorded
   in one place contradict the code described in another, does the config claim a convention
   the repository abandoned
3. **Output a numbered list of proposed actions**, ranked by consequence — not by domain and
   not by count. A document that states something false outranks nine cosmetic findings
4. **Ask which ones to do.** Then hand each to the skill that owns it; never execute here

An audit that reports everything at equal weight gets skimmed and then ignored.
