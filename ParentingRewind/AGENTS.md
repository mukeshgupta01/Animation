# Parenting Rewind project instructions

Before doing project work, read `PROJECT-HANDOFF.md` completely, then inspect the live project state. The handoff is a guide; live files take precedence. Before creating a video, also read `README.md`, `COVERED-TOPICS.md`, and `production-assets/asset-library.json`; search `metadata/` to avoid repeating an active or historical topic. Rebuild the topic index with `scripts/update_covered_topics.py` after adding metadata.

## Asset reuse comes first

- Do not call an image-generation tool until the local asset library has been checked.
- Reuse existing characters, locations and suitable scene panels whenever they accurately support the new lesson.
- Reframe existing panels with different crops, slow pans, zooms, color treatments, overlays and captions in local code; these operations do not require a new generated image.
- Reusing a brand intro, outro, character or setting is encouraged.
- Do not reuse the complete scene sequence of an earlier video with only a new title or narration.
- Consecutive episodes must not have the same panel order.
- Every episode still needs a distinct situation, evidence-based lesson, script, narration, captions, title and description.
- Generate a new storyboard only when the library cannot supply the scene beats required to communicate the lesson clearly.
- When a new asset is generated, save it under `production-assets`, add it to `asset-library.json`, and describe its permitted topics and panels.
- After completing an episode, increment the relevant panel `published_uses` values in the asset library. A local draft does not count as published.

## Safety and isolation

- This project targets adults and parents. Do not make it look child-directed.
- Present general parenting education, not personalised therapy, diagnosis or medical advice.
- Research lesson claims using authoritative sources and record the sources in metadata.
- Never reuse Tiny Tales OAuth files, tokens, channel locks, upload ledgers, archives or Scheduled Tasks.
- No upload is authorized unless this project later receives its own verified channel identity and the user explicitly approves it.

## Batch authorization

- On 2026-08-22 the user approved unrestricted local batch production after approving the existing videos. Produce as many complete, validated videos as practical, targeting 50 or more; do not impose an artificial episode limit.
- This authorization covers normal in-scope research, creative decisions, local image generation, narration, rendering, validation and routine failure recovery without further confirmation.
- It does not authorize uploads, publication, emails, external scheduling, OAuth changes or copying anything between projects.
- Checkpoint progress frequently because a Codex account may run out of credit: after every small production interval, keep durable rules current here and record exact changing status, completed episode ranges, failures and resume commands in `PROJECT-HANDOFF.md`.
- Do not upload or create Scheduled Tasks until this project has a separate channel, a matching immutable channel-ID lock and explicit user approval.
- STOP OVERRIDE (2026-08-23): the user rejected the authorized batch renderer because its characters and visuals looked the same across videos. Do not resume `scripts/produce_authorized_batch.py` or generate more videos from its three-storyboard rotation. Before any further batch, create genuinely varied visual assets and obtain approval of one new representative video.
- UPDATED REUSE APPROVAL (2026-08-23): after approving the redesigned direction, the user explicitly said visuals may be recycled. Reuse is allowed in small, non-consecutive doses; do not return to long runs dominated by the same three storyboard families. Vary panel order, crop, pacing, lesson and narration, and keep adding new casts/settings between reuse intervals.

## Quality gate

- Treat V2 as the current voice/content baseline and V4 as the latest music-level review candidate until the user records a different preference.
- Before batching a format, obtain user approval of one representative finished video.
- Validate each finished video proportionately: playable file, expected duration, vertical resolution, audio stream, narration intelligibility, captions and metadata.
- Do not count a draft, failed render or technically invalid MP4 as completed.

## Inclusive visual casting

- When episodes have substantially different subject matter and call for new people or a new family, vary the apparent ethnic and cultural backgrounds represented across episodes instead of defaulting to the same-looking cast.
- Vary mothers, fathers and other appropriate caregivers; vary child age and gender to fit each scenario; and vary homes, rooms and public backgrounds across the batch.
- Avoid a repetitive feed: rotate casts, settings, panel order, crops, motion, emotional pacing and lesson structure so viewers do not feel they are watching the same video repeatedly.
- Keep every portrayal natural, respectful and contemporary. Do not use caricatures, costumes, tokenism or visual stereotypes to signal nationality.
- Describe visible appearance and family context in generation prompts rather than asserting an exact nationality that cannot be established from appearance alone.
- Continuity takes priority within an episode: the same character must retain a consistent face, age and appearance across all of that episode's scenes.

## Keep the account handoff current

- After any material change to outputs, preferred versions, assets, scripts, metadata, channel identity, OAuth status, upload state, email automation or Scheduled Tasks, update `PROJECT-HANDOFF.md` before finishing the task.
- Update its `Last updated` date and next actions, and make sure `CONTINUE-IN-NEW-CODEX.txt` still points to the correct files.
- Keep instructions concise. Put durable rules in this file and changing status/details in `PROJECT-HANDOFF.md`.
- Never place OAuth secrets, tokens, passwords or other credential values in either handoff file.

## Finished-video transfer

- On this computer, every newly completed and validated redesigned episode must be copied to the OneDrive for Business destination configured in `transfer-config.json`.
- Keep the local `output` copy; the OneDrive operation is a verified mirror, not a destructive move.
- Never silently overwrite a different destination file. The shared producer verifies size and SHA-256 before accepting an existing or newly copied file.
