# Parenting Rewind project handoff

Last updated: 2026-08-22 (Australia/Sydney)

This document lets a fresh Codex session continue safely. It contains no OAuth client secret, token, password or immutable YouTube channel ID. Inspect the live workspace before acting because files may have changed after this handoff.

## Current objective

Create a high-quality, adult-facing parenting education channel under the working name **Parenting Rewind**. The user plans to create the YouTube channel later. On 2026-08-22 the user approved the existing videos and authorized an open-ended overnight local production run targeting 50 or more complete videos. No upload is authorized.

This project is separate from `KidsRhymes` / Tiny Tales. Never reuse that project's OAuth files, token, channel lock, upload ledger, archive or Scheduled Tasks.

## Current external state

- The Parenting Rewind YouTube channel has not been created or verified.
- This project has no OAuth client secret, OAuth token, immutable channel lock, upload ledger, uploader, upload archive, upload Scheduled Task or email automation.
- Nothing from this project has been uploaded to YouTube.
- Do not upload until a separate OAuth token returns the exact new channel ID from `channels.list(mine=true)` and the user explicitly approves one private test upload.

## Approved creative direction

- Audience: parents and adults, not children. Set audience metadata accurately after the channel exists; the creative should remain clearly adult-directed.
- Core structure: show a familiar parenting problem, an unhelpful reaction, a pause/rewind moment, a calmer response and one specific takeaway.
- Useful recurring device: **Pause. Rewind. Repair.** or **Say this instead.**
- Typical child ages discussed: approximately 2–8.
- Tone: practical, specific, empathetic and conversational—like one parent advising another, not a robotic or all-knowing AI persona.
- Give general parenting education only. Do not provide personalized therapy, diagnosis or medical advice.
- Research factual/behavioral claims with authoritative sources such as CDC, AAP or HealthyChildren and record the sources in each video's metadata.
- Recurring characters and settings are fine, but every episode needs distinct substance. Do not publish a template with only the words changed.
- For episodes with substantially different topics and newly cast people or families, vary the apparent ethnic and cultural backgrounds represented across the series. Keep portrayals natural and respectful, avoid stereotypes, and preserve character continuity within each episode.
- Vary mothers, fathers and other suitable caregivers, child ages and genders, family compositions, rooms, homes and public settings. Rotate scene order, crops, motion, emotional pacing and lesson structure so the channel does not feel visually or narratively repetitive.

## Voice, music and visuals

- The user approved the second pilot's warmer conversational delivery as the narration baseline and said they were happy with V4's music direction on 2026-08-22.
- Current preferred voice baseline: `en-US-AvaMultilingualNeural`, rate `-5%`, pitch `-1Hz`.
- A stable pool of two or three voices may be used between videos, but do not randomize every episode or switch voices mid-video except for clearly intentional dialogue.
- Synthetic voices remain synthetic; truly non-AI narration would require a human recording.
- The user does not want ambient background noise or sound effects. Use a musical score that follows the emotion: restrained tension/frustration, pause/rewind, calm and resolution.
- Keep music clearly audible while always preserving narration intelligibility. Use restrained automatic ducking under speech.
- Pilot V3's music was too quiet and was rejected as a listening reference. Pilot V4 raises it by approximately 9.54 dB with narration-aware ducking and is now the approved music baseline.
- Reuse local images before generating new ones to save credits. Existing panels may be reframed, cropped, panned, zoomed, color-treated and overlaid.
- Do not reuse an entire previous sequence with only new text or narration.
- Record `new_image_generation_calls` in episode metadata. The shoe storyboard used one built-in image-generation call; V2, V3 and V4 used zero new image-generation calls. Pilot 02 used one new built-in image-generation call for its six-panel screen-time storyboard.

## Current pilot state

The first lesson is a shoe-putting-on scenario.

- `output/parenting-rewind-pilot-01-shoes.mp4`: V1; approximately 68.33 seconds; voice was considered robotic.
- `output/parenting-rewind-pilot-01-shoes-v2-conversational.mp4`: V2; approximately 78.67 seconds; user liked this version and it is the preferred content/voice baseline.
- `output/parenting-rewind-pilot-01-shoes-v3-dynamic-music.mp4`: V3; music too quiet; keep as a rejected reference, not a production choice.
- `output/parenting-rewind-pilot-01-shoes-v4-audible-dynamic-music.mp4`: V4; corrected louder dynamic music; technical checks passed; approved as the current music direction.

V4 technical checks: 1080×1920 vertical H.264 video, 48 kHz stereo AAC audio, duration approximately 78.67 seconds.

On 2026-08-22, the user said they were happy with V4 and asked to start the next video. Treat V2 voice plus V4 music as approved unless the user records a later preference.

## Current representative episode state

Pilot 02 addresses **ending screen time without shouting**.

- `output/parenting-rewind-pilot-02-screen-time-v1.mp4`: complete local V1 awaiting user review; do not upload.
- Duration: approximately 88.83 seconds.
- Technical format: 1080×1920 vertical H.264/yuv420p at 30 fps; 48 kHz stereo AAC at approximately 192 kbps.
- Full video/audio decode passed. Final audio measured approximately -15.9 LUFS integrated, 3.0 LU LRA and -2.2 dBFS true peak.
- SHA-256: `A0E5283EE964D67755AA75880958A14A6E13E77D22015679FDD3F2BEDCDADA8A`.
- Narration uses the approved V2 settings: `en-US-AvaMultilingualNeural`, rate `-5%`, pitch `-1Hz`.
- Music is a new locally synthesized emotional score using V4-style +9.54 dB gain and sidechain ducking. It contains no ambient background noise or sound effects.
- Captions are burned in from speech-service sentence boundaries, match the narration transcript, and also exist as `production-work/pilot-02-screen-time-v1/captions.srt`.
- One new six-panel living-room storyboard was generated in one built-in image-generation call: `production-assets/screen-time-storyboard-01.png`.
- All new storyboard panel `published_uses` remain zero because this is an unpublished local review file.
- Metadata records AAP/HealthyChildren research, original title/description/tags, generation-call counts, technical validation and `upload_authorized: false`.

## Important project files

- `AGENTS.md`: binding project instructions.
- `README.md`: project overview.
- `production-assets/asset-library.json`: reusable asset inventory and usage counts.
- `production-assets/pilot-01-shoe-storyboard.png`: existing six-panel storyboard.
- `scripts/produce_pilot_01.py`: V1 producer.
- `scripts/produce_pilot_01_v2.py`: V2 conversational producer.
- `scripts/produce_pilot_01_v3_dynamic_music.py`: V3 dynamic-music producer.
- `scripts/remix_pilot_01_v4_audible_music.py`: V4 louder-music remix.
- `metadata/pilot-01-shoes.json`: V1 metadata.
- `metadata/pilot-01-shoes-v2-conversational.json`: V2 metadata.
- `metadata/pilot-01-shoes-v3-dynamic-music.json`: V3 metadata.
- `metadata/pilot-01-shoes-v4-audible-dynamic-music.json`: V4 metadata.
- `production-assets/screen-time-storyboard-01.png`: new six-panel Pilot 02 living-room storyboard.
- `scripts/produce_pilot_02_screen_time_v1.py`: isolated Pilot 02 producer.
- `metadata/pilot-02-screen-time-v1.json`: Pilot 02 metadata and research record.
- `output/parenting-rewind-pilot-02-screen-time-v1.mp4`: completed Pilot 02 review MP4.
- `production-work/pilot-02-screen-time-v1/quality-report.json`: Pilot 02 validation report.
- `production-work/pilot-02-screen-time-v1/quality-contact-sheet.jpg`: all eight Pilot 02 scene beats.

## Active batch authorization and checkpoint

- STOPPED BY USER (2026-08-23): the user said the batch's videos, characters and visuals looked exactly the same and directed Codex to stop repeating everything. All detected Python and FFmpeg batch processes were terminated. Do not resume the current renderer.
- The batch ledger reached completed episodes 003-027 before termination; with the two earlier pilots, 27 validated completed videos are recorded, although the user rejects the repeated visual format. A 28th MP4 may exist from an interrupted in-progress item and must not be treated as validated without checking its ledger/report.
- `scripts/produce_authorized_batch.py` and its three-storyboard rotation are rejected as a production format. Preserve outputs for review; do not upload or silently delete them.
- Any future production must first introduce genuinely distinct casts, child ages/genders, family structures, locations, backgrounds and compositions, then obtain approval of one representative redesigned video before batching.
- On 2026-08-23, at the user's request, all 26 rejected batch MP4s (episodes 003-028) were removed from the active `output` folder and moved recoverably to `rejected-repetitive-batch-archive/output`. The two approved pilots were preserved. Do not restore the rejected MP4s to active output unless the user explicitly requests it.
- A new representative redesign is complete at `output/parenting-rewind-redesign-01-kitchen-siblings-v1.mp4`: 39.4 seconds, new fictional Black mother in her early 40s, eight-year-old daughter and four-year-old son, new pale-blue kitchen/dining setting, and a sibling turn-taking lesson. It passed the automated quality report, full FFmpeg decode and visual frame inspection. It is awaiting user review; do not batch this redesigned approach until approved.
- The user subsequently approved continued production and said recycled visuals are acceptable. Current plan: a six-video redesigned bundle total (the completed kitchen episode plus five more), with each new storyboard family used at most twice, non-consecutively, and with different lesson, order, crop and narration. This does not authorize restarting the rejected 54-item three-storyboard renderer.
- Two additional distinct storyboard assets are complete locally and awaiting registration/rendering: `production-assets/bedtime-father-daughter-storyboard-01.png` (South Asian father, six-year-old daughter, teal/coral bedroom at night) and `production-assets/playground-leaving-storyboard-01.png` (Middle Eastern mother, three-year-old son, outdoor yellow-slide playground). A first playground draft copied the kitchen mother's identity and was rejected/not saved; a no-reference retry produced the correct new cast and is the saved asset.
- New asset: `production-assets/kitchen-siblings-storyboard-01.png`, registered in `production-assets/asset-library.json`. It was created with one built-in image-generation call using the shoe storyboard only as a realism/style reference. Final prompt described a six-panel dinner-preparation conflict, parent pause, timer-based turns, different safe jobs and family-table resolution; it required a different cast, ages, room, palette and camera compositions and prohibited reuse of old people or rooms.
- The user explicitly approved all current videos and authorized as many additional local videos as practical, targeting 50 or more with no artificial cap.
- Normal in-scope creative and technical decisions are pre-approved. Do not pause to ask about cast, child age/gender, setting, topic selection, local asset generation, rendering or routine recovery.
- Uploading, publishing, email automation, OAuth work and Scheduled Tasks remain unauthorized.
- The first new batch asset was generated successfully with the built-in image tool, copied to `production-assets/supermarket-storyboard-01.png`, and registered in `production-assets/asset-library.json`: a six-panel supermarket storyboard with a fictional mother and five-year-old son with East Asian appearance. The initial call was blocked by automated output moderation; a simplified respectful retry succeeded.
- Checkpoint this section after every small production interval. Record exact output counts, episode IDs, asset paths, validation status, failures and resume commands.
- Checkpoint 1 (2026-08-23): the resumable catalog contains 54 distinct batch episodes. Batch items 1-6 completed as episodes 003-008, each with MP4, burned-in captions, SRT, metadata and a passing quality report. Together with the two earlier pilots, 8 finished local videos now exist. The first new MP4 also passed a full FFmpeg decode and visual frame inspection. Resume with `& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_authorized_batch.py --start 7 --count 5`.
- Checkpoint 2 (2026-08-23): batch items 7-11 completed as episodes 009-013 with passing quality reports. Including the two pilots, 13 finished local videos exist. Resume with `& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_authorized_batch.py --start 12 --count 5`.
- Checkpoint 3 (2026-08-23): batch items 12-16 completed as episodes 014-018 with passing quality reports. Including the two pilots, 18 finished local videos exist. Resume with `& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_authorized_batch.py --start 17 --count 5`.
- Checkpoint 4 (2026-08-23): batch items 17-21 completed as episodes 019-023 with passing quality reports. Including the two pilots, 23 finished local videos exist. Resume with `& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_authorized_batch.py --start 22 --count 5`.

## Superseded historical discussion (do not follow)

The material below predates and is superseded by the active batch authorization above.

Possible next lessons:

1. Handling a supermarket tantrum.
2. Making the bedtime transition calmer.
3. Responding to sibling fighting.
4. Helping a child admit a mistake.

The user discussed having 30–40 videos ready overnight. That discussion is **not approval** to mass-produce finished videos. A safer proposal was six finished videos total (including the shoe pilot), 30–40 researched concepts/scripts, and three reusable storyboard packs. The user had not approved or rejected that proposal before switching accounts.

## Required next steps

1. Ask the user to review `output/parenting-rewind-redesign-01-kitchen-siblings-v1.mp4`, focusing on whether the new cast, ages, two-child composition and kitchen background solve the repetition problem.
2. Keep the rejected three-storyboard batch stopped and archived. Do not generate a replacement batch until this representative visual approach is approved.
3. If approved, create several additional storyboard families before batching, with distinct mothers/fathers/caregivers, child ages/genders/counts, ethnic appearances, indoor/outdoor/public locations, palettes and camera compositions.
4. Do not upload, publish, email or create external Scheduled Tasks.
