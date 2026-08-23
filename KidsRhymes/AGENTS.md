# Tiny Tales project instructions

Before changing or running this project, read `PROJECT-HANDOFF.md` completely and then inspect the live runtime state. The handoff is a guide; local manifests, ledgers, task status, logs, and files are the source of truth when they are newer.

Safety requirements:

- Never expose, copy, replace, or commit OAuth credentials or tokens.
- Never reuse this project's token or channel lock for another channel or laptop.
- Verify the immutable channel ID before every real upload.
- Upload only as private and made for kids.
- A real upload requires the existing explicit confirmation flag.
- Never regenerate a completed item or upload an archived/existing video again.
- Archive only after YouTube returns a video ID.
- Do not delete user files, old output folders, credentials, manifests, ledgers, archives, or Scheduled Tasks without inspecting and verifying the exact target.
- Keep generation independent from uploading: an upload or email failure must not stop future generation cycles.
- Preserve the editorial rules and user preferences recorded in `PROJECT-HANDOFF.md`.
- The animal-shadow guessing format was retired by the user on 2026-08-23. Preserve historical outputs, but do not render, queue, upload or schedule any new shadow-format video.

At the beginning of a continuation, report the verified live state and any difference from the handoff before making material changes.
