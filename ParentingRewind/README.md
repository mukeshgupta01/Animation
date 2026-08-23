# Parenting Rewind

This is a separate adult-facing parenting education video project. It is not part of Tiny Tales.

## Current scope

- Two local review pilots:
  - **When Your Child Refuses Their Shoes**: V2 narration and V4 music direction approved as the creative baseline
  - **Screen Time Is Over: What to Say Without Shouting**: Pilot 02 V1 awaiting user review
- 1080 × 1920 vertical video
- Original project storyboards, synthetic narration, burned-in captions and original locally synthesized music
- No YouTube channel, uploader, OAuth credentials, token, channel lock, ledger or Scheduled Task is configured
- No upload is authorized
- The repetitive three-storyboard batch was rejected and removed from active output. Its MP4s are preserved under `rejected-repetitive-batch-archive/output` only for recovery.
- The user explicitly approved `output/parenting-rewind-redesign-01-kitchen-siblings-v1.mp4` on 2026-08-23 and authorized continued local production until asked to stop.
- Redesigned episodes 02-06 are complete in `output`, with rotated bedroom, playground and kitchen casts/settings. Continue only the redesigned workflow; keep the rejected repetitive renderer retired.

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

Future episodes must check `production-assets\asset-library.json` before requesting new artwork. The library now contains six entryway panels and six living-room screen-time panels. Suitable scenes can be reused by changing crops, motion, overlays, captions, narration and sequencing locally.

Recurring characters and settings create useful channel continuity, but the complete visual sequence must not be repeated with only superficial text changes. New artwork should be generated only when the existing panels cannot clearly illustrate the new parenting situation.
