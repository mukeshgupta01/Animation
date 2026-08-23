# Tiny Tales project instructions

Before changing or running this project, read `PROJECT-HANDOFF.md` completely and then inspect the live runtime state. The handoff is a guide; local manifests, ledgers, task status, logs, and files are the source of truth when they are newer. Before creating a new concept, read `COVERED-TOPICS.md` and rebuild it with `automation/update_covered_topics.py` after new metadata or completed media is added.

Safety requirements:

- Never expose, copy, replace, or commit OAuth credentials or tokens.
- Never reuse this project's token or channel lock for another channel or laptop.
- Verify the immutable channel ID before every real upload.
- Current upload visibility is `public` by the user's explicit instruction on 2026-08-24. Always mark uploads made for kids, preserve the immutable channel lock, and require the explicit confirmation flag for every real upload.
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
- Available verified voice profiles are `ana-us`, `maisie-uk`, `natasha-au`, and `ryan-uk`. Do not use the same profile within three consecutive new videos. Keep delivery natural, friendly, and non-squeaky.
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
