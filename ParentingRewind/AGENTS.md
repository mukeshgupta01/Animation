# Parenting Rewind project instructions

Before doing project work, read `PROJECT-HANDOFF.md` completely, then inspect the live project state. The handoff is a guide; live files take precedence. Before creating a video, also read `README.md`, `COVERED-TOPICS.md`, and `production-assets/asset-library.json`; search `metadata/` to avoid repeating an active or historical topic. Rebuild the topic index with `scripts/update_covered_topics.py` after adding metadata.

## Asset reuse comes first

- CURRENT IMAGE METHOD (2026-08-23 21:44): the user rejected the free local ComfyUI/SDXL visual trial as poor quality and explicitly asked to continue with Codex image generation instead. Do not preserve a preference for free local image agents. Use the built-in image-generation workflow when a genuinely new storyboard is needed, while still applying the asset audit and credit-conservation rules below.

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
- Parenting Rewind uses its own dedicated Google Cloud/OAuth project. Confirm the non-secret project ID and current verification status in `PROJECT-HANDOFF.md`; never copy Birthday Songs credentials into this project.
- Never upload outside this project's verified, fail-closed Parenting Rewind automation. Upload authority exists only when the current `PROJECT-HANDOFF.md` records the verified channel identity, immutable channel lock and the user's explicit authorization; never infer it from local credentials alone.
- If a resumable upload is interrupted or its wrapper reports failure after transfer begins, query the verified channel read-only for the exact metadata title before retrying. If YouTube already created the video, reconcile its ID into the attempt journal and ledger. Do not upload a duplicate.

## Batch authorization

- On 2026-08-22 the user approved unrestricted local batch production after approving the existing videos. Produce as many complete, validated videos as practical, targeting 50 or more; do not impose an artificial episode limit.
- USER RECONFIRMATION (2026-08-24): continue producing small, varied Parenting Rewind video intervals under this open-ended authorization, using the approved Codex image-generation workflow when audited assets cannot communicate the new lesson.
- This authorization covers normal in-scope research, creative decisions, local image generation, narration, rendering, validation and routine failure recovery without further confirmation.
- This local-production authorization does not by itself authorize uploads, publication, emails, external scheduling or OAuth changes. Treat any separately granted automation authority exactly as recorded in the current handoff.
- Checkpoint progress frequently because a Codex account may run out of credit: after every small production interval, keep durable rules current here and record exact changing status, completed episode ranges, failures and resume commands in `PROJECT-HANDOFF.md`.
- Do not create or change upload Scheduled Tasks unless the handoff confirms a separate channel, matching immutable channel-ID lock and explicit user approval.
- PUBLIC UPLOAD OVERRIDE (2026-08-26 20:55): the user superseded the five-hour cadence. Upload the oldest remaining episode first as `public`, one video every two hours through `2026-08-28T10:55:10Z`, then one every four hours, always on immutable channel `UCGb-IUQX2KQa_KA24MwE_aQ` and always `made_for_kids=false`. Windows task `Parenting Rewind - Public Upload Cadence` checks every two hours; after the temporary period the uploader's four-hour gate skips alternating checks. The old private and superseded five-hour tasks must remain disabled. Preserve fail-closed channel, metadata, FFprobe, hash and duplicate checks.
- STOP OVERRIDE (2026-08-23): the user rejected the authorized batch renderer because its characters and visuals looked the same across videos. Do not resume `scripts/produce_authorized_batch.py` or generate more videos from its three-storyboard rotation. Before any further batch, create genuinely varied visual assets and obtain approval of one new representative video.
- UPDATED REUSE APPROVAL (2026-08-23): after approving the redesigned direction, the user explicitly said visuals may be recycled. Reuse is allowed in small, non-consecutive doses; do not return to long runs dominated by the same three storyboard families. Vary panel order, crop, pacing, lesson and narration, and keep adding new casts/settings between reuse intervals.

## Quality gate

- Treat V2 as the current voice/content baseline and V4 as the latest music-level review candidate until the user records a different preference.
- Before batching a format, obtain user approval of one representative finished video.
- Validate each finished video proportionately: playable file, expected duration, vertical resolution, audio stream, narration intelligibility, captions and metadata.
- Do not count a draft, failed render or technically invalid MP4 as completed.
- For every newly produced episode after 2026-08-23 17:33, end the spoken narration with a brief adult-facing request to like and subscribe for more practical Parenting Rewind videos. Include it in burned-in captions and place it after the educational takeaway; do not interrupt or weaken the lesson.

## Inclusive visual casting

- When episodes have substantially different subject matter and call for new people or a new family, vary the apparent ethnic and cultural backgrounds represented across episodes instead of defaulting to the same-looking cast.
- Vary mothers, fathers and other appropriate caregivers; vary child age and gender to fit each scenario; and vary homes, rooms and public backgrounds across the batch.
- Avoid a repetitive feed: rotate casts, settings, panel order, crops, motion, emotional pacing and lesson structure so viewers do not feel they are watching the same video repeatedly.
- Keep every portrayal natural, respectful and contemporary. Do not use caricatures, costumes, tokenism or visual stereotypes to signal nationality.
- Describe visible appearance and family context in generation prompts rather than asserting an exact nationality that cannot be established from appearance alone.
- Continuity takes priority within an episode: the same character must retain a consistent face, age and appearance across all of that episode's scenes.
- Cover the full parenting age range rather than concentrating only on young school-age children. Deliberately include toddlers/preschoolers (roughly 2-4), school-age children (roughly 5-12), and teenagers (roughly 13-18) across future production intervals.
- For a rolling group of about ten new episodes, normally include at least two toddler/preschool topics and at least two teenage topics, unless the topic audit shows a stronger reason to adjust the mix.
- Make situations developmentally appropriate. Toddler topics may include transitions, biting/hitting, sleep, toilet-learning stress, separation and limited language. Teenage topics may include privacy, independence, phones/social media, school pressure, friendship conflict, curfews, driving, chores and respectful disagreement.
- Keep the audience adult-facing at every age. Do not infantilize teenagers, portray normal adolescent independence as pathology, or present toddler behaviour as deliberate adult-like manipulation.

## Keep the account handoff current

- At the end of every Parenting Rewind task, review the user's newest instructions. Add any durable workflow, creative, upload, notification, safety or continuity rule to this `AGENTS.md` in the same checkpoint instead of leaving it only in chat history.
- Keep `AGENTS.md` synchronized with the latest explicit user direction. When a new instruction supersedes an older one, label or replace the obsolete rule clearly so a fresh session cannot follow both.
- After any material change to outputs, preferred versions, assets, scripts, metadata, channel identity, OAuth status, upload state, email automation or Scheduled Tasks, update `PROJECT-HANDOFF.md` before finishing the task.
- Update its `Last updated` date and next actions, and make sure `CONTINUE-IN-NEW-CODEX.txt` still points to the correct files.
- Keep instructions concise. Put durable rules in this file and changing status/details in `PROJECT-HANDOFF.md`.
- Never place OAuth secrets, tokens, passwords or other credential values in either handoff file.
- A fresh Codex account or session must be able to resume without this chat history. `CONTINUE-IN-NEW-CODEX.txt` must use the current absolute workspace paths and instruct the new session to read this file and `PROJECT-HANDOFF.md` completely before acting.
- Before resuming, the new session must inspect live Git status/branch divergence, output and metadata counts, OneDrive availability, the latest upload report and the actual Windows Scheduled Task state. Never assume those external states from an older checkpoint.

## Finished-video transfer

- On this computer, every newly completed and validated redesigned episode must be copied to the OneDrive for Business destination configured in `transfer-config.json`.
- Keep the local `output` copy; the OneDrive operation is a verified mirror, not a destructive move.
- Never silently overwrite a different destination file. The shared producer verifies size and SHA-256 before accepting an existing or newly copied file.

## Keep Git current

- After each material automation change or small completed production checkpoint, review the diff, update `PROJECT-HANDOFF.md`, commit the relevant Parenting Rewind source/metadata files, and push the current branch when the remote is available.
- Stage only intended `ParentingRewind` paths. Never commit OAuth client files, tokens, immutable runtime locks, upload ledgers, logs, generated MP4s, production work, virtual environments or unrelated user changes.
- Do not create an unattended auto-commit task: every Git checkpoint must be reviewed so credentials and partial outputs cannot be captured accidentally.
- USER RECONFIRMATION (2026-08-23): keep Git updated continuously as part of the work. After every small completed production interval, make a reviewed local commit and push it when safe. If the branch is ahead and behind, do not force-push or discard either side; record the divergence and reconcile explicitly before pushing.
- USER RECONFIRMATION (2026-08-23 20:42): keep this `AGENTS.md` current with the user's latest durable instructions and include those updates in the reviewed Git checkpoint and push.
- AUTOMATIC SYNC AUTHORIZATION (2026-08-23): the user authorized the workspace-level `Animation Git Sync Every Three Hours` task. It may fetch, cleanly fast-forward and push reviewed commits for the whole repository, but it must follow the fail-closed rules in the root `AGENTS.md`: no auto-commit, force-push, dirty-tree pull, destructive reset or automatic divergence resolution.
