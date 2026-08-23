# Tiny Tales project instructions

Before changing or running this project, read `PROJECT-HANDOFF.md` completely and then inspect the live runtime state. The handoff is a guide; local manifests, ledgers, task status, logs, and files are the source of truth when they are newer. Before creating a new concept, read `COVERED-TOPICS.md` and rebuild it with `automation/update_covered_topics.py` after new metadata or completed media is added.

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

## Latest completed checkpoint (2026-08-23 17:14 Australia/Sydney)

- `Bea's Healthy Habits Treasure Trail` is complete at 365.133333 seconds (6:05), with a new independently moving bee mascot rather than Pip or an animal-card quiz. The output ID is `beas-healthy-habits-trail-01`.
- Its five accepted built-in image-generation backgrounds are `automation/production-assets/healthy-habits-*.png`: handwashing garden, toothbrushing cove, colourful-food picnic, movement playground, and sleep bedroom. Do not regenerate or overwrite them without a concrete defect.
- The resumable producer is `automation/production/produce_bea_healthy_habits.py`. Use `C:\Animation\Animation\.venv\Scripts\python.exe`; the bare Windows `python` command resolves to an inactive Microsoft Store alias.
- The video passed its automated quality gate, five response gaps over five seconds, 1080p H.264/stereo AAC checks, full FFmpeg decode, and visual contact-sheet review. It is collision-safely queued with private/made-for-kids metadata.
- Live channel verification immediately before queueing returned Tiny Tales and immutable channel ID `UCEn9N-ITQHshjgt6fy7fxnw`. The pending folder now contains 36 MP4s; the immediate dry run found 35 age-eligible and still selected `jungle-animal-clue-detectives-01.mp4` next. `COVERED-TOPICS.md` records 45 concepts.
- Both Scheduled Tasks were Ready when checked at 16:54. Next runs were generation at 20:05 and private upload at 20:20. The 16:20 upload had failed with YouTube daily upload-quota HTTP 429 and preserved the queue item; do not bypass or duplicate that upload.
- This checkpoint is committed and pushed in the same production interval. A new account must still verify a clean worktree and zero divergence from `origin/main` before starting the next concept. Choose a different topic and visual system; do not turn Pip or Bea into a repetitive fixed-location template.

## User-requested pause (2026-08-23 17:27 Australia/Sydney)

- The user asked to stop creating videos so they can change Codex accounts first. Do not resume generation or start a renderer until the user explicitly asks the new account to continue.
- The briefly proposed `Rory's Eight-Planet Postcard Adventure` was stopped before a producer, metadata file, rendered video, or queue entry was created. It is not a completed or covered topic.
- Three preview-only built-in image generations for Mercury, Venus, and Earth were made under Codex's default generated-images directory but were not copied into this workspace or consumed by project code. A future account should begin from live project state and may redesign or discard that proposal.
- No Python or FFmpeg process was active when this pause was recorded. The latest completed video remains `Bea's Healthy Habits Treasure Trail`; the completed checkpoint immediately above is authoritative.
- `Tiny Tales - Continuous Generation` was disabled after the stop request so its 20:05 trigger cannot create another video. The separate `Tiny Tales - Daily Private Upload` task remains Ready for the already-approved four-hour private queue cadence. Re-enable generation only after a new explicit user instruction.
