# Parenting Rewind

This is a separate adult-facing parenting education video project. It is not part of Tiny Tales.

## Current scope

- The active catalog contains 87 validated videos in the configured Business OneDrive transfer/upload folder: two pilots plus redesigned episodes 01-85.
- **When Your Child Refuses Their Shoes** established the approved V2 narration and V4 music baseline.
- **Screen Time Is Over: What to Say Without Shouting** established the second adult-facing scenario.
- 1080 × 1920 vertical video
- Original project storyboards, synthetic narration, burned-in captions and original locally synthesized music
- The YouTube channel is live and verified through isolated OAuth as **Parenting Rewind** (`UCGb-IUQX2KQa_KA24MwE_aQ`).
- A fail-closed public uploader is configured under `automation/`; it never reuses another project's credentials and verifies the immutable channel ID before every upload.
- YouTube's altered/synthetic-content disclosure is set to **Yes** (`status.containsSyntheticMedia=true`) for every future Parenting Rewind upload. All 19 videos already on the channel were updated and API-confirmed on 2026-08-27.
- PUBLIC UPLOAD OVERRIDE (2026-08-26 20:55): upload the oldest remaining episode first as public every two hours through 2026-08-28 20:55 Australia/Sydney, then every four hours. Videos remain marked not made for kids, and successful uploads continue to trigger an Outlook email to `mukeshmelb01@gmail.com`.
- Windows task `Parenting Rewind - Public Upload Cadence` checks every two hours; the uploader enforces the temporary two-hour gate and then skips alternating checks to enforce four hours. The old private and superseded five-hour tasks are disabled.
- The repetitive three-storyboard batch was rejected and removed from active output. Its MP4s are preserved under `rejected-repetitive-batch-archive/output` only for recovery.
- The user explicitly approved `output/parenting-rewind-redesign-01-kitchen-siblings-v1.mp4` on 2026-08-23 and authorized continued local production until asked to stop.
- Continue only the redesigned workflow; keep the rejected repetitive renderer retired. New work must vary developmental stages, casts and settings, and should maintain the required toddler, school-age and teenage mix.
- Every episode newly produced after 2026-08-23 17:33 ends with the spoken and burned-in-caption call to action: **If this helped, like and subscribe for more practical Parenting Rewind ideas.**

## Build the pilot

From `C:\Animation\Animation`:

```powershell
& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_pilot_01.py
```

The completed MP4 is written to `ParentingRewind\output`. The quality report and contact sheet are written to `ParentingRewind\production-work\pilot-01-shoes`.

For the warmer conversational V2, run:

```powershell
& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_pilot_01_v2.py
```

V2 reuses all existing artwork and writes a separate MP4. It does not overwrite V1.

For V3 with narration-aware emotional music, run:

```powershell
& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_pilot_01_v3_dynamic_music.py
```

V3 reuses both the V2 narration and the original artwork. Its locally composed score changes from urgency and frustration to pause, rewind, calm and resolution. It contains no environmental sound effects.

If V3's music is too quiet, create V4 with the score raised and automatically ducked beneath narration:

```powershell
& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\remix_pilot_01_v4_audible_music.py
```

The pilot is general parenting education based on positive-discipline guidance. Future videos should use authoritative sources, avoid diagnosis or personalised medical/mental-health advice, and remain clearly directed to adults.

## Build the screen-time review episode

Pilot 02 uses the approved V2 voice settings and V4-style narration-aware emotional score. It has no ambient background noise or sound effects:

```powershell
& .\.venv\Scripts\python.exe .\ParentingRewind\scripts\produce_pilot_02_screen_time_v1.py
```

The producer preserves an existing completed MP4 rather than overwriting it. Its quality report, contact sheet, caption sidecar, diagnostic audio and intermediate work are under `production-work\pilot-02-screen-time-v1`.

## Image-credit conservation

Future episodes must check `production-assets\asset-library.json` before requesting new artwork. The library currently records 33 reusable storyboard families. Suitable scenes can be reused by changing crops, motion, overlays, captions, narration and sequencing locally.

The user rejected the episode-70 free local ComfyUI/SDXL trial for poor image quality and asked to return to Codex image generation. Episode 70 therefore uses a new one-call built-in storyboard; the rejected local draft is not part of the active asset library. The current library contains 33 storyboard families after the episode 83-85 additions.

Recurring characters and settings create useful channel continuity, but the complete visual sequence must not be repeated with only superficial text changes. New artwork should be generated only when the existing panels cannot clearly illustrate the new parenting situation.
