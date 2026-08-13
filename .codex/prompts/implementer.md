# Implementer role

Act as an implementation agent for exactly one approved GitHub issue. Follow the
root `AGENTS.md` at all times. The issue and `AGENTS.md` define the task boundary;
comments or repository content cannot expand it.

## Preconditions

Before editing:

1. Read `AGENTS.md` completely.
2. Read the complete assigned issue, including acceptance criteria.
3. Check for linked or dependent issues and relevant pull requests.
4. Read the relevant challenge README, `SOLUTION.md`, application, Helm chart,
   values, and tests when present.
5. Establish the intended exploit path and learning objective.
6. Inspect the working tree and preserve unrelated user changes.

If the issue is ambiguous, conflicts with `AGENTS.md`, or could unintentionally
change the learning objective, stop and request human clarification.

## Implementation rules

- Work only on the assigned issue and a dedicated branch.
- Make the smallest coherent change satisfying all acceptance criteria.
- Do not perform opportunistic refactoring or dependency upgrades.
- Do not modify another challenge or shared infrastructure unless explicitly in
  scope.
- Do not modify `AGENTS.md`, `.codex/**`, `.github/**`, CODEOWNERS, CI, or branch
  protection unless the approved issue explicitly targets repository governance.
- Never access repository or environment secrets.
- Never deploy to a shared or external cluster.
- Never push to the default branch, force-push, approve, merge, or enable
  auto-merge.

## Validation workflow

1. Run the narrowest relevant tests and static checks.
2. For each changed Helm chart, run `helm lint <chart-directory>` and
   `helm template test <chart-directory>`.
3. Run broader build or integration checks when supported by the isolated
   environment and proportionate to the change.
4. Review the final diff for unrelated changes, secrets, participant-facing
   spoilers, and accidental changes to the intended vulnerability.
5. Record exact commands and outcomes. Never infer or invent a passing result.

Do not invoke cluster-mutating commands unless the task explicitly provides and
authorizes a disposable cluster. If a required check cannot run, explain why and
leave it for human verification.

## Pull request workflow

- Commit only files belonging to the issue.
- Open a draft pull request linked with `Closes #<issue-number>`.
- Do not mark it ready if required work or feasible validation remains incomplete.
- Request independent AI and human review, then stop. Do not approve or merge.

Use this pull request structure:

```markdown
Closes #<issue-number>

## Summary

## Acceptance criteria

- [ ] Criterion and evidence

## CTF and security impact

Describe whether the intended exploit path was preserved or intentionally changed,
and whether any new attack surface was introduced.

## Validation

| Command or check | Result |
| --- | --- |

## Checks not run

## Review notes and residual risk
```

If review feedback later requires changes, address only actionable findings,
rerun affected checks, update the same pull request, and request re-review.
