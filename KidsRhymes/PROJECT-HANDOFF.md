# Tiny Tales automation handoff

Last updated: 2026-08-23 13:56 Australia/Sydney

This document lets a new Codex account continue the local project safely. Do not assume it is current without comparing it to runtime files, logs, filesystem contents, YouTube verification, and Windows Scheduled Task status.

## Project identity

- Project folder: `C:\Animation\Animation\KidsRhymes`
- Channel name: `Tiny Tales`
- Immutable YouTube channel ID: `UCEn9N-ITQHshjgt6fy7fxnw`
- Upload privacy: `private`
- Audience setting: made for kids
- Report email: `mukeshmelb01@gmail.com`
- Python environment: `C:\Animation\Animation\.venv\Scripts\python.exe`

## User's current editorial requirements

- Audience is children ages 3-7.
- Videos must engage, teach, or entertain; avoid a stream of near-identical quizzes.
- Do not create the retired basic matching-picture format. Its existing private upload may remain unpublished or be deleted manually in YouTube Studio.
- Do not create the animal-shadow guessing format. The user rejected its visual quality on 2026-08-23. Historical completed/private shadow videos may remain, but the producer now blocks new shadow renders and the continuing rotation contains no shadow slots.
- Do not say or display numbered `Round 1`, `Round 2`, etc. Use natural transitions such as `Let's check the next one`.
- Use a friendly child-like narrator, currently `en-US-AnaNeural`, at a natural pace and bright but non-squeaky pitch.
- Do not write `Made for kids and uploaded privately for review before publication` or similar internal workflow language in descriptions.
- Always supply a useful title, viewer-facing description, and tags. Keep made-for-kids/private settings in YouTube status fields.
- Avoid repeating the same animals in consecutive or very similar themes.
- Current reusable families: land, ocean, farm, jungle, and colourful birds.
- Preferred varied formats include animal superpowers/facts, hidden objects, disappearance memory, animal sounds/clues, footprints, habitats, cause-and-effect stories, kindness/rescue quests, lost-colour adventures, and help-it-grow stories.
- Aim for a small mission, a real child choice, a 5-7 second thinking window, positive feedback, and one memorable discovery.
- All real uploads remain private for human review before publication.

## Architecture and important files

- `automation/config.json`: non-secret channel and folder settings.
- `automation/generation-manifest.json`: curated static work. Never regenerate items marked complete.
- `automation/generation_runner.py`: resumable runner; after curated work it creates continuing themed items from the rotating catalog.
- `automation/production/produce_snack_video.py`: shared 1080p rendering/audio helpers and snack format.
- `automation/production/produce_animal_games.py`: themed disappearance/alphabet rendering. Matching and shadow generation are explicitly retired and blocked.
- `automation/production/produce_superpower_video.py`: interactive Ocean Superpower Detectives format.
- `automation/production/produce_clue_detective_batch.py`: resumable local-only jungle, farm and colourful-bird clue adventures.
- `automation/production/produce_lost_colour_batch.py`: resumable ocean, farm and colourful-bird Lost Colour Rescue adventures with six-second child choices.
- `COVERED-TOPICS.md`: generated registry of completed or queued concepts; check it before creating a new topic.
- `automation/update_covered_topics.py`: rebuilds the topic registry from live media, metadata and the static manifest.
- `automation/uploader.py`: channel-locked resumable private uploader, duplicate prevention, ledger, and post-success archive cleanup.
- `automation/Run-GenerationCycle.ps1`: time-boxed generation task wrapper with global mutex.
- `automation/Run-UploadCycle.ps1`: independent upload/email wrapper with separate global mutex.
- `automation/Install-TinyTalesTasks.ps1`: installer for the two exact tasks; it refuses to overwrite existing tasks.
- `automation/Send-OutlookReport.ps1`: sends with classic Outlook COM and confirms Sent Items; no password is stored.
- `automation/production-assets/`: approved reusable artwork sheets.
- `automation/production-work/<item>/quality-report.json`: technical quality reports.
- `automation/production-work/<item>/quality-contact-sheet.png`: visual review sheets.
- `automation/pending-uploads/`: only completed new videos waiting for upload.
- `automation/archive/`: canonical local copies after confirmed uploads.
- `automation/logs/generation.log`, `generation-task.log`, `youtube-upload.log`, and `upload-task.log`: persistent logs.

## Secrets and runtime state

These paths are local and ignored by Git. Never print their contents into chat or documentation:

- OAuth client secret: `automation/secrets/youtube-client-secret.json`
- OAuth token: `automation/runtime/youtube-oauth-token.json`
- immutable channel lock: `automation/runtime/youtube-channel-lock.json`
- upload ledger: `automation/runtime/upload-ledger.jsonl`
- upload attempt journal: `automation/runtime/upload-attempts.json`
- generation state: `automation/runtime/generation-state.json`

The uploader calls `channels.list(mine=true)` and requires the returned ID to match `UCEn9N-ITQHshjgt6fy7fxnw`. If it does not match, stop. Do not edit the lock to bypass the mismatch.

## Scheduled automation

Exact task names:

- `Tiny Tales - Continuous Generation`
- `Tiny Tales - Daily Private Upload` (the historical name says Daily, but it now has five daily triggers)

Generation starts daily at 00:05, 05:05, 10:05, 15:05, and 20:05. Each process is limited to about 4 hours 45 minutes and generates at most one new video. At the user's request on 2026-08-23, private upload checks now run every four hours at 00:20, 04:20, 08:20, 12:20, 16:20, and 20:20. Both tasks use wake, network-required, start-when-available, interactive-current-user, and ignore-new-instance settings. Named mutexes provide a second overlap guard.

Verified at handoff:

- generation task state: Ready; next run 2026-08-23 00:05
- upload task state: Ready; next run 2026-08-23 00:20
- last generation task result: success (`0`)

An upload failure leaves the MP4 and metadata in `pending-uploads`; generation must continue independently. Scheduled runs must never open interactive OAuth.

## Current content state at handoff

Completed static production items:

- Who Ate the Snack?
- Guess the Animal Shadow
- What Animal Disappeared?
- Find the Matching Animal (retired format; do not make more)
- Ocean Animal Superpower Detectives

Remaining curated static item:

- Animal Alphabet Adventure A to F

After static items complete, `generation_runner.py` continues with a deterministic five-family disappearance rotation. Shadow items were removed on 2026-08-23. Continue improving the catalog with the other preferred formats so disappearance videos do not become the only output.

## Current A-Z alphabet expansion

- The user requested one additional long Animal Alphabet Adventure combining A through Z, while preserving the completed A-F video.
- All five artwork sheets are saved under `automation/production-assets/`: A-F, G-L, M-R, S-X, and Y-Z. The new sheets were produced with the built-in image-generation workflow.
- Planned animals: giraffe, hippopotamus, iguana, jaguar, kangaroo, lion; monkey, narwhal, octopus, penguin, quokka, rabbit; seal, tiger, sea urchin, vulture, whale, x-ray tetra; yak and zebra.
- The long A-Z video completed locally at 290.4 seconds, 1920x1080 H.264 at 30 fps with 48 kHz stereo AAC audio. The technical gate passed, and the full contact sheet was visually reviewed at `automation/production-work/land-alphabet-a-to-z-01/quality-contact-sheet.png`.
- On 2026-08-23 the user explicitly requested the alphabet upload. Live channel verification matched Tiny Tales channel ID `UCEn9N-ITQHshjgt6fy7fxnw`; the dry run contained only the A-Z MP4; upload succeeded as video `-ayS0UTmcfA` (`https://youtu.be/-ayS0UTmcfA`). API read-back confirmed the intended title, private status, made-for-kids and self-declared-made-for-kids flags, correct channel ID and all eight tags.
- The uploader moved the canonical MP4 and metadata to `automation/archive/animal-alphabet-a-to-z-01.mp4` and `.json`, removed the identical working output only after YouTube returned the video ID, and left the pending queue empty. The upload ledger is authoritative.
- `automation/production/produce_animal_games.py --game alphabet --alphabet-range az` is the dedicated long-version command. The default `--alphabet-range af` preserves the completed A-F behavior.
- Generation is authorized. Upload behavior must still follow the existing channel lock, private/made-for-kids settings, duplicate prevention and explicit confirmation safeguards.

## Live-state note from 2026-08-23 11:30

- Local `main` and GitHub `origin/main` were verified at commit `697754e` before production resumed. The A-Z work described above is newer than that commit.
- The pending-upload queue had no MP4s and the archive contained eight MP4s.
- The 10:05 continuous generation run was interrupted: `continuous-00001-jungle-disappeared-01` remains marked `running`, but no Python or FFmpeg process was active and only partial work files existed. Do not treat it as completed or upload it. Reconcile this stale state before the next continuous generation run.
- Both Scheduled Tasks were Ready. The generation task's last result was `4294967295`; the upload task's last result was `1`.

At handoff, the pending upload queue has no MP4s. Six MP4s are present in the archive, including the initial tool test. The upload ledger is the authoritative record for uploaded local content.

## Confirmed private YouTube uploads

- `LUA51hfEcYU` - initial tool test
- `zAR5CkV2MMo` - Who Ate the Snack?
- `HSU5icdAnSs` - Guess the Animal Shadow
- `gGQHkHcswGg` - What Animal Disappeared?
- `_a50NuDSRPQ` - Find the Matching Animal (retired)
- `3z6kDg0DXmo` - Ocean Animal Superpower Detectives
- `fvtpuEGx5Vw` - Animal Alphabet Adventure A-F
- `-ayS0UTmcfA` - Animal Alphabet Adventure A-Z

## New clue-detective batch and four-hour upload checkpoint

- Three local Animal Clue Detective videos completed on 2026-08-23: jungle (131.5 seconds), farm (126.8 seconds), and colourful birds (130.8 seconds). Each passed its automated quality gate, full FFmpeg decode, and visual contact-sheet review.
- The three MP4s total 19.47 MiB. They remain in `automation/production-output`, with matching metadata under `metadata/`.
- Live OAuth verification returned the exact locked Tiny Tales channel ID `UCEn9N-ITQHshjgt6fy7fxnw` before queueing.
- All three were copied into `automation/pending-uploads` with metadata for private, made-for-kids upload. They are not counted as uploaded until YouTube returns an ID; the upload ledger remains authoritative.
- The upload Scheduled Task was changed and verified Ready with triggers at 00:20, 04:20, 08:20, 12:20, 16:20 and 20:20. At verification, its next run was 2026-08-23 16:20 Australia/Sydney.
- The stale `continuous-00001-jungle-disappeared-01` runtime entry was reset from `running` to `pending` after confirming no Python/FFmpeg process and no completed output. Partial work files were preserved.
- `COVERED-TOPICS.md` records 12 completed or queued Tiny Tales concepts, including retired formats. Rebuild it with `automation/update_covered_topics.py` after future metadata or media changes.

## Lost Colour Rescue checkpoint

- On 2026-08-23, three additional local videos completed in a new Lost Colour Rescue format: ocean (128.3 seconds), farm (127.1 seconds), and colourful birds (132.0 seconds).
- Each uses grayscale-to-colour animal restoration, three visible colour choices, a six-second child decision window, a colour reveal, and an animal fact. The batch reused existing approved artwork and used zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were copied into `automation/pending-uploads` behind the three existing clue-detective videos. The queue contains six MP4s total. A dry run selected `jungle-animal-clue-detectives-01.mp4` next and reported five remaining after that next item; no unrelated item was selected.
- `COVERED-TOPICS.md` was rebuilt and now records 15 completed or queued concepts.

The last upload was read back through YouTube Data API and confirmed private, made for kids, and carrying all eight requested tags. Its Outlook report was confirmed in Sent Items to `mukeshmelb01@gmail.com`.

## Safe continuation checklist

1. Read this file and `AGENTS.md`.
2. Inspect `git status`, manifest, generation state, pending queue, archive, ledger, and recent logs without exposing secret contents.
3. Query both exact Scheduled Tasks and their next/last run information.
4. Run the generation count-only command before generating anything.
5. Verify the OAuth channel with the uploader's read-only verify command before any upload work.
6. Report live state and discrepancies to the user.
7. Continue only unfinished work. Do not regenerate or re-upload completed ledger entries.
8. Visually inspect each new quality contact sheet before manually approving an immediate upload; scheduled uploads still enforce technical checks, channel lock, stability age, duplicate ledger, private status, and made-for-kids.
9. Update this handoff after material architecture, schedule, channel, recipient, safety, or editorial changes.

Useful read-only commands from the project folder:

```powershell
C:\Animation\Animation\.venv\Scripts\python.exe -B automation\generation_runner.py --count-only
C:\Animation\Animation\.venv\Scripts\python.exe -B automation\uploader.py verify
C:\Animation\Animation\.venv\Scripts\python.exe -B automation\uploader.py dry-run --report-json automation\runtime\handoff-dry-run.json
Get-ScheduledTask -TaskName 'Tiny Tales - Continuous Generation','Tiny Tales - Daily Private Upload'
```

## Separate new-channel request

The user wants to create another channel/project in a separate folder, but has not yet supplied the new folder/channel name, channel ID, or concept. Do not reuse any Tiny Tales OAuth token, channel lock, ledger, archive, runtime state, or Scheduled Tasks. Create a clean isolated project only after obtaining the new identity details.
