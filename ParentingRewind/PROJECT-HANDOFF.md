# Parenting Rewind project handoff

Last updated: 2026-08-23 12:37 (Australia/Sydney)

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
- EXPLICIT REDESIGN APPROVAL (2026-08-23): the user approved `output/parenting-rewind-redesign-01-kitchen-siblings-v1.mp4` and authorized the five-video redesigned bundle. The user then instructed Codex to continue creating local videos until asked to stop. This expands local production only; upload, publication, email, OAuth and Scheduled Tasks remain unauthorized.
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
- Redesigned checkpoint 1 (2026-08-23 11:49): episodes 02-06 completed with passing automated quality gates and full FFmpeg decodes. Six-frame visual contact sheets were created and reviewed successfully in each episode folder under `production-work/redesigned-bundle-2026-08-23`. Active `output` now contains eight MP4s: two approved pilots plus redesigned episodes 01-06. The five new episodes are bedtime stalling, leaving the playground, the one-more-story loop, specific teamwork praise, and meaningful playground warnings. No upload occurred.
- Redesigned checkpoint 2 (2026-08-23 11:54): episodes 07-11 completed with passing automated quality gates, full FFmpeg decodes and reviewed six-frame visual contact sheets. Active `output` now contains 13 MP4s: two approved pilots plus redesigned episodes 01-11. The interval used five different visual families in sequence: supermarket, entryway, kitchen, living room and bedroom. Resume code is `scripts/produce_redesigned_bundle_07_to_11.py`; it preserves passed existing outputs. No upload occurred.
- New asset checkpoint (2026-08-23 11:57): `production-assets/homework-mother-daughter-storyboard-01.png` was created with one built-in image-generation call and registered in `production-assets/asset-library.json`. It introduces a fair-skinned mother in her late 30s, a nine-year-old daughter, and a sage/terracotta after-school study setting.
- Redesigned checkpoint 3 (2026-08-23 12:01): episodes 12-16 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 18 MP4s: two approved pilots plus redesigned episodes 01-16. The interval used homework, playground, supermarket, bedroom and kitchen families in sequence. Resume code is `scripts/produce_redesigned_bundle_12_to_16.py`; it preserves passed existing outputs. No upload occurred.
- New asset checkpoint (2026-08-23 12:04): `production-assets/library-grandmother-granddaughter-storyboard-01.png` was created with one built-in image-generation call and registered in `production-assets/asset-library.json`. It introduces an East Asian-appearance grandmother in her early 60s, a four-year-old granddaughter and a bright community-library setting.
- Redesigned checkpoint 4 (2026-08-23 12:18): episodes 17-21 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 23 MP4s: two approved pilots plus redesigned episodes 01-21. The interval used library, living-room, homework, supermarket and entryway families in sequence. Resume code is `scripts/produce_redesigned_bundle_17_to_21.py`; it preserves passed existing outputs. Tiny Tales A-Z upload was prioritized after this interval; Parenting production remains local-only and is now resumed.
- Redesigned checkpoint 5 (2026-08-23 12:25): episodes 22-26 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 28 MP4s: two approved pilots plus redesigned episodes 01-26. The interval used library, kitchen, homework, playground and bedroom families in sequence. Resume code is `scripts/produce_redesigned_bundle_22_to_26.py`; it preserves passed existing outputs. No Parenting upload occurred.
- New asset checkpoint (2026-08-23 12:28): `production-assets/laundry-father-two-children-storyboard-01.png` was created with one built-in image-generation call and registered in `production-assets/asset-library.json`. It introduces a Latino-appearance father in his early 40s, a ten-year-old daughter, a six-year-old son and a white/lavender laundry-mudroom setting.
- Redesigned checkpoint 6 (2026-08-23 12:31): episodes 27-31 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 33 MP4s: two approved pilots plus redesigned episodes 01-31. The interval used laundry, library, living-room, homework and supermarket families in sequence. Resume code is `scripts/produce_redesigned_bundle_27_to_31.py`; it preserves passed existing outputs. No Parenting upload occurred.
- Redesigned checkpoint 7 (2026-08-23 12:37): episodes 32-36 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 38 MP4s: two approved pilots plus redesigned episodes 01-36. The interval used laundry, bedroom, library, entryway and kitchen families in sequence. Resume code is `scripts/produce_redesigned_bundle_32_to_36.py`; it preserves passed existing outputs. No Parenting upload occurred.
- New asset checkpoint (2026-08-23 12:41): `production-assets/soccer-father-son-storyboard-01.png` was created with one built-in image-generation call and registered in `production-assets/asset-library.json`. It introduces a dark-skinned father in his late 30s, a seven-year-old son and an outdoor community soccer-field setting.
- Redesigned checkpoint 8 (2026-08-23 12:50): episodes 37-41 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 43 MP4s: two approved pilots plus redesigned episodes 01-41. The interval used soccer, laundry, library, homework and playground families in sequence. Resume code is `scripts/produce_redesigned_bundle_37_to_41.py`; it preserves passed existing outputs. No Parenting upload occurred.
- Redesigned checkpoint 9 (2026-08-23 13:01): episodes 42-48 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains exactly 50 MP4s: two approved pilots plus redesigned episodes 01-48. The interval used supermarket, bedroom, kitchen, soccer, laundry, library and living-room families in sequence, with distinct lessons, scene orders and crop patterns. Resume code is `scripts/produce_redesigned_bundle_42_to_48.py`; it preserves passed existing outputs. The user's target of 50 active local videos has been reached, and open-ended local production remains authorized until the user asks to stop. No Parenting upload occurred.
- Redesigned checkpoint 10 (2026-08-23 13:09): episodes 49-53 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 55 MP4s: two approved pilots plus redesigned episodes 01-53. The interval used homework, playground, supermarket, bedroom and kitchen families in sequence. Resume code is `scripts/produce_redesigned_bundle_49_to_53.py`; it preserves passed existing outputs. No Parenting upload occurred.
- Redesigned checkpoint 11 (2026-08-23 13:17): episodes 54-58 completed with passing automated gates, full FFmpeg decodes and reviewed visual contact sheets. Active `output` now contains 60 MP4s: two approved pilots plus redesigned episodes 01-58. The interval used soccer, laundry, library, living-room and homework families in sequence. Resume code is `scripts/produce_redesigned_bundle_54_to_58.py`; it preserves passed existing outputs. No Parenting upload occurred.
- Transfer checkpoint (2026-08-23): all 60 active Parenting MP4s were copied non-destructively to `C:\Users\MukeshGupta\OneDrive\ParentingRewind-60-Videos-2026-08-23` and verified by file count and total byte size (206.34 MiB). Git continues to exclude MP4s; use OneDrive for finished-video transfer and Git for production code and metadata.
- Business OneDrive checkpoint (2026-08-23): at the user's request, the same 60 active Parenting MP4s were also copied non-destructively to `C:\Users\MukeshGupta\OneDrive - SQL BI Consulting Pvt Ltd\Videos\ParentingRewind-60-Videos-2026-08-23`. The destination was verified at 60 files and 216,361,489 bytes (206.34 MiB). Treat this OneDrive for Business location as the preferred cross-computer transfer folder; the earlier personal OneDrive copy was left untouched.
- Automatic transfer rule (2026-08-23): `transfer-config.json` stores the OneDrive for Business destination. The shared `produce()` helper in `scripts/produce_redesigned_bundle_02_to_06.py` now mirrors every newly completed redesigned MP4 only after its quality gate passes, preserves the local output, verifies SHA-256, accepts an identical existing destination, and refuses to overwrite a different file. Future redesigned bundle scripts should continue importing this shared helper.
- Topic registry checkpoint (2026-08-23): `COVERED-TOPICS.md` records 84 unique active or historical topics so future sessions avoid accidental repetition. Rebuild it after metadata changes with `scripts/update_covered_topics.py`.

## Superseded historical discussion (do not follow)

The material below predates and is superseded by the active batch authorization above.

Possible next lessons:

1. Handling a supermarket tantrum.
2. Making the bedtime transition calmer.
3. Responding to sibling fighting.
4. Helping a child admit a mistake.

The user discussed having 30–40 videos ready overnight. That discussion is **not approval** to mass-produce finished videos. A safer proposal was six finished videos total (including the shoe pilot), 30–40 researched concepts/scripts, and three reusable storyboard packs. The user had not approved or rejected that proposal before switching accounts.

## Required next steps

1. Continue small local redesigned intervals until the user asks to stop, checkpointing exact completed episode IDs and resume commands after each interval.
2. Keep the rejected three-storyboard batch stopped and archived. Rotate the broader asset library in non-consecutive doses; do not rebuild a repetitive feed.
3. Continue varying mothers, fathers and suitable caregivers; child ages, genders and counts; ethnic appearances; indoor, outdoor and public locations; palettes, panel order and crops.
4. Do not upload, publish, email or create external Scheduled Tasks.
