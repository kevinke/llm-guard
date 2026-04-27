# Git Workflow For This Fork

This repository is used as a downstream fork with local development against both the original upstream project and the fork's own mainline.

## Branch Roles

- Local `main` tracks `upstream/main` and must stay as a clean upstream mirror.
- Local `fork-main` tracks `origin/main` and is the downstream integration branch for this fork.
- Feature branches should be created from `fork-main` and pushed to `origin/<feature-branch>`.

## Agent Rules

- Do not repoint local `main` away from `upstream/main`.
- Do not merge downstream feature work into local `main`.
- When the user wants to ship fork-specific work, merge it into `fork-main`, then push `fork-main` to `origin/main`.
- When the user wants the latest upstream changes, update local `main` from `upstream/main` first.
- If downstream needs upstream changes, bring them into `fork-main` explicitly after updating local `main`.

## Preferred Daily Flow

1. Update upstream mirror:
   - `git switch main`
   - `git fetch upstream`
   - `git pull --ff-only`
2. Update downstream integration branch:
   - `git switch fork-main`
   - `git fetch origin`
   - `git pull --ff-only`
3. Start new work from downstream mainline:
   - `git switch fork-main`
   - `git switch -c <feature-branch>`
4. Land fork-specific work:
   - merge the feature branch into `fork-main`
   - push `fork-main` to `origin/main`

## Interpretation Notes

- If the user says "merge to main" in this fork, prefer merging into `fork-main` and then updating `origin/main`, unless the user explicitly says to change the local upstream mirror workflow.
- Before changing remotes or branch tracking, verify state with `git remote -v` and `git branch -vv`.