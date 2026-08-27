# Tiny Tales project instructions

Before changing or running this project, read `PROJECT-HANDOFF.md` completely and then inspect the live runtime state. The handoff is a guide; local manifests, ledgers, task status, logs, and files are the source of truth when they are newer. Before creating a new concept, read `COVERED-TOPICS.md` and rebuild it with `automation/update_covered_topics.py` after new metadata or completed media is added.

Safety requirements:

- Never expose, copy, replace, or commit OAuth credentials or tokens.
- Never reuse this project's token or channel lock for another channel or laptop.
- Tiny Tales now uses dedicated Google Cloud project ID `tiny-tales-506508`. Never use that project's OAuth client or quota for the Birthday channel or any other channel, and never rotate Cloud projects to bypass quota.
- Verify the immutable channel ID before every real upload.
- Current upload visibility is `public` by the user's explicit instruction on 2026-08-24. Always mark uploads made for kids, preserve the immutable channel lock, and require the explicit confirmation flag for every real upload.
- A real upload requires the existing explicit confirmation flag.
- Never regenerate a completed item or upload an archived/existing video again.
- When the user clearly asks to fix and replace or re-upload a defective Tiny Tales video, that request is standing authorization to delete the exact verified defective YouTube upload as part of the replacement. Do not ask for a second conversational deletion confirmation. Before deletion, still verify the immutable channel ID, exact video ID and exact expected title; send only one delete request, confirm absence before uploading, and never infer permission for batch or unrelated deletion.
- Archive only after YouTube returns a video ID.
- Every video created after 2026-08-24 19:24 Australia/Sydney must prove a continuous visual timeline with no uncovered or overlapping transition intervals, prove that any finale/end card occurs only in its intended final event, pass a full FFmpeg decode, and have both its general and every-boundary transition contact sheets visually reviewed before upload. Queue metadata must carry the required quality flags and evidence paths enforced by `uploader.py`; never bypass the cutoff or falsify review evidence.
- Use a content-specific 1280x720 custom thumbnail for each new confirmed Tiny Tales upload. Base it on the video's real visuals, keep text short and exactly readable, visually review it, verify the exact channel/video ID/title before setting it, and fetch the served YouTube thumbnail back for final comparison. Never apply Tiny Tales thumbnails to unrelated historical channel uploads.
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

## Generation resumed (2026-08-23 17:36 Australia/Sydney)

- The user explicitly asked the new Codex account to continue from the project handoff, satisfying the pause checkpoint's resume condition.
- Live verification found a clean `main` worktree at `5fda52b`, zero divergence from `origin/main`, 36 pending MP4s, 9 archived/ledgered uploads, and no active Python or FFmpeg process.
- Read-only YouTube verification matched Tiny Tales and immutable channel ID `UCEn9N-ITQHshjgt6fy7fxnw`. The upload dry run selected `jungle-animal-clue-detectives-01.mp4` from 36 queued items and performed no upload.
- `Tiny Tales - Continuous Generation` was re-enabled and verified Ready for 20:05. `Tiny Tales - Daily Private Upload` remained enabled and Ready for 20:20; its previous result remains `1` from the recorded quota failure.
- Generation is authorized again under the existing one-video-per-cycle safeguards. The animal-shadow format remains retired, and uploads remain private, made for kids, channel-locked, and independently scheduled.

## First resumed generation cycle (2026-08-23 17:42 Australia/Sydney)

- After the user reaffirmed that video generation should continue, the existing guarded Scheduled Task was started once manually while remaining enabled for its normal triggers.
- `What Farm Animal Disappeared? | Memory Game 1 for Kids` completed successfully as `what-farm-animal-disappeared-01` at 130 seconds. It passed the automated quality gate, a full FFmpeg decode, and visual contact-sheet review.
- The completed MP4 and viewer-facing metadata are in `automation/pending-uploads`; the private queue contains 37 MP4s. No upload was triggered by this generation cycle.
- `COVERED-TOPICS.md` was rebuilt and records 46 concepts. The next count-only candidate is `What Colourful Bird Disappeared 1`.
- The generation task returned to Ready with exit code `0` and remains scheduled for 20:05. Continue respecting the one-video-per-cycle cap and add varied non-quiz formats so disappearance episodes do not dominate the catalog.

## Disappearance-frequency correction (2026-08-23 Australia/Sydney)

- The user asked not to create disappearance-memory videos so frequently.
- `automation/generation_runner.py` no longer synthesizes a five-theme disappearance episode whenever the curated manifest is exhausted. Existing completed and queued memory videos remain preserved.
- An exhausted manifest now produces no new video until a deliberately varied item is added. Do not restore an all-disappearance fallback. Disappearance may appear occasionally in a genuinely mixed catalog, but never consecutively or as the dominant continuing format.

## Creative and voice rotation (2026-08-23 Australia/Sydney)

- The user does not want children to feel that new videos are the same template or the same voice. Variation must be structural, not merely a theme or animal swap.
- Consecutive new videos must vary the format family, visual system, interaction mechanic, character or presenter, setting structure, and narration profile. Review at least the latest five covered/queued concepts before proposing the next one.
- Available verified voice profiles are `ana-us`, `maisie-uk`, `natasha-au`, and `ryan-uk`. The user explicitly requires a different lead voice in every consecutive video; never use the same lead profile for adjacent productions, and do not reuse a profile within the next three new videos. Keep delivery natural, friendly, and non-squeaky.
- Long-form character stories should use genuinely different narrator and character voices when dialogue is present, rather than using only pitch changes on one voice.
- Every new non-legacy manifest item must declare `format_family`, `visual_system`, `interaction_style`, and `voice_profile`. The runner rejects missing fields and recent voice/format repetition before rendering.
- Record the actual voice profile and creative-family fields in queued metadata and quality reports so future sessions can audit the rotation. Preserve all completed media; this policy applies prospectively.
- The user’s requested story/song directions are recorded in `STORY-ROADMAP.md`: health routines, peek-a-boo, a traditional shark-family song with an original arrangement, star-character play using the public-domain “Twinkle” melody, an Ant and Grasshopper musical retelling, a paintbrush song, birthday celebration, Five Little Ducks, a ninja soccer child, and children helping an animal. Preserve the roadmap’s distinct treatment of each idea.
- The roadmap also records the user’s colour, breakfast, dad-coming-home, Mumma-shopping, playing-with-friends, sharing-toys, excavator, ice-cream and fruit-picking directions plus additional original concepts. Continue extending this roadmap proactively with genuinely different ideas, then produce them under the novelty and voice rules.
- Prioritize the animal-helping story first, then rotate through song, sports, art, fable, counting and celebration formats. Do not produce several songs or several rescue stories consecutively.

## Newest-first uploads (2026-08-23 Australia/Sydney)

- The user asked that uploads choose the most recently created stable video rather than the oldest queued video.
- `automation/config.json` sets `upload_queue_order` to `newest_first`; `automation/uploader.py` applies descending modification time with a deterministic filename tie-breaker after all existing stability, duplicate, archive and technical checks.
- This changes queue priority only. It does not bypass unresolved-attempt protection, change made-for-kids status, or weaken the immutable channel lock. Visibility is controlled separately by `automation/config.json`.

## Latest completed story checkpoint (2026-08-23 21:32 Australia/Sydney)

- `Maya and the Rainy-Day Joey Rescue` completed as `maya-rainy-day-joey-rescue-01` at 225.6 seconds and is queued for private review. It uses `natasha-au` narration, `maisie-uk` dialogue, moving Maya/joey/adult-kangaroo characters, two matched weather states and three audited participation gaps.
- The producer is `automation/production/produce_maya_joey_rescue.py`. Its five accepted generated assets are `automation/production-assets/maya-character.png`, `joey-character.png`, `adult-kangaroo-character.png`, `maya-joey-rainy-park.png`, and `maya-joey-sunset-park.png`; keep them with the producer for reproducibility.
- Automated checks, a full FFmpeg decode and visual contact-sheet review passed. The queue contains 38 MP4s and `COVERED-TOPICS.md` records 47 concepts. After the five-minute stability window, the uploader dry run selected Maya as the newest eligible item; no upload was triggered.
- The upload Scheduled Task is already installed and operates without an active Codex session. Keep its existing private/made-for-kids, channel-lock, duplicate, stability and unresolved-attempt safeguards intact.

## Original 3D-look prototype and generation stop (2026-08-23 22:05 Australia/Sydney)

- At the user's request, automatic generation was stopped after one 3D-look experiment. `Tiny Tales - Continuous Generation` is disabled with last result `0`; no Python or FFmpeg process remains. Do not re-enable it without a new explicit user request. The separate private-upload task remains enabled and Ready.
- `Nia's Rainbow Breakfast Dance` completed as `nia-rainbow-breakfast-dance-01` at 150.7 seconds. It is an original Tiny Tales breakfast/colour/movement chant and must not copy CoComelon characters, songs, branding, sets, facial design or other trade dress.
- This is not true rigged Blender animation: Blender was unavailable. The visual method uses original polished 3D-rendered pose assets, six Nia poses, six fruit-friend poses, three dimensional kitchen environments, beat-synchronised pose switching, bounce/tilt motion, parallax and camera travel. Describe it accurately as `3D-look` or `3D-rendered pose animation`.
- Nia uses `ana-us`; the host uses `ryan-uk`. Six audited movement/colour response gaps exceed five seconds. Automated 1080p H.264/stereo AAC checks, a full FFmpeg decode and final contact-sheet review passed after correcting the title composition and opening entrance.
- The producer is `automation/production/produce_nia_rainbow_breakfast.py`. Its accepted assets are `automation/production-assets/nia-3d-pose-sheet.png`, `breakfast-friends-3d-pose-sheet.png`, `rainbow-breakfast-kitchen-3d.png`, `rainbow-breakfast-table-3d.png`, and `rainbow-breakfast-finale-3d.png`; keep all five with the producer.
- The corrected video and metadata are queued for private review, bringing the queue to 39 MP4s and `COVERED-TOPICS.md` to 48 concepts. The immediate dry run correctly excluded Nia during its five-minute stability window; after the window elapsed, a second dry run selected Nia from all 39 eligible videos. No upload was triggered.

## Public upload policy and Nia upload checkpoint (2026-08-24 07:46 Australia/Sydney)

- The user explicitly changed future Tiny Tales uploads from private to public. `automation/config.json` now sets `privacy_status` to `public`; `uploader.py` uses that configured value for YouTube status, reports and the ledger. Existing historical private uploads are not mass-published by this instruction.
- All uploads must remain made for kids, channel-locked, duplicate-guarded, technically validated and explicitly confirmed. Public visibility does not weaken any other safety check.
- The 00:20 scheduled Nia attempt reached 11.2% and stopped because `Run-UploadCycle.ps1` treated normal Python stderr progress as a terminating PowerShell error. The wrapper now temporarily allows native stderr and trusts the uploader's exit code, matching the generation wrapper fix.
- The interrupted attempt briefly created YouTube ID `63l7E_6iivs`, but live API checks found it unprocessed and then confirmed that both the ID and exact title disappeared. Only after those checks was Nia's unresolved-attempt guard marked `failed_confirmed_absent`.
- A fresh explicit upload succeeded as public video `ygc-y4_XBwk` (`https://youtu.be/ygc-y4_XBwk`). API read-back matched the exact Tiny Tales channel, title, 2:31 duration, description, seven tags, public status, made-for-kids and self-declared-made-for-kids flags. The canonical MP4/metadata were archived only after YouTube returned the new ID; the queue contains 38 MP4s.
- `Tiny Tales - Continuous Generation` remains disabled. The historical task name `Tiny Tales - Daily Private Upload` remains installed and enabled, but its current behavior is public according to configuration.

## Hourly upload retry policy (2026-08-24 08:13 Australia/Sydney)

- The regular upload task keeps its existing six daily triggers at 00:20, 04:20, 08:20, 12:20, 16:20 and 20:20 Australia/Sydney.
- `Tiny Tales - Hourly Upload Retry` is a separate enabled task with the 18 intervening hourly triggers. It runs `Run-UploadCycle.ps1 -RetryOnly` and exits without uploading unless `runtime/upload-retry-state.json` records a duplicate-safe failed upload.
- A retry targets the same failed queue filename, not whichever video later becomes newest. The shared global mutex prevents overlap with the regular task.
- Only failures known not to have created a YouTube video, currently quota/upload-limit rejection, are automatically armed for retry. Ambiguous interrupted attempts remain blocked for manual YouTube reconciliation to prevent duplicates.
- Outlook reporting is now separated from upload success. An email problem is logged but cannot arm an upload retry or turn a successful upload into a task failure.
- The user explicitly resumed Tiny Tales video creation immediately after approving this retry behavior. The Animal Action Alphabet is the active build; automatic generation should be re-enabled only after its curated manifest item and producer are safely ready.

## Two new 3D-look productions and resumed schedule (2026-08-24 09:04 Australia/Sydney)

- `Animal Action Alphabet A-Z` completed as `animal-action-alphabet-a-to-z-01` at 330.4 seconds using `maisie-uk`. It contains 26 original 3D-rendered animals, five original world-stage environments and 26 audited 4.8-second movement windows. Its quality gate, full FFmpeg decode and complete A-Z contact-sheet review passed.
- `Brio's Paintbrush Colour Workshop` completed as `brio-paintbrush-colour-workshop-01` at 154.1 seconds using `ryan-uk`. It is a canvas-restoration music story with six Brio poses, five clean colour-drop friends, four art worlds, primary-colour painting, orange/green mixing and ten audited participation gaps. Its quality gate, full decode and contact-sheet review passed.
- Both producers and reproducibility assets are retained under `automation/production` and `automation/production-assets`. Built-in image generation made 11 calls for Animal Action (one rejected/replaced chroma-conflicting sheet) and 6 calls for Brio (the damaged purple drop is excluded); no external stock or copied preschool-brand imagery was used.
- Both outputs and public/made-for-kids metadata are queued. `COVERED-TOPICS.md` records 50 concepts; the queue has 39 MP4s and the archive has 11. At 09:04 the dry run selected Brio newest-first, with Animal Action behind it.
- The regular 08:20 task successfully uploaded Maya publicly as `HtNGbHueDKQ` on the locked Tiny Tales channel and confirmed its email report. Retry state is clear.
- The user explicitly resumed generation, so `Tiny Tales - Continuous Generation` is enabled and Ready for 10:05 with last result `0`. The curated manifest is currently exhausted; scheduled runs must safely no-op until another deliberately varied producer is added. Never restore the retired repetitive disappearance fallback.

## Dedicated Tiny Tales OAuth project (2026-08-24 18:53 Australia/Sydney)

- Tiny Tales was previously sharing Google Cloud project `cool-artwork-506302-q0` with the user's Birthday channel. The user created dedicated project `tiny-tales-506508`, enabled YouTube Data API v3, and supplied a Desktop OAuth client requesting only `youtube.upload` and `youtube.readonly`.
- Interactive authorization and an independent read-only verification both returned Tiny Tales and immutable channel ID `UCEn9N-ITQHshjgt6fy7fxnw`. The prior token is preserved under ignored `automation/runtime/credential-backups/`; never copy it or the new credential to the Birthday channel.
- The upload tasks were disabled during cutover and re-enabled only after verification. A dry run performed no upload, found 38 queued MP4s, and selected `animal-action-alphabet-a-to-z-01.mp4`; retry state was unarmed.

## Corrected Maya replacement and future transition gate (2026-08-24 19:28 Australia/Sydney)

- The uploaded Maya video flashed its true end card during 22 unintended 0.25-0.35 second timeline gaps. The producer now makes all 23 transitions exactly contiguous, aborts on any uncovered render timestamp, audits every transition, and proves the end card is the final event only.
- The corrected 225.6-second render passed its expanded quality gate, full decode, normal contact sheet, and a separate visual review sheet sampling every former flash point. Defective YouTube ID `HtNGbHueDKQ` was verified, deleted once, and confirmed absent before replacement upload `WLzesx1OxNU` was created.
- Read-back of `WLzesx1OxNU` matched Tiny Tales, exact title/description/seven tags, public visibility, made-for-kids flags, and 3:46 duration. The defective local archive remains preserved; the corrected archive uses the collision-safe `maya-rainy-day-joey-rescue-01-corrected.mp4` name.
- `automation/config.json` and `uploader.py` now fail closed for every future video created after the recorded cutoff unless its metadata asserts passed quality/decode/transition review and points to a passing producer report, zero-gap transition audit, general contact sheet, and reviewed transition contact sheet. Every real upload also performs a fresh full FFmpeg decode.

## Creative thumbnail refresh and resumed generation (2026-08-24 21:25 Australia/Sydney)

- The 12 live Tiny Tales automation uploads now use version-2 content-specific thumbnails built from 12 distinct built-in image-generation artworks based on truthful frames from their archived videos. Each has one short exact hook rendered locally. All were visually reviewed, uploaded, fetched back at 1280x720, pixel-compared, and reviewed again; served RMS differences were 2.179 to 4.941 from normal YouTube recompression.
- `Tavi the Tiny Train's Shape Delivery Day` completed as `tavi-shape-delivery-day-01` at 226.6 seconds using `natasha-au`. It is a connected shape-and-sequencing delivery story with five original 3D-look railway environments and deterministic code-animated Tavi/cargo motion.
- Tavi passed a complete FFmpeg decode, every producer quality check, a 27-boundary zero-gap audit, general contact-sheet review, and every-boundary transition contact-sheet review. Its queue sidecar carries the enforced evidence fields and is eligible for the normal scheduled public made-for-kids upload after the stability guard.
- `generation_runner.py` now copies producer quality evidence into every future upload sidecar. Keep the YouTube fields from the curated manifest authoritative and never mark `transition_contact_sheet_reviewed` true before actually inspecting both contact sheets.
- The user explicitly asked creation to continue. `Tiny Tales - Continuous Generation`, the regular upload task, and the hourly retry task were all Ready after reconciliation. The 11-item curated manifest is currently complete; scheduled generation safely no-ops until another deliberately varied producer is added.

## Narration-to-visual planning requirement (2026-08-25)

- The user rejected `Tavi the Tiny Train's Shape Delivery Day` because its visuals remained substantially the same for too long and the narration did not feel synchronized with what was shown. The user asked not to repair it and later explicitly requested its deletion. Exact Tiny Tales upload `GUO4zUZDbVo` was deleted and confirmed absent on 2026-08-25; preserve the local archive and historical ledger, and never re-upload it.
- Every newly planned Tiny Tales story must map each voiced beat to a matching visual shot before asset generation. The visual must begin with its narration, remain until that narration finishes, and depict the named subject/action. Prefer a materially new composition every 8 to 14 seconds; do not treat a continuous background with small overlay changes as sufficient variety.
- `Star Friends' Twinkle Playground` completed as `star-friends-twinkle-playground-01` at 116.4 seconds using `ana-us`. Its 13 voiced beats use 13 unique built-in-generated 3D-style compositions with continuous camera motion; no story artwork is reused. The approved plan is `metadata/star-friends-twinkle-playground-01-plan.json`.
- Star Friends passed its producer gate, independent full FFmpeg decode, 14-boundary zero-gap audit, explicit narration-to-visual sync audit, general contact-sheet review and every-boundary transition review. It uploaded publicly as `I7ZMQh9BoHE` with its reviewed custom thumbnail on 2026-08-25.

## Mandatory prepared thumbnails (2026-08-25)

- The user requires every Tiny Tales upload to receive a relevant, colourful, visually reviewed custom thumbnail. `automation/config.json` now sets `custom_thumbnail_required: true`; `uploader.py` excludes any queue item without a 1280x720 JPEG under 2 MB plus `prepared_thumbnail`, `thumbnail_hook`, and `thumbnail_reviewed: true` metadata. Never bypass this hold or let YouTube choose an automatic frame.
- For an eligible upload, the uploader verifies the prepared file before sending video data, records the returned video ID duplicate-safely, then immediately calls `thumbnails.set` and records the result separately. A thumbnail failure must never trigger a duplicate video upload.
- If YouTube accepts a video but the prepared thumbnail call fails, `runtime/thumbnail-retry-state.json` records that exact video ID and thumbnail. Every later real upload cycle retries the thumbnail first and will not send another video until the repair succeeds.
- Three missed recent uploads received reviewed built-in-image-generation thumbnail artwork and exact locally rendered hooks: Tavi `GUO4zUZDbVo` / `SHAPE DELIVERY!`, farm disappearance `dui6_QeKMFc` / `WHO DISAPPEARED?`, and Bea `3c5rj6In7pQ` / `HEALTHY HABIT QUEST!`. All three were fetched back from YouTube at 1280x720 and pixel-verified with RMS 2.730 to 4.242.
- YouTube's live API reported Tavi `GUO4zUZDbVo` as private immediately before the user's later explicit deletion request. One exact-ID deletion request was sent on 2026-08-25 and two API checks confirmed the ID absent. Its reviewed JPEG/artwork and archived MP4 remain local for audit, but the deleted ID is no longer a live-thumbnail target.
- Star Friends used reviewed JPEG `automation/thumbnails/star-friends-twinkle-playground-01.jpg` with hook `PLAY WITH THE STARS!` when it uploaded as `I7ZMQh9BoHE`. The older backlog remains preserved and excluded until each item independently passes the current visual/sync/transition/decode gates and receives a relevant reviewed thumbnail.

## Permanent visual-quality baseline (2026-08-25)

- The user established the recent `Star Friends' Twinkle Playground` scenes and colourful custom thumbnails as the minimum visual-quality baseline for all future Tiny Tales work. Match or exceed their polish; do not regress to basic layouts, long-held backgrounds, small overlay swaps, or generic thumbnails.
- Plan every voiced beat before generating assets and map it to a composition that directly depicts the named character, action, setting, object, or learning idea. The matching visual must begin with the narration and remain through its completion.
- Use original premium 3D-style compositions with expressive, age-appropriate characters, consistent character identity, rich but harmonious colour, dimensional lighting, foreground/background depth, and a clear visual focal point. Review every generated asset and reject weak, inconsistent, misleading, cluttered, or visibly lower-quality variants.
- Introduce a materially new, narration-relevant composition about every 6 to 10 seconds in energetic sequences, and never exceed 14 seconds without a justified internal visual progression. Continuous camera travel, parallax, character motion, and environmental animation should add life within shots without pose flicker or rapid unrelated switching.
- Keep thumbnails truthful to the video's actual content while making them colourful, cinematic, emotionally expressive, and immediately readable at small size. Use one strong focal story moment and a short exact hook rendered deterministically; never rely on a plain frame grab or generated lettering.
- Fail closed before queueing or uploading unless the narration-to-visual plan, asset review, sync audit, full decode, zero-gap transition audit, general contact sheet, transition contact sheet, and prepared-thumbnail review all pass at this quality level.

## Ten-minute upload cadence and new production set (2026-08-27)

- The user explicitly authorized uploading the reviewed Tiny Tales backlog with a ten-minute gap. `Tiny Tales - Daily Private Upload` now has one long-running repeating `PT10M` trigger, anchored to a future ten-minute boundary, and must upload at most one eligible item per run. All public/made-for-kids, immutable-channel, duplicate, unresolved-attempt, stability, full-decode, quality-evidence and custom-thumbnail gates remain mandatory.
- The normal wrapper already prioritizes an armed duplicate-safe retry for the exact failed source, so `Tiny Tales - Hourly Upload Retry` is preserved but Disabled while the ten-minute cadence is active. Do not enable a competing retry schedule unless the normal cadence is changed again.
- The reviewed installer uses the same ten-minute trigger for fresh installations. `automation/Set-TinyTalesTenMinuteUploads.ps1` is the fail-closed live migration script; it verifies both existing task actions before changing the trigger or disabling the retry task.
- The upload task is allowed to start and finish while the laptop is on battery; otherwise Windows silently skips every ten-minute slot. Network availability, global mutex, `IgnoreNew`, and the 45-minute execution limit remain enforced.
- A new varied three-video set is recorded in `metadata/new-set-plan-2026-08-27.json`: Cardboard Box Invention Club (`maisie-uk`), Niko's Ninja Soccer Kindness Match (`ryan-uk`), and Ant and Grasshopper's Shared Harvest (`natasha-au`). Preserve this voice and format rotation.
- Cardboard Box is the completed first production in this set. Its six accepted built-in-generated scenes, producer, reviewed audits, MP4 metadata and custom thumbnail passed all permanent quality gates and were released to the safeguarded queue. Preserve them; do not regenerate or requeue the source.

## Cardboard Box completion and stricter voice rotation (2026-08-27)

- The user reiterated that narration must stay visibly synchronized and that consecutive videos must not keep the same child voice. Treat lead-voice change as mandatory for every adjacent production, with the existing three-video reuse exclusion still in force. The current sequence is Cardboard Box `maisie-uk`, Niko `ryan-uk`, and Ant/Grasshopper `natasha-au`; dialogue-heavy stories should additionally use distinct character voices.
- `The Cardboard Box Invention Club` completed at 89.2 seconds from the exact plan `metadata/cardboard-box-invention-club-01-plan.json`. Its six voiced beats use six unique full-screen premium 3D-style compositions; each narration starts with its matching artwork and finishes inside it, all story shots are at most 13.98 seconds, all seven boundaries have zero gaps, and the final card appears only in the final event.
- The producer is `automation/production/produce_cardboard_box_invention_club.py`. It adds continuous camera travel, scene-specific action overlays and original deterministic music without reusing story artwork. The full 1080p H.264/stereo AAC decode, quality gate, narration-sync audit, general contact sheet, every-boundary contact sheet and `ONE BOX, FOUR WORLDS!` custom thumbnail were visually reviewed and passed before release to the manifest.

## Three-hour upload schedule (2026-08-25)

- The user explicitly changed the normal Tiny Tales upload cadence to every three hours to support channel growth. The regular upload task must check at 00:20, 03:20, 06:20, 09:20, 12:20, 15:20, 18:20, and 21:20 Australia/Sydney.
- The hourly retry task uses the 16 intervening `:20` slots and remains retry-only. It must never select a new unrelated queue video unless a duplicate-safe failure for that exact source is armed.
- Frequency does not bypass the immutable channel lock, public/made-for-kids configuration, duplicate prevention, upload limits, custom-thumbnail requirement, stability window, or any post-cutoff quality evidence gate. An empty or fully held queue must safely no-op.
- The continuous-generation task remains enabled, but the curated manifest currently has 12 completed items and zero remaining. Add only deliberately varied, fully planned concepts that meet the permanent visual-quality baseline; never restore repetitive fallback generation merely to fill three-hour upload slots.
