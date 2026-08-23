# Workspace instructions

This workspace contains two separate video projects. Keep their files, credentials, channel identities, upload histories, archives, reports and Scheduled Tasks isolated.

## Project routing

- `KidsRhymes` is the Tiny Tales children's-video project. Before working there, read `KidsRhymes/AGENTS.md` and `KidsRhymes/PROJECT-HANDOFF.md` if present.
- `ParentingRewind` is the adult-facing parenting education project. Before working there, read `ParentingRewind/AGENTS.md` and `ParentingRewind/PROJECT-HANDOFF.md`.
- When the user says "the new channel" or "Parenting Rewind," work only under `ParentingRewind` unless the user explicitly expands the scope.

## Workspace safety

- Before starting new workspace changes, run `git pull --ff-only origin main` from the workspace root and reconcile any incoming instructions or live-state updates before continuing. If the worktree is not clean or the pull cannot fast-forward, stop and inspect rather than forcing or discarding changes.
- Inspect live files and state before changing anything; handoff documents are guides and may become outdated.
- Preserve existing videos, manifests, metadata, credentials, Scheduled Tasks and user changes unless the user explicitly authorizes a verified change.
- Never copy or reuse OAuth client secrets, tokens, channel locks, upload ledgers or archives between projects, laptops or channels.
- Each YouTube channel automation must use its documented dedicated Google Cloud/OAuth project. Never create or rotate projects merely to evade YouTube quota; project separation is for credential and operational isolation, and channel-level upload limits still apply.
- Never print or place secrets or tokens in instructions, handoffs, logs or source control.
- Do not upload, publish, email, schedule, or mass-generate content without the authorization recorded in the applicable project instructions and confirmed by live state.
- After a material project change, update that project's handoff in the same task so a fresh Codex session receives the current state. Record paths and status, never secret values.
- Keep the applicable `AGENTS.md` current when user preferences, safety rules, automation behavior, or continuation requirements materially change. Update only the project in scope unless the instruction applies workspace-wide.
- If an instruction or handoff appears stale or conflicts with live state, stop the affected external action, reconcile the discrepancy safely and update the documentation.
- If an upload process exits after sending data but before recording a video ID, perform a read-only channel query for the exact title before any retry. Reconcile a confirmed upload into the local ledger; never risk a duplicate upload.

## Repository synchronization

- The user authorized automatic Git synchronization for this `Animation` repository every three hours so Parenting Rewind work from this computer and other-project work from another computer remain shared.
- The scheduled sync may fetch, fast-forward a clean `main`, and push reviewed commits. It must never auto-commit, force-push, reset, discard files, auto-resolve a divergence, or pull into a dirty worktree.
- When the worktree is dirty, fetch only and leave the user's files untouched. When local and remote have diverged, log the state and leave reconciliation to an interactive reviewed session.
- The task is `Animation Git Sync Every Three Hours`; its reviewed scripts are `automation/Run-GitSync.ps1` and `automation/Install-GitSyncTask.ps1`. Runtime logs belong under ignored `runtime/`.
