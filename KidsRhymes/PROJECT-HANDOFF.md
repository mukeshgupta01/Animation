# Tiny Tales automation handoff

Last updated: 2026-08-27 Australia/Sydney

This document lets a new Codex account continue the local project safely. Do not assume it is current without comparing it to runtime files, logs, filesystem contents, YouTube verification, and Windows Scheduled Task status.

## Project identity

- Project folder: `C:\Animation\Animation\KidsRhymes`
- Channel name: `Tiny Tales`
- Immutable YouTube channel ID: `UCEn9N-ITQHshjgt6fy7fxnw`
- Dedicated Google Cloud project ID: `tiny-tales-506508` (never share with the Birthday channel or any other channel)
- Upload privacy: `public` for new uploads by explicit user instruction on 2026-08-24
- Audience setting: made for kids
- Daily summary email: `mukeshmelb01@gmail.com` at 06:00 Australia/Sydney; never email after each upload
- Python environment: `C:\Animation\Animation\.venv\Scripts\python.exe`

## User's current editorial requirements

- Audience is children ages 3-7.
- Videos must engage, teach, or entertain; avoid a stream of near-identical quizzes.
- Do not create the retired basic matching-picture format. Its existing private upload may remain unpublished or be deleted manually in YouTube Studio.
- Do not create the animal-shadow guessing format. The user rejected its visual quality on 2026-08-23. Historical completed/private shadow videos may remain, but the producer now blocks new shadow renders and the continuing rotation contains no shadow slots.
- Do not say or display numbered `Round 1`, `Round 2`, etc. Use natural transitions such as `Let's check the next one`.
- Rotate friendly, child-appropriate narrator profiles across new videos. Verified profiles are `ana-us` (`en-US-AnaNeural`), `maisie-uk` (`en-GB-MaisieNeural`), `natasha-au` (`en-AU-NatashaNeural`), and `ryan-uk` (`en-GB-RyanNeural`). Keep delivery natural and non-squeaky; do not repeat a profile within three consecutive new videos.
- Do not write `Made for kids and uploaded privately for review before publication` or similar internal workflow language in descriptions.
- Always supply a useful title, viewer-facing description, and tags. Keep made-for-kids/public settings in YouTube status fields.
- Avoid repeating the same animals in consecutive or very similar themes.
- Current reusable families: land, ocean, farm, jungle, and colourful birds.
- Preferred varied formats include animal superpowers/facts, hidden objects, disappearance memory, animal sounds/clues, footprints, habitats, cause-and-effect stories, kindness/rescue quests, lost-colour adventures, and help-it-grow stories.
- Aim for a small mission, a real child choice, a 5-7 second thinking window, positive feedback, and one memorable discovery.
- For storybook adventures inspired by `The Lost Rainbow Adventure`, retain an independently moving recurring character such as Pip. The number of locations must follow the topic naturally and is not fixed at six.
- New real uploads are public and made for kids. Existing historical private uploads remain private unless the user separately asks to publish the backlog.

## Architecture and important files

- `automation/config.json`: non-secret channel and folder settings.
- `automation/generation-manifest.json`: curated static work. Never regenerate items marked complete.
- `automation/generation_runner.py`: resumable runner; after curated work it creates continuing themed items from the rotating catalog.
- `automation/production/produce_snack_video.py`: shared 1080p rendering/audio helpers and snack format.
- `automation/production/produce_animal_games.py`: themed disappearance/alphabet rendering. Matching and shadow generation are explicitly retired and blocked.
- `automation/production/produce_superpower_video.py`: interactive Ocean Superpower Detectives format.
- `automation/production/produce_clue_detective_batch.py`: resumable local-only jungle, farm and colourful-bird clue adventures.
- `automation/production/produce_lost_colour_batch.py`: resumable ocean, farm and colourful-bird Lost Colour Rescue adventures with six-second child choices.
- `automation/production/produce_habitat_rescue_batch.py`: resumable ocean, wild-animal and bird Find My Home habitat-rescue adventures with illustrated map destinations.
- `automation/production/produce_move_like_animal_batch.py`: resumable ocean, farm and friendly-animal movement adventures with large animated characters and participation timers.
- `automation/production/produce_counting_parade_batch.py`: resumable ocean, farm and colourful-bird one-to-four counting adventures with delayed numeral reveals.
- `automation/production/produce_animal_tools_lab_batch.py`: resumable ocean, farm and bird body-feature lab adventures with custom diagrams and adaptation explanations.
- `automation/production/produce_hidden_object_story_batch.py`: resumable farm, ocean and bird hidden-object kindness quests with connected story clues and reveal circles.
- `automation/production/produce_baby_animal_album_batch.py`: resumable farm, wild-animal and bird family-album vocabulary adventures with adult/baby pages and six-second choices.
- `automation/production/produce_picture_size_adventures.py`: resumable early-maths batch with three distinct scene systems: ocean picture bubbles, a farm height ruler, and bird measuring strips.
- `automation/production/produce_raindrop_journey_story.py`: resumable one-off water-cycle narrative with a recurring raindrop character, seven changing environments, and three movement moments.
- `automation/production/produce_animal_sound_orchestra.py`: resumable one-off concert with eight farm, wild and bird performers, animated stage palettes, and child call-and-response windows.
- `automation/production/produce_animal_opposites_playground.py`: resumable one-off split-screen spatial-vocabulary adventure with six opposite pairs and movement prompts.
- `automation/production/produce_animal_shape_builders.py`: resumable one-off early-geometry construction story with six shapes, changing environments, and tracing prompts.
- `automation/production/produce_tiny_seed_growth_story.py`: resumable one-off plant-life-cycle narrative with seven growth stages, an underground root cutaway, and farm helpers.
- `automation/production/produce_five_senses_quest.py`: resumable long-form Pip adventure with five generated storybook locations, two voice deliveries, animated travel/reactions, sense-token collection, and audited response gaps.
- `automation/production-assets/five-senses-*.png`: five accepted generated backgrounds for sight, hearing, smell, taste and touch. These assets are intentionally force-added to Git despite the project's broad PNG ignore rule so the producer works on another computer.
- `automation/production/produce_four_seasons_journey.py`: resumable long-form Pip adventure through four season-specific destinations, with moving-character travel, four token types, contextual child activities, two voice deliveries, and audited response gaps.
- `automation/production-assets/four-seasons-*.png`: four accepted generated backgrounds for spring, summer, autumn and winter. Force-add these ignored PNG assets with the producer so the video remains reproducible on another computer.
- `automation/production/produce_bea_healthy_habits.py`: resumable six-minute story with a new moving bee mascot, five life-skills destinations, five habit badges, two voice deliveries, and audited response gaps.
- `automation/production-assets/healthy-habits-*.png`: five accepted generated backgrounds for handwashing, toothbrushing, colourful food, movement and sleep. Force-add these ignored PNG assets with the producer for cross-computer reproducibility.
- `automation/production/produce_maya_joey_rescue.py`: resumable child-led Australian wildlife-helping story with independently moving Maya, joey and adult-kangaroo characters, two weather states, two voice profiles and three audited participation gaps.
- `automation/production-assets/maya-character.png`, `joey-character.png`, `adult-kangaroo-character.png`, `maya-joey-rainy-park.png`, and `maya-joey-sunset-park.png`: accepted generated cutouts and matched park backgrounds for the Maya story. Force-add these ignored PNG assets with the producer for cross-computer reproducibility.
- `automation/production/produce_nia_rainbow_breakfast.py`: original 3D-look breakfast/colour/movement prototype using pose switching, parallax, camera travel, two voices, original rhythmic audio and six audited participation gaps.
- `automation/production-assets/nia-3d-pose-sheet.png`, `breakfast-friends-3d-pose-sheet.png`, `rainbow-breakfast-kitchen-3d.png`, `rainbow-breakfast-table-3d.png`, and `rainbow-breakfast-finale-3d.png`: accepted generated 3D-rendered character and kitchen assets. Force-add them with the producer. This method is not true rigged Blender animation.
- `COVERED-TOPICS.md`: generated registry of completed or queued concepts; check it before creating a new topic.
- `automation/update_covered_topics.py`: rebuilds the topic registry from live media, metadata and the static manifest.
- `automation/uploader.py`: channel-locked resumable uploader using configured visibility, duplicate prevention, ledger, and post-success archive cleanup.
- `automation/Run-GenerationCycle.ps1`: time-boxed generation task wrapper with global mutex.
- `automation/Run-UploadCycle.ps1`: independent upload wrapper with separate global mutex; it never sends email.
- `automation/Install-TinyTalesTasks.ps1`: installer for generation, upload, retry and daily-summary tasks; it refuses to overwrite existing tasks.
- `automation/Send-DailyUploadSummary.ps1`: counts the previous Sydney calendar day's successful ledger rows, sends one Outlook summary, confirms Sent Items, and blocks duplicate sends for the same date. `-DryRun` tests counts without email.
- `automation/Set-TinyTalesDailySummaryEmail.ps1`: fail-closed live migration that verifies the upload-task action and installs or updates the 06:00 summary task.
- `automation/Send-OutlookReport.ps1`: retained historical per-upload mailer; no active task or upload wrapper calls it.
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

Generation triggers remain configured at 00:05, 05:05, 10:05, 15:05, and 20:05. Normal upload checks run every three hours at 00:20, 03:20, 06:20, 09:20, 12:20, 15:20, 18:20, and 21:20 using current configured visibility (`public`). The separate retry-only task covers the intervening hourly `:20` slots. Tasks use wake, network-required, start-when-available, interactive-current-user, and ignore-new-instance settings. Named mutexes provide a second overlap guard.

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

## Find My Home habitat checkpoint

- On 2026-08-23, three additional local Find My Home videos completed: ocean (141.4 seconds), wild animals (140.4 seconds), and birds (142.2 seconds).
- The format uses a rescue-map introduction, an animal need, three illustrated habitat destinations, a six-second choice window, a highlighted suitable home, and a habitat fact. Existing artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were added to `automation/pending-uploads`. The queue contains nine MP4s total. The immediate dry run still selected `jungle-animal-clue-detectives-01.mp4`; it reported six age-eligible remaining items because the three habitat files had not yet passed the configured five-minute stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 18 completed or queued concepts.

## Move Like an Animal checkpoint

- On 2026-08-23, three additional local movement videos completed: ocean (131.8 seconds), farm (129.5 seconds), and friendly animals (134.2 seconds).
- The format opens with safe-space guidance, presents four large animated animal movements, gives children six seconds to participate, and closes each movement with a related fact. Existing artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were added to `automation/pending-uploads`, bringing the queue to 12 MP4s for private uploads at four-hour intervals.
- `COVERED-TOPICS.md` was rebuilt and now records 21 completed or queued concepts.

## Animal Counting Parade checkpoint

- On 2026-08-23, three additional local counting videos completed: ocean (113.7 seconds), farm (112.2 seconds), and colourful birds (115.9 seconds).
- The format presents four groups containing one to four animals, gives a six-second counting window, reveals the numeral and one-to-one count markers, and adds a short animal fact. Existing artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were added to `automation/pending-uploads`, bringing the queue to 15 MP4s for private uploads at four-hour intervals.
- `COVERED-TOPICS.md` was rebuilt and now records 24 completed or queued concepts.

## Amazing Animal Tools Lab checkpoint

- On 2026-08-23, three additional local body-feature videos completed: ocean (137.3 seconds), farm (136.5 seconds), and birds (137.5 seconds).
- The format presents a large custom body-feature diagram, three possible animal owners, a six-second inspection window, the correct animal reveal, and an explanation of how the feature functions. Existing animal artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were added to `automation/pending-uploads`, bringing the queue to 18 MP4s for private uploads at four-hour intervals.
- `COVERED-TOPICS.md` was rebuilt and now records 27 completed or queued concepts.

## Hidden-object kindness-story checkpoint

- On 2026-08-23, three connected hidden-object stories completed: Find Sheep's Lost Bell (117.6 seconds), Turtle's Friendship Badge (118.4 seconds), and The Cozy Nest Quest (119.7 seconds).
- Each story follows four sequential visual clues with animal helpers, a six-second search window, a circled reveal, and a cooperative resolution. The scenes and hidden items were drawn locally in code; existing animal artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were added to `automation/pending-uploads`, bringing the queue to 21 MP4s for private uploads at four-hour intervals.
- `COVERED-TOPICS.md` was rebuilt and now records 30 completed or queued concepts.

## Scheduled generation reconciliation at 15:05

- The existing `Tiny Tales - Continuous Generation` task started `what-ocean-animal-disappeared-01` at 15:05 on 2026-08-23. Manual rendering was held until the scheduled FFmpeg work completed, avoiding a resource collision.
- The ocean memory game completed at 134.3 seconds, passed its automated report, full FFmpeg decode and visual contact-sheet review, and was automatically copied to the pending queue by the generation runner.
- The queue now contains 22 MP4s. This is one allowed memory-game rotation item; no shadow or matching content was created.
- Continuous state advanced to the next allowed item, `What Farm Animal Disappeared 1`. `COVERED-TOPICS.md` now records 31 concepts.

## Baby Animal Family Album checkpoint

- On 2026-08-23, three additional local Baby Animal Family Album videos completed: farm (118.1 seconds), wild animals (123.6 seconds), and birds (124.7 seconds).
- The scrapbook format introduces four adult animals per episode, presents three possible baby names, gives a six-second child choice window, and reveals the correct family vocabulary with a short fact. The three episodes use separate farm, wild-animal and bird casts and backgrounds. Existing artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review.
- Their MP4s and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 25 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 22 age-eligible items because the three newest files were still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 34 completed or queued concepts.

## Picture-size comparison checkpoint

- On 2026-08-23, three additional early-maths videos completed: Ocean Bubble Size Station (117.2 seconds), Farm Barn Height Lineup (109.1 seconds), and Bird Feather Measuring Studio (115.6 seconds).
- These are deliberately different visual systems rather than simple theme swaps: changing ocean bubble diameters teach big/small/middle, barn cards line up against height marks for tall/short/middle, and bird picture strips terminate at different ruler positions for long/short/middle. Wording explicitly asks children to compare the displayed pictures, avoiding unsupported claims about real species sizes.
- Every episode provides four comparisons and a six-second thinking window. Existing approved animal artwork was reused with zero new image-generation calls.
- All three passed automated technical gates, full FFmpeg decodes and visual contact-sheet review with clear answer outlines and no observed clipping.
- Their MP4s and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 28 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 25 age-eligible items because the three newest files were still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 37 completed or queued concepts.

## Little Raindrop water-cycle story checkpoint

- On 2026-08-23, the one-off connected story `The Little Raindrop's Big Journey` completed at 153.8 seconds.
- This is not a repeated quiz template. Dot travels through seven changing scenes: sun-warmed ocean, rising water vapour, cloud formation, rain, a watered farm, a flowing river, and return to the ocean. The narration introduces evaporation, condensation, precipitation, collection/runoff, and water's importance to living things.
- Three 4.5-second participation moments invite children to lift their hands like vapour, shape a cloud, and wiggle their fingers like rain. Ocean, farm, river and cycle-diagram visuals were drawn locally around existing approved animal artwork; zero new image-generation calls were used.
- The video passed its automated technical gate, full FFmpeg decode, and a visual review covering every story and participation scene.
- Its MP4 and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 29 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 28 age-eligible items because the newest story was still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 38 completed or queued concepts.

## Animal Sound Orchestra checkpoint

- On 2026-08-23, the one-off `Animal Sound Orchestra` completed at 192.9 seconds.
- Eight performers take three differently coloured concert stages: cow/moo, sheep/bleat or baa, pig/oink, chicken/cluck, lion/roar, elephant/trumpet, owl/hoot, and parrot/squawk. Narration also notes that animals may use several calls, avoiding presenting each species as having only one sound.
- Every performer has a 4.8-second call-and-response window with a progress bar, animated musical notes and a pulsing character. The opening and finale show the whole ensemble. Existing approved animal artwork was reused with zero new image-generation calls.
- The video passed its automated technical gate, full FFmpeg decode, and a visual review of the opening, all eight performer screens, all eight echo screens, and the finale.
- Its MP4 and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 30 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 29 age-eligible items because the newest concert was still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 39 completed or queued concepts.

## Animal Opposites Playground checkpoint

- On 2026-08-23, the one-off `Animal Opposites Playground` completed at 155.5 seconds.
- Six split-screen scenes teach up/down with a parrot, in/out with a pig and barn, near/far with an elephant and depth cues, over/under with a dolphin and wave marker, open/closed with a goat and gates, and day/night with an owl, sun and moon.
- Each narrated pair is followed by a five-second whole-body prompt. This is a paired spatial-composition format, not a choice-card quiz. Backgrounds, position markers, barns, gates, depth scenery, arrows, sun, moon and stars were drawn locally around existing approved animal artwork; zero new image-generation calls were used.
- The video passed its automated technical gate, full FFmpeg decode, and a visual review of the title, all six teaching screens, all six movement screens, and the finale.
- Its MP4 and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 31 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 30 age-eligible items because the newest video was still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 40 completed or queued concepts.

## Animal Shape Builders checkpoint

- On 2026-08-23, the one-off `Animal Shape Builders` completed at 161.7 seconds.
- Six helpers construct different parts of a playground: Dolphin uses circles for ocean bubbles, Goat uses triangles for mountains and a roof, Pig uses square barn windows, Elephant uses rectangle bridge planks, Owl finds oval nest eggs, and Parrot hangs five-point star decorations.
- Every scene explains relevant curved edges, straight sides or corners and is followed by a 4.8-second air-tracing activity. This is a connected construction story rather than a guessing quiz. All shape geometry and environments were drawn locally around existing approved animal artwork; zero new image-generation calls were used.
- The video passed its automated technical gate, full FFmpeg decode, and a visual review of the title, all six teaching screens, all six tracing screens, and the completed-playground finale.
- Its MP4 and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 32 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 31 age-eligible items because the newest video was still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 41 completed or queued concepts.

## Tiny Seed farm growth story checkpoint

- On 2026-08-23, the one-off `The Tiny Seed's Big Farm Adventure` completed at 162.2 seconds.
- Seven connected stages follow a sunflower from seed, planting and watering through roots, sprout, leaves, flower and new seeds. Changing sun/rain palettes, an underground root cutaway, plant-stage drawings and six farm helpers make the growth sequence visually explicit.
- Narration introduces germination, root functions, the ingredients leaves use to make sugars, pollination and the repeating plant life cycle. Three five-second movement moments invite children to grow fingers downward as roots, curl and rise as a sprout, and stretch as leaves.
- The video passed its automated technical gate, full FFmpeg decode, and a visual review of the lifecycle title, all seven stages, all three movement states, and the finale. All environments and plant stages were drawn locally around existing approved animal artwork; zero new image-generation calls were used.
- Its MP4 and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 33 MP4s for private, made-for-kids uploads at four-hour intervals. The immediate dry run reported 32 age-eligible items because the newest story was still inside the configured stability window.
- `COVERED-TOPICS.md` was rebuilt and now records 42 completed or queued concepts.

## Pip's Five Senses Quest checkpoint

- The user identified `reference-generators/create_lost_rainbow_adventure.py` as the desired richer adventure style and clarified that the moving character matters while the location count can vary by topic. The reference producer's useful structure is a moving/blinking/speaking Pip mascot, location travel, two child-like voice deliveries, a real five-second activity gap, a collectible flying back to Pip, continuous music/SFX, and a final payoff.
- On 2026-08-23, the new and topically distinct `Pip's Five Senses Quest` completed at 306.866667 seconds (5:07) and 92,005,932 bytes. Five locations fit the five-senses topic naturally: Looking Lantern Meadow/sight, Whispering Bell Woods/hearing, Fragrant Flower Conservatory/smell, Sunlit Taste Picnic Garden/taste, and Texture Treasure Shore/touch.
- Pip independently floats, bobs, blinks, speaks, waves, travels into and out of each scene, reacts to success, collects a moving sense token, and celebrates with all five orbiting tokens. Narrator and Pip use separate rate/pitch deliveries. Every response gap passed at more than five seconds.
- Seven built-in image-generation calls produced the project visuals. Five final backgrounds were accepted and saved under `automation/production-assets/`; two taste-scene variants with a suspicious mark were rejected and never copied into the project.
- The final video passed its automated 1080p H.264/AAC technical gate, voice-overlap audit, response-gap audit, full FFmpeg decode, and visual review of all arrivals, activities, reward states and finale.
- Its MP4 and metadata were added to `automation/pending-uploads`, bringing the live queue folder to 34 MP4s. The immediate dry run reported 33 age-eligible items because this new file was inside the stability window. `COVERED-TOPICS.md` now records 43 completed or queued concepts.
- The scheduled 16:20 uploader ran while production was held. YouTube returned HTTP 429 for `jungle-animal-clue-detectives-01.mp4`, specifically the daily video-upload quota; the queue item was preserved and a later scheduled cycle can retry. Do not bypass the quota or manually duplicate the upload.

## Pip's Four Seasons Journey checkpoint

- On 2026-08-23, the distinct `Pip's Four Seasons Journey` completed at 279.266667 seconds (4:39) and 86,880,144 bytes. Four locations follow this topic naturally rather than forcing the reference video's scene count: Bud-and-Bloom Garden/spring, Sunny Shade Cove/summer, Whirling Leaf Lane/autumn, and Snowflake Grove/winter.
- Pip independently floats, bobs, blinks, speaks, waves, travels into and out of each setting, reacts to success, collects a moving season token, and celebrates with all four orbiting tokens. Narrator and Pip retain separate rate/pitch deliveries.
- Activities ask children to find three buds, identify shade and water, count five falling leaves, and find three snowflakes plus warm clothes. All four audited response gaps exceed five seconds; summer safety language keeps decisions with a trusted grown-up.
- Four built-in image-generation calls produced four accepted storybook backgrounds with no rejected variants. The accepted files are under `automation/production-assets/four-seasons-*.png` and must be force-added despite the broad PNG ignore rule.
- The final MP4 passed the automated 1080p H.264/AAC gate, voice-overlap and activity-gap audits, full FFmpeg decode, and a visual review of the title, all destinations, prompts, rewards, moving Pip states, and finale.
- Its MP4 and metadata were added collision-safely to `automation/pending-uploads`, bringing the live queue folder to 35 MP4s. The immediate dry run reported 34 age-eligible items because this newest file was inside the configured stability window; the next item remains `jungle-animal-clue-detectives-01.mp4`. `COVERED-TOPICS.md` now records 44 concepts.

## Bea's Healthy Habits Treasure Trail checkpoint

- On 2026-08-23, `Bea's Healthy Habits Treasure Trail` completed at 365.133333 seconds (6:05) and 97,164,751 bytes. It deliberately changes both the character and topic: Bea is a separately drawn flying bee mascot who visits five habit-specific environments rather than reusing Pip or animal choice cards.
- The five destinations are Bubble Brook Wash Garden/handwashing, Sparkle Smile Cove/toothbrushing, Colourful Crunch Picnic/food variety, Wiggle-and-Move Playground/active play, and Cozy Moonlight Nest/sleep routine. Prompts use trusted-grown-up and safe-space guidance without treating one family routine as universal.
- Bea independently flies, bobs, flaps, blinks, speaks, waves, enters and exits each scene, collects five moving pictogram badges, and celebrates with them orbiting. Narrator and Bea use separate rate/pitch deliveries. Every audited response gap is between 5.25 and 5.37 seconds.
- Five built-in image-generation calls produced five accepted, visually distinct storybook environments with no rejected variants. Accepted files are under `automation/production-assets/healthy-habits-*.png` and must be force-added despite the broad PNG ignore rule.
- The final MP4 passed its automated 1080p H.264/stereo AAC gate, voice-overlap and activity-gap audits, full FFmpeg decode, and a visual review of title, all destinations, prompt/reward states, moving Bea, and finale.
- Read-only live verification immediately before queueing returned Tiny Tales channel ID `UCEn9N-ITQHshjgt6fy7fxnw`. The MP4 and metadata were copied collision-safely into `automation/pending-uploads`; the folder now contains 36 MP4s. The immediate dry run found 35 age-eligible items and retained `jungle-animal-clue-detectives-01.mp4` as next. `COVERED-TOPICS.md` now records 45 concepts.

## User-requested generation pause

- At 17:27 on 2026-08-23, the user asked Codex not to create more videos until they change Codex accounts first. Do not resume generation without a new explicit instruction from the user.
- A proposed `Rory's Eight-Planet Postcard Adventure` was stopped before any producer, metadata, rendered output, or pending-queue entry existed. Three preview-only Mercury, Venus, and Earth images remained in Codex's default generated-images area and were never copied into the project. The topic is not listed in `COVERED-TOPICS.md`.
- No Python or FFmpeg process was active at the pause. The latest completed production and queue checkpoint is Bea's Healthy Habits entry above.
- The exact Windows task `Tiny Tales - Continuous Generation` was disabled to enforce the pause before its 20:05 trigger. The independent `Tiny Tales - Daily Private Upload` task remains Ready and unchanged so already-queued private made-for-kids videos can continue at the approved cadence. Re-enable generation only after the user explicitly asks to resume.

## Generation resumed by the new account

- At 17:36 on 2026-08-23, the user explicitly asked the new Codex account to continue from this handoff. This ended the generation pause; it did not alter the retired-format rules or upload safeguards.
- The live `main` worktree was clean at commit `5fda52b` with zero divergence from `origin/main`. There were 36 pending MP4s, 9 archive MP4s, 9 upload-ledger entries, and no active Python or FFmpeg processes.
- The required count-only check reported six completed curated items and one remaining item, `What Farm Animal Disappeared 1`; it generated nothing.
- Read-only YouTube verification matched Tiny Tales and immutable channel ID `UCEn9N-ITQHshjgt6fy7fxnw`. A dry run performed no upload, found 36 queued items, and selected `jungle-animal-clue-detectives-01.mp4` next.
- `Tiny Tales - Continuous Generation` was re-enabled and verified Ready with its next run at 20:05. `Tiny Tales - Daily Private Upload` remained enabled and Ready with its next run at 20:20. Its last result remained `1`, consistent with the recorded YouTube daily upload-quota failure.
- Generation may continue under the existing one-video-per-cycle limit. Do not create animal-shadow videos, and preserve the independent private/made-for-kids upload workflow.

## First resumed generation cycle

- At 17:39 on 2026-08-23, after the user reaffirmed the instruction to keep generating videos, the enabled `Tiny Tales - Continuous Generation` task was started once manually. Its existing mutex and one-video-per-cycle limit remained in force.
- The cycle completed successfully in 102.5 seconds and generated `What Farm Animal Disappeared? | Memory Game 1 for Kids` (`what-farm-animal-disappeared-01`), a 130-second farm-animal memory video.
- `automation/production-work/farm-disappeared-episode-01/quality-report.json` passed all size, duration, video, and audio checks. A full FFmpeg decode returned no errors, and the complete contact sheet was visually reviewed with readable prompts, answer states, and no observed clipping.
- The MP4 and viewer-facing metadata were added to `automation/pending-uploads`, increasing the queue from 36 to 37 MP4s. Generation did not invoke the uploader.
- `COVERED-TOPICS.md` was rebuilt and now records 46 completed or queued concepts. A post-run count-only check reported `What Colourful Bird Disappeared 1` as the next candidate.
- The generation task returned to Ready with exit code `0` and remains enabled for 20:05. Preserve the five-cycle daily schedule and one-video cap, but continue introducing varied non-quiz concepts so disappearance episodes do not become the dominant output.

## Disappearance-memory frequency correction

- After reviewing the first resumed cycle, the user asked that disappearance videos not be created so frequently.
- The old `continuous_item()` fallback in `automation/generation_runner.py` contained five disappearance-only theme slots. It was removed, so completing the curated manifest no longer automatically selects another disappearance episode.
- Existing historical and queued disappearance videos are preserved. Do not delete or regenerate them.
- Scheduled generation remains enabled, but an exhausted curated manifest now completes without producing a video. Add intentionally varied, reviewed manifest items before expecting further output; do not restore a repetitive fallback.
- Future mixed catalogs may use the memory format occasionally, but it must not run consecutively or dominate the rotation. Prefer stories, science, movement, sounds, habitats, kindness, cause-and-effect, and other visually distinct formats.

## Creative-format and narration rotation

- On 2026-08-23, the user clarified that children should not feel that new Tiny Tales videos are the same kind of video with the same voice.
- `automation/voice_profiles.py` defines four verified Edge TTS profiles: `ana-us`, `maisie-uk`, `natasha-au`, and `ryan-uk`. `produce_snack_video.py` now exposes the selected profile to the shared producer family, and `generation_runner.py` passes a stable item seed or explicit manifest profile into each new subprocess.
- New non-legacy manifest items must declare `format_family`, `visual_system`, `interaction_style`, and `voice_profile`. Validation rejects a voice or format family repeated within the previous two new manifest entries. The selected fields are copied into queued metadata for auditability.
- Before designing a new concept, review at least the latest five entries in `COVERED-TOPICS.md` plus live queued metadata. Change the format, interaction, art/layout system, presenter/character, and setting progression—not only the topic or animal family.
- When a story includes a speaking character, use a separate actual voice from the narrator. Pitch/rate variation of one voice alone is not sufficient.
- Existing completed and queued media must not be regenerated merely to retrofit this policy. Apply it prospectively to new productions.

## User-requested varied story roadmap

- `STORY-ROADMAP.md` records the user’s latest directions and distinct treatments: children helping an animal, children playing with star characters to a public-domain “Twinkle” adaptation, a nonviolent ninja-soccer kindness story, an original paintbrush song, a kinder Ant and Grasshopper musical retelling, Five Little Ducks, an original peek-a-boo spatial-language song, a traditional shark-family concept with fully original Tiny Tales arrangement/visuals, an inclusive birthday celebration, and a health-routine rhythm relay distinct from Bea.
- It now also records colour-mixing, breakfast, Dad-coming-home, Mumma-shopping, playing-with-friends, sharing-toys, excavator construction, ice-cream science and fruit-picking concepts, plus an initial set of proactively invented future ideas. Keep expanding the slate without collapsing it into one song or quiz template.
- The roadmap also defines six possible recurring characters unlike Pip: Rory the Rocket, Momo the Mole, Kiko the Kite, Fizz the Bubble, Tavi the Tiny Train and Cora the Coral Polyp. None may reuse Pip’s exact float/travel/token loop.
- Production priority begins with `Maya and the Rainy-Day Joey Rescue`, a child-led animal-helping story with an Australian narrator and a different Maya dialogue voice. Follow it with a different format such as the star-character musical rather than another rescue story.
- Song concepts must use public-domain source material where applicable and new Tiny Tales arrangements, connecting verses, sound design and visuals. Never imitate a modern branded recording or character design.

## Newest-first upload priority

- On 2026-08-23, the user explicitly requested that the uploader choose a recently created video when uploading.
- `automation/config.json` now sets `upload_queue_order` to `newest_first`. `queue_files()` in `automation/uploader.py` sorts stable eligible MP4s by descending modification time and then filename for deterministic ties.
- This priority change preserves the five-minute stability window, technical validation, exact channel verification, private visibility, made-for-kids status, explicit confirmation flag, ledger duplicate checks and unresolved-attempt refusal.
- Dry-run the queue after any ordering change and report the selected filename before relying on the next Scheduled Task.

## Maya and the Rainy-Day Joey Rescue checkpoint

- At 21:29 on 2026-08-23, `Maya and the Rainy-Day Joey Rescue` completed as `maya-rainy-day-joey-rescue-01` at 225.6 seconds. It is a connected child-led wildlife-helping story rather than another disappearance game or theme-swapped quiz.
- The story uses `natasha-au` narration and `maisie-uk` Maya dialogue, independently moving Maya/joey/adult-kangaroo characters, rainy and post-rain sunset park states, and three child activities: give space, slow breathing and gentle finger hops.
- Five built-in image-generation calls produced the accepted project assets listed above. The automated quality gate passed every check, all three response gaps exceeded five seconds, the complete MP4 passed an FFmpeg decode, and the contact sheet was visually reviewed across discovery, helper call, calm waiting, reunion and safety lesson.
- The generation task finished successfully and returned to Ready with exit code `0`. The pending private-upload queue contains 38 MP4s, and `COVERED-TOPICS.md` records 47 concepts. No upload was triggered by generation.
- The upload task remains independent and needs no active Codex session. It is installed for 00:20, 04:20, 08:20, 12:20, 16:20 and 20:20 checks; the computer must remain signed in, network-connected and available to wake. All uploads remain private and made for kids.
- Immediately after generation, the five-minute stability guard correctly excluded Maya and the dry run selected `what-farm-animal-disappeared-01.mp4`. At 21:34, after the guard elapsed, a second dry run selected `maya-rainy-day-joey-rescue-01.mp4` from all 38 eligible items, confirming newest-first behavior without uploading it.

## Nia 3D-look prototype and explicit generation stop

- On 2026-08-23, the user requested an original lively 3D preschool video inspired only by the broad engagement qualities of leading nursery-animation channels, not a copy of any channel's videos, characters, songs, branding, sets, faces or trade dress.
- `Nia's Rainbow Breakfast Dance` completed as `nia-rainbow-breakfast-dance-01` at 150.7 seconds. It teaches red/yellow/blue through an original breakfast chant, six movement pauses and inclusive guidance that breakfast can look different in every family.
- Five built-in image-generation calls produced six consistent Nia poses, two poses each for strawberry/banana/blueberry friends, and three lively kitchen environments. The final method is 3D-rendered pose animation with bounce/tilt, pose switching, parallax and camera motion; Blender was not installed, so this must not be represented as true rigged 3D animation.
- Nia uses `ana-us` and the host uses `ryan-uk`. The technical gate passed, all six quiet response gaps exceed five seconds, the complete MP4 decoded without error, and the corrected contact sheet was visually reviewed after moving the title panel away from Nia's face and speeding up her opening entrance.
- The corrected MP4 and private/made-for-kids metadata are in the pending queue. The queue contains 39 MP4s, and `COVERED-TOPICS.md` records 48 concepts. The immediate dry run excluded Nia during the stability window and selected Maya; after five minutes, a second dry run selected Nia from all 39 eligible videos. Neither dry run uploaded anything.
- After the one deliberate prototype completed, `Tiny Tales - Continuous Generation` was disabled and verified Disabled with last result `0`; no Python or FFmpeg process remained. Do not re-enable automatic generation unless the user explicitly asks. `Tiny Tales - Daily Private Upload` remains enabled and Ready for 00:20, with its prior result `1` preserved from the recorded quota failure.

## Public visibility change and confirmed Nia upload

- At 07:35 on 2026-08-24, the user explicitly requested public uploads instead of private uploads. This applies prospectively to queued/new uploads; it does not mass-publish the historical private backlog.
- `automation/config.json` now uses `privacy_status: public`. `uploader.py` applies configured visibility to the YouTube request, ledger and report; the Outlook report and task installer wording are visibility-neutral/current. Made-for-kids, immutable channel verification, explicit confirmation, stability, technical, duplicate and unresolved-attempt guards remain mandatory.
- The scheduled 00:20 Nia upload reached 11.2% and was interrupted because normal progress on stderr triggered PowerShell's `Stop` behavior. The 04:20 run correctly refused a duplicate. `Run-UploadCycle.ps1` now temporarily sets native invocation error handling to `Continue` and uses the uploader exit code, preventing progress logs from terminating future transfers.
- API investigation found transient ID `63l7E_6iivs` with Nia's exact title/start timestamp but no processed duration; subsequent exact-ID and uploads-playlist checks confirmed YouTube discarded it. The attempt was marked `failed_confirmed_absent` only after those live checks.
- The explicit retry succeeded as `ygc-y4_XBwk` (`https://youtu.be/ygc-y4_XBwk`). Read-back matched Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`, the exact title/description/seven tags, 2:31 duration, public visibility, made-for-kids and self-declared-made-for-kids flags. The uploader ledger recorded success and archived the canonical MP4/metadata; the pending queue now contains 38 MP4s.
- The upload Scheduled Task remains enabled under its historical name `Tiny Tales - Daily Private Upload`; despite that name, configured behavior is now public. Automatic generation remains disabled.

The latest upload is Nia video `ygc-y4_XBwk`, read back as public and made for kids on the exact Tiny Tales channel. Email reporting is separate from upload success and must not cause a duplicate retry.

## Hourly retry task and resumed creation

- At 08:13 on 2026-08-24, the user asked for failed uploads to retry hourly without changing the regular four-hour schedule. The original task still has exactly its six triggers at 00:20, 04:20, 08:20, 12:20, 16:20 and 20:20.
- The new enabled `Tiny Tales - Hourly Upload Retry` task has the 18 intervening hourly triggers and next runs at 09:20. It uses `Run-UploadCycle.ps1 -RetryOnly`, the same global mutex, and `runtime/upload-retry-state.json`.
- A retry is armed only for a failure that is safe to repeat without duplicate risk, and it targets the exact failed filename. Quota/upload-limit rejection is automatically retryable; an ambiguous interrupted insert remains protected by the attempt journal and requires live reconciliation.
- Reporting email failure is logged separately and no longer changes upload success or triggers another video upload. Static Python compilation, PowerShell parsing and an empty-state `-RetryOnly` skip test passed before task installation.
- The user then explicitly asked to continue video creation. `Animal Action Alphabet A-Z` is recorded in `STORY-ROADMAP.md` and is the active original 3D-look build using `maisie-uk`; automatic generation was still Disabled at this checkpoint while the curated producer/assets were being prepared.

## Animal Action Alphabet and Brio workshop completion

- `Animal Action Alphabet A-Z` completed as `animal-action-alphabet-a-to-z-01` at 330.4 seconds. It uses `maisie-uk`, 26 individual animal sprites, five generated 3D world stages, code-driven movement/camera/action trails and 26 audited 4.8-second response gaps. The producer is `automation/production/produce_animal_action_alphabet.py`; its ten accepted `animal-action-*` assets are in `automation/production-assets`.
- The animal video passed 1080p H.264/stereo AAC checks, a full FFmpeg decode and visual inspection of a complete A-Z contact sheet. It is queued public/made-for-kids behind the current newest item.
- `Brio's Paintbrush Colour Workshop` then completed as `brio-paintbrush-colour-workshop-01` at 154.1 seconds. It uses `ryan-uk`, six consistent Brio poses, five accepted colour-drop friends, four generated art environments, code-painted canvas marks, colour mixing and ten participation gaps of at least five seconds. Its producer is `automation/production/produce_brio_paintbrush_workshop.py`; accepted `brio-*`, `paint-drop-*` and `paintbrush-*` assets remain in `automation/production-assets`.
- Brio also passed its quality gate, full decode and contact-sheet review. At 09:04, the dry run found 39 eligible public queue items and selected `brio-paintbrush-colour-workshop-01.mp4` newest-first. Animal Action is immediately behind it. `COVERED-TOPICS.md` now records 50 concepts.
- The 08:20 scheduled cycle independently uploaded `maya-rainy-day-joey-rescue-01.mp4` successfully as public/made-for-kids video `HtNGbHueDKQ`; the Outlook report was confirmed and the retry state was cleared. The archive has 11 MP4s.
- `Tiny Tales - Continuous Generation` was re-enabled by the user's explicit resume request and is Ready for 10:05 with last result `0`. All ten curated manifest entries are complete, so scheduled generation now safely exits without producing anything until a new varied, reviewed manifest item is added. Do not restore automatic disappearance generation.

## Dedicated Google Cloud/OAuth migration

- At 18:44 on 2026-08-24, the user replaced the Tiny Tales Desktop OAuth client with one from new dedicated Google Cloud project `tiny-tales-506508`. Tiny Tales had previously shared project `cool-artwork-506302-q0` with the user's Birthday channel, causing the project's `Video Uploads per day` limit to be consumed across both automations.
- This is a one-time channel/credential isolation change, not quota sharding. The new Cloud project, OAuth client, token, quota, immutable channel lock, ledger, archive and Scheduled Tasks belong only to Tiny Tales. Never use them for the Birthday channel, and never rotate projects to evade a quota or channel-level upload limit.
- Both upload tasks were disabled before token replacement. The prior OAuth token was moved without deletion to ignored backup `automation/runtime/credential-backups/youtube-oauth-token.pre-dedicated-project-20260824.json`; never print or copy its contents.
- The first authorization reached Google but correctly failed closed because YouTube Data API v3 was not enabled. After the user enabled the API, interactive authorization succeeded and returned Tiny Tales channel ID `UCEn9N-ITQHshjgt6fy7fxnw`. A separate `uploader.py verify` call returned the same immutable identity.
- The post-migration dry run performed no upload, found 38 queued MP4s, and selected `animal-action-alphabet-a-to-z-01.mp4` under public/made-for-kids configuration. Retry state was unarmed. `Tiny Tales - Daily Private Upload` and `Tiny Tales - Hourly Upload Retry` were then re-enabled and verified Ready for 20:20 and 19:20 respectively.
- The live archive and upload ledger each contain 12 confirmed items. The newest confirmed upload is public/made-for-kids Brio video `xmY61TirVWE`, which completed at 18:25 before the credential migration.

## Maya defect correction, replacement upload and mandatory future transition QA

- The user reported that Maya's intended final card, `KINDNESS CAN MAKE A DIFFERENCE`, flashed every few seconds throughout the story. Frame extraction from the archived upload confirmed it at 45.95 seconds, matching an uncovered timeline interval from 45.858 to 46.108 seconds.
- Root cause was deterministic: `build_timeline()` left 22 pauses of 0.25 or 0.35 seconds, while `render()` used `events[-1]` (the end card) whenever no event covered a timestamp. The original contact sheet sampled scene interiors and therefore missed every gap.
- `automation/production/produce_maya_joey_rescue.py` now extends each visual event through its intended pause, making all 23 transitions exactly contiguous. Rendering fails closed if any timestamp lacks an event. Its quality report now requires `continuous_visual_timeline` and `end_card_is_final_event_only`, and `timeline-gap-audit.json` records every boundary.
- A new 225.6-second, 43,751,353-byte corrected MP4 was rendered with SHA-256 `6f8b263144d22b0375e0a6caebade1eaafa49d3c082969bb8f595ae66e4721af`. It passed the expanded producer gate, 1080p H.264/48 kHz stereo AAC checks, full FFmpeg decode, normal contact sheet, and visual review of `transition-contact-sheet.png`, which sampled all 22 former flash timestamps and showed only the correct adjacent story scenes.
- Exact read-back verified defective upload `HtNGbHueDKQ` as the Maya title on immutable Tiny Tales. It was public at initial diagnosis and read as private immediately before deletion. One `videos.delete` request was sent; the immediate read was briefly stale, so no retry was attempted. A delayed exact-ID query confirmed it absent, and a full uploads-playlist scan confirmed zero exact-title matches before replacement.
- The corrected collision-safe queue item uploaded publicly as `WLzesx1OxNU` (`https://youtu.be/WLzesx1OxNU`). API read-back matched Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`, exact title and description, seven tags, 3:46 duration, public visibility, made-for-kids and self-declared-made-for-kids flags. The corrected archive is `automation/archive/maya-rainy-day-joey-rescue-01-corrected.mp4`; the defective original archive remains preserved as `automation/archive/maya-rainy-day-joey-rescue-01.mp4` for audit/recovery and must never be re-uploaded.
- The separate one-time `youtube.force-ssl` deletion token was revoked and its temporary token/helper files removed. Google also invalidated the normal grant for the same OAuth client, so the user completed a fresh authorization requesting only the original `youtube.upload` and `youtube.readonly` scopes. A final channel verification passed.
- At the user's request, all future Tiny Tales videos created after Unix cutoff `1787563445` (`2026-08-24T09:24:05Z`) are subject to a new fail-closed uploader gate. `automation/config.json` records the cutoff. `uploader.py` requires queue metadata flags `quality_gate_passed`, `full_decode_passed`, `transition_audit_passed`, and `transition_contact_sheet_reviewed`, plus valid in-project paths `quality_report`, `transition_audit`, `quality_contact_sheet`, and `transition_contact_sheet`. The producer report must pass and explicitly prove a continuous timeline and final-only end card; every audit interval must be zero. Every real upload also runs a fresh full FFmpeg decode. Existing pre-cutoff backlog items are preserved and grandfathered.
- A deliberate future-dated missing-evidence test was blocked with all four absent flags named. The next pre-existing dry-run item is `animal-action-alphabet-a-to-z-01.mp4`; 38 MP4s remain queued.
- Sydney-time upload history on 2026-08-24: Nia succeeded at 07:45, Maya defective upload succeeded at 08:20 and was later deleted/replaced, Brio succeeded at 18:25, and corrected Maya succeeded at 19:23. The corrected Maya replacement is the newest confirmed upload.

## Brio defect correction and replacement upload

- The user reported that `Brio's Paintbrush Colour Workshop` jumped between visuals too frequently. Diagnosis of the archived upload found two deterministic renderer defects: `brio_pose = int(t * 2.5) % 6` hard-swapped among six unrelated poses every 0.4 seconds for most of the 154-second video, and 20 uncovered 0.3-second timeline gaps fell back to `events[-1]`, flashing the final `ONE BRAVE LITTLE MARK` card during the story.
- `automation/production/produce_brio_paintbrush_workshop.py` now assigns a stable intentional Brio pose by scene phase, uses gentler bob/tilt motion, extends each visual event through its pause so the timeline is contiguous, and raises instead of displaying the end card if any timestamp lacks an event. The estimated hard-pose swaps fell from 372 to 13 intentional scene changes, approximately 5.064 changes per minute.
- The corrected 154.1-second, 36,680,927-byte render has SHA-256 `9773b722f1d9e43b03116f88c786b2fa000f9692ec5639d37573aeaa32a47aa1`. It passed 1080p H.264/48 kHz stereo AAC checks, full FFmpeg decode, all producer quality checks, a 21-boundary zero-gap audit (maximum floating-point residual `2.842e-14` seconds), the general contact sheet, every-boundary transition contact sheet, and a focused corrected-pose cadence contact sheet. A scene-change comparison found 13 high-change frames in the corrected video versus 38 in the defective archive.
- Exact read-back verified the defective Tiny Tales upload as `xmY61TirVWE`. After explicit user approval, a channel/title-locked one-time deletion sent exactly one delete request and confirmed the ID absent. A subsequent exact-ID and exact-title search found no remaining copy before replacement, preventing a duplicate.
- The corrected collision-safe queue item uploaded publicly as `yUCTNP3pJxg` (`https://youtu.be/yUCTNP3pJxg`). Its canonical corrected archive is `automation/archive/brio-paintbrush-colour-workshop-01-corrected.mp4`. Preserve the defective original archive `automation/archive/brio-paintbrush-colour-workshop-01.mp4` for audit/recovery and never upload it again.
- Independent API read-back after YouTube processing succeeded matched the immutable Tiny Tales channel, exact title and description, all seven tags, 2:35 duration, public visibility, and made-for-kids status. The archive and ledger each contain 14 confirmed items; 38 MP4s remain pending, and the post-replacement dry run selects `animal-action-alphabet-a-to-z-01.mp4` next without uploading it.
- The temporary `youtube.force-ssl` credential was revoked and removed. The normal OAuth authorization was then recreated with only `youtube.upload` and `youtube.readonly`, and channel verification returned immutable Tiny Tales ID `UCEn9N-ITQHshjgt6fy7fxnw` before the replacement upload.
- `Tiny Tales - Daily Private Upload` and `Tiny Tales - Hourly Upload Retry` were paused throughout diagnosis/replacement and restored to Ready afterward. `Tiny Tales - Continuous Generation` is also Ready; the curated manifest remains exhausted, so generation safely no-ops until a deliberately varied item is added.

## Standing authorization for defective-video replacement

- On 2026-08-24, the user said they do not want a separate authorization request every time a defective Tiny Tales upload must be deleted. A clear instruction to fix and replace or re-upload a defective Tiny Tales video now includes authorization to delete that exact verified live version; do not ask a redundant conversational confirmation.
- This standing permission is narrow. Verify the immutable Tiny Tales channel, exact video ID and exact expected title immediately before one delete request, confirm absence before uploading the correction, and never use it for batch deletion, unrelated videos, or a request that only asks for diagnosis/local editing.
- No Scheduled Task may delete videos. A persistent broad deletion credential was not created; provider, operating-system or sandbox security prompts may still be required when a future deletion occurs and must not be bypassed.

## Custom thumbnails for live Tiny Tales automation uploads

- At the user's request, video generation was paused while custom thumbnails were created for every automation-ledger upload that is still live on Tiny Tales. The channel contains 142 historical videos, including unrelated legacy material; scope was therefore restricted to the 12 live videos recorded by this project's upload ledger. No unrelated historical upload was changed.
- `automation/thumbnail-manifest.json` locks each thumbnail to an exact video ID, exact expected title, archived source video, representative timestamp, wording and layout. `automation/generate_thumbnails.py` deterministically produces 1280x720 JPEGs under `automation/thumbnails` from truthful video frames. `automation/thumbnail_uploader.py` requires an explicit confirmation flag, verifies dimensions/file size, the immutable channel, every exact ID/title, and records successful sets in ignored `runtime/thumbnail-upload-ledger.jsonl`.
- All 12 thumbnails were visually reviewed together, uploaded successfully, fetched back from YouTube at 1280x720, pixel-compared with the local reviewed files, and visually reviewed again as a served contact sheet. Every comparison passed with RMS difference between 2.197 and 3.368, consistent with YouTube JPEG recompression.
- The covered live IDs are `zAR5CkV2MMo`, `HSU5icdAnSs`, `gGQHkHcswGg`, `_a50NuDSRPQ`, `3z6kDg0DXmo`, `fvtpuEGx5Vw`, `gqeS_ZdmQ6Q`, `-ayS0UTmcfA`, `ygc-y4_XBwk`, `WLzesx1OxNU`, `yUCTNP3pJxg`, and `DTLx7vnHwd8`. Future confirmed Tiny Tales uploads should receive the same content-specific, reviewed and served-back-verified thumbnail treatment.

## Paused next-generation concept

- Before the thumbnail priority change, work began on `Tavi the Tiny Train's Shape Delivery Day`, a distinct connected sequencing story teaching first/next/then/last and circle/square/triangle/rectangle through community deliveries. It uses a side-scrolling toy-railway visual system and stable deterministic Tavi/cargo motion rather than a quiz, rescue, alphabet parade or paint song.
- Four original built-in image-generation backgrounds are preserved locally as `automation/production-assets/tavi-shape-depot-3d.png`, `tavi-music-garden-3d.png`, `tavi-reading-nook-3d.png`, and `tavi-playground-3d.png`. A fifth garden/finale scene, producer, manifest entry, narration and render do not yet exist. Do not regenerate or overwrite the four accepted backgrounds.
- `Tiny Tales - Continuous Generation` is Disabled while this work is paused. The two upload tasks remain Ready. When video generation resumes, complete Tavi under the mandatory full-decode, continuous-timeline, final-card-only, transition-audit and both-contact-sheet review gates before queueing it.

## Creative thumbnail refresh and Tavi completion

- The initial frame-layout thumbnail set was replaced on 2026-08-24 with a substantially more colourful version-2 set. Twelve distinct built-in image-generation artworks were derived from representative real video frames, without generated text; `generate_thumbnails.py` adds the exact short hooks deterministically. The reviewed source artwork is under `automation/thumbnail-artwork/*-v2.png`, and `thumbnail-manifest.json` records the exact video/title/artwork/hook mapping.
- All 12 replacement JPEGs were uploaded to the immutable Tiny Tales channel, fetched back with cache-busting, verified at 1280x720, and visually reviewed as one served contact sheet. RMS comparison against the local reviewed files ranged from 2.179 to 4.941, consistent with YouTube recompression.
- `Tavi the Tiny Train's Shape Delivery Day` is no longer paused. Five built-in image-generation calls produced the accepted depot, music garden, reading nook, playground, and community garden environments. `automation/production/produce_tavi_shape_delivery.py` renders stable code-animated Tavi/cargo motion over those scenes; it is not true rigged 3D animation.
- The completed MP4 is 226.6 seconds. Its producer quality report passed, a second independent full FFmpeg decode returned no errors, all 27 timeline boundaries are exactly contiguous, the end card occurs only in the final event, and both the general and every-boundary transition contact sheets were visually reviewed. The reviewed queue sidecar contains the mandatory post-cutoff evidence and is ready for the normal scheduled public made-for-kids upload.
- `generation_runner.publish()` now merges producer evidence fields into the upload sidecar, preventing future post-cutoff renders from reaching the uploader without their quality artifacts. The continuous-generation task was re-enabled by the user's explicit request and was Ready alongside both upload tasks. All 11 curated items are currently complete, so the next cycle will no-op until another varied, reviewed concept is deliberately added; do not restore the repetitive disappearance fallback.

## Tavi feedback and newly planned Star Friends video

- On 2026-08-25 the user said Tavi's visuals stayed the same for most of the video and its narration did not feel synchronized. Tavi had already uploaded publicly as `GUO4zUZDbVo`. The user explicitly asked not to repair it and instead requested a different video planned again from scratch. Tavi was not deleted, edited or replaced.
- `metadata/star-friends-twinkle-playground-01-plan.json` was written before production. It maps 13 exact narration lines to 13 unique visual compositions and explicit motion, limits story shots to 14 seconds, forbids instructional panels during the story, and requires narration containment and semantic shot review.
- Thirteen separate built-in image-generation calls created the accepted assets `automation/production-assets/star-friends-01-arrival.png` through `star-friends-13-goodnight.png`. The prompt set preserved one original trio—a golden star with coral cheeks, mint star with round glasses, and lavender star with a teal scarf—across arrival, playground activation, two trampoline views, two seesaw views, two comet-slide views, two constellation-path views, finale, bedtime breath and goodnight. No generated text or outside brand imagery was used.
- `automation/production/produce_star_friends_twinkle_playground.py` completed the 116.4-second 1080p video using `ana-us`, original synthesized music, continuous per-shot camera moves and subtle sparkle motion. Each narration begins exactly with its assigned visual. `narration-visual-sync-audit.json` proves all narration ends inside the matching visual; the producer also proves 13 unique story assets and no shot over 14 seconds.
- The producer quality gate, independent full FFmpeg decode, 14-boundary zero-gap audit, final-only end card, general contact sheet and every-boundary contact sheet all passed visual review. The queue sidecar's review flag is true and its post-cutoff evidence validates. The video is ready for the normal scheduled public made-for-kids upload; it has not been uploaded manually in this session.

## Relevant custom thumbnail enforcement and recent repairs

- On 2026-08-25 the user explicitly required a relevant, amazing custom thumbnail on every Tiny Tales upload and asked to repair recent misses. The upload/thumbnail ledger audit found three missing recent IDs: Tavi `GUO4zUZDbVo`, farm disappearance `dui6_QeKMFc`, and Bea `3c5rj6In7pQ`.
- Three separate built-in image-generation calls used truthful video frames as references and produced no text: a teal garden train carrying circle/square/triangle/rectangle parcels; four expressive farm animals around a glowing missing-animal silhouette; and Bea following five visual healthy-habit badges. The final artwork is `automation/thumbnail-artwork/<video-id>-v2.png`; deterministic exact hooks are rendered by `generate_thumbnails.py`.
- The final hooks are `SHAPE DELIVERY!`, `WHO DISAPPEARED?`, and `HEALTHY HABIT QUEST!`. All three 1280x720 JPEGs were visually reviewed, uploaded only after exact video ID/title/channel verification, fetched back through YouTube's API-provided max-resolution URLs, pixel-compared, and visually reviewed together. Served RMS values were 3.859, 2.730, and 4.242 respectively.
- `thumbnail_uploader.py` now accepts repeated `--video-id` filters so repairs can target exact manifest entries without reapplying unrelated thumbnails. `verify_served_thumbnails.py` verifies exact ID/title/channel, uses signed URLs for private videos, requires 1280x720, compares served pixels, and produces a contact sheet.
- Live YouTube state at about 15:00 Australia/Sydney reported Tavi processed/made-for-kids but private, conflicting with the historical public ledger. No visibility mutation was authorized or made; preserve live state unless the user directs otherwise.
- `automation/config.json` now requires a prepared custom thumbnail for every future upload. Queue entries lacking `prepared_thumbnail`, an exact `thumbnail_hook`, `thumbnail_reviewed: true`, a valid 1280x720 JPEG, or the 2 MB limit are excluded rather than uploaded. The 35 older queued videos remain preserved and held for thumbnail preparation.
- If a video insert succeeds but `thumbnails.set` fails, the uploader writes the exact ID/title/source/thumbnail to ignored `runtime/thumbnail-retry-state.json`. Subsequent real cycles service this repair before any new video and clear it only after YouTube confirms the thumbnail; they never retry the already-recorded video upload.
- Star Friends is ready with reviewed `automation/thumbnails/star-friends-twinkle-playground-01.jpg` and hook `PLAY WITH THE STARS!`. Its sidecar carries the prepared-thumbnail fields. The current dry run reports Star Friends as the only eligible next upload; after YouTube returns its new ID, the uploader will set the prepared thumbnail immediately and record it separately.

## Visual-quality baseline confirmed by user (2026-08-25)

- The user explicitly asked that all future Tiny Tales visuals maintain the same quality as the recent Star Friends production and colourful custom-thumbnail artwork. This is now a permanent production requirement, not a one-off preference.
- Future videos must be planned narration beat by narration beat, use premium original 3D-style compositions with expressive consistent characters, dimensional lighting, rich colour and depth, and change to a materially new matching composition about every 6 to 10 seconds in energetic passages. No story shot may exceed 14 seconds without meaningful internal visual progression.
- Every generated asset must be reviewed and weak, inconsistent, cluttered, misleading, or generic variants rejected. Motion must feel continuous and purposeful; do not recreate Tavi's long static stretches or Brio's rapid pose flicker.
- Every upload must include a truthful, colourful, cinematic custom thumbnail with a strong focal moment and short deterministic hook. The existing sync, zero-gap, full-decode, contact-sheet, and thumbnail gates must fail closed if the result does not meet this baseline.

## Tavi deletion and Star Friends upload checkpoint (2026-08-25 21:43 Australia/Sydney)

- While the deletion workflow waited for a safe window, the scheduled uploader completed `Star Friends' Twinkle Playground` publicly as `I7ZMQh9BoHE` and immediately applied its reviewed `PLAY WITH THE STARS!` custom thumbnail. The upload report, video ledger, and thumbnail ledger all record the confirmed result.
- At the user's explicit request, exact Tiny Tales video `GUO4zUZDbVo`, `Tavi the Tiny Train's Shape Delivery Day | Shapes and Sequencing for Kids`, was verified immediately before deletion as private, made for kids, 3:47 long, and owned by immutable channel `UCEn9N-ITQHshjgt6fy7fxnw`. Exactly one `videos.delete` request was sent. The deletion helper confirmed the ID absent, and a second independent exact-ID query using the restored limited credential also confirmed it absent.
- The temporary `youtube.force-ssl` grant was revoked and not retained. As expected, Google also revoked the normal grant for the same OAuth client; the user completed a new authorization requesting only `youtube.upload` and `youtube.readonly`, and the uploader verified it against Tiny Tales before automation resumed.
- Preserve `automation/archive/tavi-shape-delivery-day-01.mp4`, its artwork, thumbnail, upload-ledger row, and `runtime/delete-tavi-report.json` for audit. Tavi was removed from `thumbnail-manifest.json` because its YouTube ID is no longer live. Never re-upload the deleted Tavi source.

## Three-hour upload cadence and generation state (2026-08-25)

- The user explicitly requested a normal Tiny Tales upload opportunity every three hours. The regular task now uses 00:20, 03:20, 06:20, 09:20, 12:20, 15:20, 18:20, and 21:20 Australia/Sydney. The retry-only task moved to the 16 intervening hourly slots and cannot select unrelated content.
- All channel-lock, public/made-for-kids, duplicate, retry, stability, full-decode, visual-quality and mandatory custom-thumbnail safeguards remain fail-closed. A scheduled slot uploads nothing when no eligible reviewed video exists or when YouTube rejects the upload limit/quota.
- Live count-only generation state returned 12 completed curated items, zero remaining and zero failed. The continuous-generation task is enabled but currently no-ops because the manifest is exhausted. New deliberately varied concepts must be planned and produced at the Star Friends quality baseline before the faster upload cadence can be supplied safely.
- The live task update was verified with eight normal triggers at `00:20, 03:20, 06:20, 09:20, 12:20, 15:20, 18:20, 21:20` and 16 retry-only intervening triggers. Both tasks were Ready; the next normal upload check was 2026-08-26 00:20 Australia/Sydney.
- A post-change uploader dry run attempted no upload and returned `next_video: null`, `remaining_upload_count: 0`. Thirty-five preserved backlog MP4s were excluded because they lack reviewed prepared thumbnails; do not treat them as eligible merely to fill the faster schedule. Publish them only if every current visual, sync, transition, decode and thumbnail gate is genuinely completed.

## Complete legacy-backlog thumbnail release (2026-08-26)

- `automation/backlog-thumbnail-plan.json` now channel-locks all 35 preserved legacy queue items to exact local artwork, deterministic short hooks, hook placement and accent colours. `automation/prepare_backlog_thumbnails.py` validates the plan, source metadata, image dimensions and 2 MB limit; renders the JPEGs and one review sheet; and updates only still-pending sidecars after the explicit `release-reviewed` command. Archived items are skipped rather than reintroduced.
- Sixteen accepted first-batch artworks and nineteen continuation artworks are stored locally under `automation/thumbnail-artwork/backlog/*-v1.png`. The continuation artwork was generated with the built-in image tool from review frames extracted from each real video. Each prompt preserved the real animal, lesson or interaction, requested premium original cinematic 3D-style preschool presentation, reserved clean hook space, and prohibited generated text, logos, watermarks, copyrighted characters and brand styling.
- All 35 deterministic 1280x720 JPEGs are under `automation/thumbnails/<source-id>.jpg`. The combined review sheet is ignored runtime evidence at `automation/runtime/backlog-thumbnail-review-contact-sheet.jpg`. Visual review confirmed readable exact hooks, truthful concepts, no generated text/branding, and exactly four visible animals in each counting-parade thumbnail.
- The release step updated 32 still-pending metadata sidecars. Three planned videos had already archived through the authorized scheduler: `Pip's Four Seasons Journey` as public/made-for-kids `KT6ezPwGYZI`, `Pip's Five Senses Quest` as `eCGiwPW_SF4`, and `The Tiny Seed's Big Farm Adventure` as `uXSMNcg-u10`. The video and thumbnail ledgers record all three successful thumbnail applications.
- The post-release uploader dry run attempted no upload, reported 32 eligible items and selected `animal-shape-builders-01.mp4` next. The immutable OAuth verification still returned Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`; generation count-only remains 12 completed, zero remaining and zero failed.
- At the live checkpoint, all three tasks were Ready with result `0`. The normal uploader's next slot was 21:20 Australia/Sydney on 2026-08-26, the retry-only task's next slot was 22:20, and generation remained an exhausted-manifest no-op. Preserve the existing public/made-for-kids, channel-lock, duplicate, retry, quality and thumbnail gates.

## Animal Sound Orchestra correction and replacement (2026-08-27)

- The user reported that the live Animal Sound Orchestra attracted viewers but every introduced animal remained motionless on stage. Diagnosis of the archived 3:13 source and `automation/production/produce_animal_sound_orchestra.py` confirmed that reveal events pasted each sprite at one fixed position/size; only background notes moved, and the animal received a small pulse only during the later response window.
- The corrected producer now gives all eight performers distinct continuous actions and entrances: Cow stomps/sways, Sheep trots, Pig snuffles, Chicken hops/taps, Lion prowls, Elephant marches, Owl hovers, and Parrot dances. The concert stage now uses moving multicolour lights, bunting, confetti, richer palettes and animated sound effects. All eight animals share the stage during the opening, welcome, original Tiny Tales opening chant/song, original four-part finale song and final bow.
- The revised welcome explicitly invites children to meet each performer and tune in for the fantastic song at the end. The final description and tags now accurately mention the original Animal Sound Song, movement, and eight performers. No new image-generation calls or outside music were used; the instrumental arrangement is deterministically synthesized by the producer.
- The corrected output is 240.8 seconds with SHA-256 `fb8c1ff04acaf386d63df7ad61bbdd7b8e719aaa2c8a5c0b65fffa60689d70e2`. It passed 1080p H.264/48 kHz stereo AAC checks, a full FFmpeg decode, exact continuous-timeline and final-only bow checks, narration containment for all 16 voice segments, eight response windows, and an explicit performer-motion audit proving five distinct sampled poses for every animal. Both the general and every-boundary contact sheets were visually reviewed.
- The defective public/made-for-kids Tiny Tales upload `h1Xb7Pou1ks` was verified immediately before deletion against immutable channel `UCEn9N-ITQHshjgt6fy7fxnw`, exact expected title and 3:13 duration. Exactly one delete request was sent using a temporary `youtube.force-ssl` credential and the ID was confirmed absent after one read-only poll. `automation/runtime/delete-animal-sound-report.json` records the operation; the original archive remains preserved and must never be uploaded again.
- The temporary deletion grant was revoked and its token/log/helper removed. The normal grant was then restored with only `youtube.upload` and `youtube.readonly` and verified against Tiny Tales before replacement. The collision-safe queue source uploaded publicly as `f1SPRanqUEg` (`https://youtu.be/f1SPRanqUEg`) and archived as `automation/archive/animal-sound-orchestra-01-corrected.mp4`.
- Independent API read-back confirmed processing succeeded, exact title/revised description/nine tags, 4:01 duration, public visibility, made-for-kids and self-declared-made-for-kids status. The existing reviewed `ANIMAL SOUND SHOW!` custom thumbnail was applied immediately; its served max-resolution image was 1280x720, visually reviewed, and differed from the local JPEG by RMS 3.792, consistent with YouTube recompression.
- Both upload tasks were disabled throughout packaging/deletion/replacement and restored to Ready afterward. The post-replacement dry run attempted no upload, reported 28 eligible items and selected `bird-feather-measuring-studio-01.mp4` next. Preserve both the defective and corrected archives and never retry either ledgered upload.

## Fifteen-minute backlog uploads and new-set start (updated 2026-08-28)

- The user explicitly changed the backlog upload gap to fifteen minutes on 2026-08-28. Live task `Tiny Tales - Daily Private Upload` uses one long-running repeating `PT15M` trigger, anchored to a future fifteen-minute boundary rather than a past midnight boundary. Each run still uploads at most one item through the existing uploader and global mutex. The migration and installer use a 3650-day repetition duration so the cadence does not expire after one day.
- Because every normal cycle checks `runtime/upload-retry-state.json` first and retries the exact duplicate-safe failed source before considering a newer item, the separate `Tiny Tales - Hourly Upload Retry` task is Disabled rather than deleted. This prevents competing schedules. `automation/Install-TinyTalesTasks.ps1` records the same design for new installs, and `automation/Set-TinyTalesFifteenMinuteUploads.ps1` safely migrates existing tasks only after verifying their exact actions.
- The faster cadence does not bypass the immutable Tiny Tales channel lock, explicit confirmation flag, public/made-for-kids status, newest-first order, duplicate and unresolved-attempt guards, five-minute stability, full-decode gate, post-cutoff quality evidence, mandatory reviewed custom thumbnail, or YouTube limits. A held, empty, quota-rejected or ambiguous queue must still no-op or fail closed.
- Live verification found the laptop on battery and the historical task settings blocking battery starts, which caused earlier trigger boundaries to advance without launching. The migration and fresh installer allow this upload task to start and finish on battery; network availability, `IgnoreNew`, the global mutex and the 45-minute execution limit remain active.
- The first corrected live slot launched at exactly 14:00 Australia/Sydney and completed with task result `0` in 47 seconds. It uploaded `Bird Feather Measuring Studio | Long and Short for Kids` publicly/made-for-kids as `D6-ogBhG368`, applied reviewed thumbnail `automation/thumbnails/bird-feather-measuring-studio-01.jpg`, verified immutable Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`, archived the source, and reduced the eligible queue from 28 to 27. A post-run dry run performed no upload and selected `farm-barn-height-lineup-01.mp4` next; the following scheduled slot was 14:10.
- The user also authorized a new varied video set. `metadata/new-set-plan-2026-08-27.json` fixes three intentionally different productions and voices: `The Cardboard Box Invention Club` (`maisie-uk`, collaborative imagination transformation story), `Niko's Ninja Soccer Kindness Match` (`ryan-uk`, sports teamwork), and `The Ant and the Grasshopper's Shared Harvest` (`natasha-au`, season-changing musical fable).
- Cardboard Box is the active first production. Six built-in image-generation calls produced accepted 1672x941 premium 3D-style scenes under `automation/production-assets/cardboard-box-*-v1.png`: opening build, pretend bus, gentle cave, puppet theatre, reading nook and finale. Visual review of `automation/production-work/cardboard-box-invention-club-01/asset-contact-sheet.png` confirmed consistent identities for all three children, recognizable box continuity, progressive colourful lighting, and a distinct visible action for every child in every scene.
- The tracked asset review is `metadata/cardboard-box-invention-club-01-asset-review.json`. Production later completed successfully as described in the checkpoint below; preserve this earlier asset-stage history but use the completion checkpoint for current state.

## Cardboard Box completion and lead-voice rule (2026-08-27)

- The user requires visually strong, narration-synchronized videos and a different lead voice in every consecutive production. `AGENTS.md` now makes adjacent lead-voice changes mandatory and retains the rule that a profile cannot recur within the next three new videos. The planned sequence is Cardboard Box `maisie-uk`, Niko `ryan-uk`, and Ant/Grasshopper `natasha-au`, with separate character voices for dialogue-heavy stories.
- `The Cardboard Box Invention Club | Imagination Story for Kids` completed as `cardboard-box-invention-club-01` at 89.2 seconds. Its exact plan is `metadata/cardboard-box-invention-club-01-plan.json`; producer is `automation/production/produce_cardboard_box_invention_club.py`.
- Six voiced beats use six unique premium 3D-style full-screen compositions. Each visual begins exactly with its matching narration and contains that narration to completion. All shots are at most 13.98 seconds, all seven boundaries have zero gaps, and the final card is the final event only. Continuous camera travel and scene-specific action overlays keep the children visibly steering, exploring, performing, reading and celebrating.
- The 1920x1080 H.264/48 kHz stereo AAC output passed the producer gate and a second independent full FFmpeg decode. The general contact sheet, every-boundary transition sheet, narration-sync audit and truthful 1280x720 `ONE BOX, FOUR WORLDS!` thumbnail were visually reviewed and approved. Queue sidecar evidence contains all mandatory true flags and valid artifact paths.
- The curated manifest now has 13 completed items, zero remaining and zero failed. Generation runner released the stable output to the public/made-for-kids queue without rendering again. The immediate dry run performed no upload; Cardboard Box was correctly excluded by the five-minute stability guard while 26 existing reviewed items remained eligible.

## Niko soccer local completion (2026-08-27)

- `Niko's Ninja Soccer Kindness Match | Teamwork Story for Kids` completed locally as `niko-ninja-soccer-kindness-match-01` at 104.8 seconds. The exact eight-shot plan is `metadata/niko-ninja-soccer-kindness-match-01-plan.json`; the producer is `automation/production/produce_niko_ninja_soccer.py`.
- Eight unique built-in-generated premium 3D-style compositions directly show Niko welcoming Lila, balance focus, cone dribbling, a gentle pass, Lila's first touch, triangle passing, kind recovery after a missed shot, and the shared goal. The tracked asset review is `metadata/niko-ninja-soccer-kindness-match-01-asset-review.json`.
- Ryan (`ryan-uk`) is the narrator and Ana (`ana-us`) gives Niko a genuinely distinct dialogue voice. All spoken segments begin and finish inside their matching artwork; every story shot is at most 13.75 seconds. The continuous timeline, final-card-only rule, H.264/1080p/stereo AAC checks, two full decodes, general contact sheet, every-boundary contact sheet, sync audit, and 1280x720 `PASS, MOVE, SHARE!` custom thumbnail passed review.
- The normal generation runner preserved the already-rendered output, marked all 14 curated items complete with zero failures, and released Niko to the safeguarded public/made-for-kids queue. The post-release dry run attempted no upload, reported 21 eligible items, and selected Niko next.
- The 15:30 Australia/Sydney scheduled cycle then uploaded Niko successfully as public/made-for-kids video `nmj4W890T3I` (`https://youtu.be/nmj4W890T3I`) on immutable Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`. The upload report records success, the prepared thumbnail ledger records the reviewed thumbnail, and the source was archived after the video ID was recorded. Twenty eligible backlog items remained after that cycle. The next planned production lead remains Ant/Grasshopper with `natasha-au`.

## Daily 06:00 upload-summary email (2026-08-27)

- The user explicitly stopped per-upload emails and requested one email at 06:00 Australia/Sydney reporting how many videos uploaded during the previous day. `automation/Run-UploadCycle.ps1` no longer invokes any mailer; upload success, retry state and task exit status remain independent from email delivery.
- New `automation/Send-DailyUploadSummary.ps1` reads only successful rows with a video ID from ignored duplicate-safe ledger `automation/runtime/upload-ledger.jsonl`. It converts previous Sydney-calendar-day boundaries to UTC with Windows time zone `AUS Eastern Standard Time`, so daylight-saving changes remain correct. The email includes the count plus source names and YouTube links, and is sent even when the count is zero.
- The summary writes ignored report/result/log files and `runtime/daily-summary-state.json`. A confirmed date is recorded only after the exact subject appears in Outlook Sent Items; any later invocation for that same summary date exits successfully without another email. `-DryRun` never sends or changes the last-sent date.
- The no-send validation for Sydney date 2026-08-26 counted exactly four ledgered uploads over UTC interval `2026-08-25T14:00:00Z` through `2026-08-26T14:00:00Z` and produced subject `Tiny Tales daily upload summary - 2026-08-26 - 4 videos`.
- Live task `Tiny Tales - Daily Upload Summary Email` was installed Ready with exact action `automation/Send-DailyUploadSummary.ps1`; first run is 2026-08-28 06:00 Australia/Sydney. It uses Interactive Outlook access, `StartWhenAvailable`, `WakeToRun`, network requirement, battery allowance, `IgnoreNew`, and a 15-minute limit. `automation/Set-TinyTalesDailySummaryEmail.ps1` safely installs or updates it after verifying the normal upload action.

## Ant/Grasshopper Pika motion pilot (2026-08-27)

- A five-second Pika image-to-video pilot is prepared for the summer opening frame. The accepted 1672x941 source is `automation/production-assets/shared-harvest-summer-opening-v1.png` with SHA-256 `7231693579a51d2b0d5e51fe9d4d42819dde2f9568ddaa817ebdf9c33f175035`.
- Pilot 01 downloaded to `automation/production-work/ant-grasshopper-shared-harvest-01/pika-pilot-01/pika-pilot-01.mp4` with SHA-256 `ca31dc61b97fcbd361da75bd2d24d2433e54ab175ccb072ab7ef830f28bc7e53`. It is 5.033 seconds, 784x470, silent H.264 and decodes fully.
- Full-sequence and full-resolution contact-sheet review found all five identities, the seed, Grasshopper's bow motion, the meadow and the final pose stable. Ant did not perform the requested two-step walk; she mainly held position with body/head movement. A persistent visible Pika watermark is present. Pilot 01 is rejected as final footage.
- Pilot 02 downloaded as a fully decodable 5.033-second 784x470 silent H.264 video with SHA-256 `5056f204c74ef7680aea45810cfc407dfdd81ad930497c18efca09eb94444a53`. It used the same source and a compact 365-character prompt prioritizing only Ant's locomotion.
- Full-sequence review confirmed Ant's front foot lifts, arcs and plants, her body transfers weight and settles, and the seed remains solid. The other four identities, their props, the meadow and camera remain stable. Pika motion is approved for a single-hero-per-shot workflow.
- The free pilot remains watermarked and only 784x470, so it is rejected for publication. `metadata/ant-grasshopper-shared-harvest-01-plan.json` permits future Pika motion design but blocks final render/queue/upload until commercial usage rights and an unwatermarked suitable-resolution export path are confirmed.
- Live reconciliation before preparing the pilot found local and `origin/main` at zero divergence; the Ant planning files were the only pre-existing dirty changes. Generation count-only returned 14 complete, zero remaining and zero failed. Read-only OAuth verification returned Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`. The queue had 10 MP4s, the archive and ledger had 47 confirmed items, and the ten-minute uploader was Ready.
- Pika has no available Codex/plugin connector. Its site was opened in the user's browser, but account sign-in and the browser upload/generation remain a user interaction. After the result is downloaded, visually review it against every locked acceptance check before any wider generation.
- The Pika free output is a test asset, not automatically approved for commercial/public use. Confirm current usage rights before putting any Pika-generated pixels into a monetized Tiny Tales video.
- The user later explicitly refused payment and manual provider work. Do not create a paid Pika/API key, buy credits, start a subscription, or proceed through a payment prompt. Pika remains test evidence only.
- The active zero-cost method is built-in generated animation keyframes plus deterministic local rendering with pose progression, eased camera/follow/parallax motion, ambient movement and beat-synchronized cuts. This is not true generative video and must be described accurately.
- `automation/production-assets/shared-harvest-summer-opening-midstep-v1.png` is an accepted matched edit of the opening frame with Ant visibly advancing while the seed, five identities, Grasshopper/fiddle, anthill, composition and lighting remain consistent. It has no watermark; SHA-256 is `9ac7316be57afeece1d9a18b28839dad2cc6f345cc4e5a0d85297938ca6fa9b7`.
- `metadata/ant-grasshopper-zero-cost-keyframe-review.json` records the accepted opening pair and the motion language. Continue one prioritized action per shot and reject any identity, anatomy, prop or scene drift before local animation.

## Ant/Grasshopper final production checkpoint (2026-08-27)

- `The Ant and Grasshopper's Shared Harvest | Musical Story for Kids` is finished locally as `ant-grasshopper-shared-harvest-01` at 114.44 seconds. Producer: `automation/production/produce_ant_grasshopper_shared_harvest.py`; exact story plan: `metadata/ant-grasshopper-shared-harvest-01-plan.json`.
- Natasha (`natasha-au`) narrates, Ana (`ana-us`) voices Ant and Ryan (`ryan-uk`) voices Grasshopper. The opening introduces the orchestra and asks viewers to stay for the fantastic final song; the original carry/play/plan/share refrain returns in the spring finale.
- Ten premium 3D-style seasonal compositions and nine accepted second action poses create visible work, playing, catching, passing, serving, planning and celebrating. Pose changes use clean music-beat cuts because dissolves between recomposed keyframes created anatomy ghosting. The first-snow second pose was rejected for duplicating Ant and never enters the render.
- The final contains no Pika footage and uses no paid provider. It is accurately a zero-cost generated-keyframe and deterministic local-code animation, not true rigged or generative video. Original local music, easing, camera travel, seasonal overlays and three voices complete the motion system.
- The master passed 1080p H.264, 48 kHz stereo AAC, full decode, ten narration-contained story shots, no shot over 14 seconds, zero boundary gaps and final-card-only checks. `quality-contact-sheet.png`, `transition-contact-sheet.png`, `action-cut-contact-sheet.png`, the sync audit and the `WORK + MUSIC = MAGIC!` thumbnail were all visually reviewed.
- Manifest state is 15 complete, zero remaining and zero failed. The safeguarded queue sidecar contains all mandatory true quality/thumbnail flags. The post-release dry run attempted no upload, reported two queued videos and selected Ant/Grasshopper next; normal ten-minute public/made-for-kids scheduling remains responsible for upload.

## Ant/Grasshopper pre-upload audio correction (2026-08-27)

- The user reviewed the first local master before upload and found two valid defects: `clap-clap-clap` was spoken instead of performed, and the promised final song was not musically distinct. The defective pending pair was moved intact to ignored `automation/production-work/ant-grasshopper-shared-harvest-01/correction-hold/`; ledger/live-state checks found no upload.
- `produce_ant_grasshopper_shared_harvest.py` now synthesizes an original stereo handclap and wooden tap. Three separate `Play a little!` cues each trigger exactly three real claps; no voice says `clap-clap`. The final `Carry a little!` line triggers three wooden taps.
- The final spring scene is a separate 13.55-second chorus: Ana and Ryan alternate the first two lines, Natasha completes the last two, and a stronger original lead melody, harmony and four-beat pulse distinguishes it from the underscore. The corrected master is 114.75 seconds.
- Full decode, zero gaps, narration/effect containment, maximum 14-second shots, final-card-only, visual contact sheets, action-cut sheet, final-song waveform and final-song spectrum passed review. The quality report explicitly records three clap cues, no spoken clap words and a distinct finale.
- Only the corrected reviewed output was returned to `pending-uploads`; the post-correction uploader dry run sent nothing, reported no failures and selected Ant/Grasshopper next under the normal public/made-for-kids safeguards.

## Ant/Grasshopper expressive narration revision (2026-08-27)

- The user made a second pre-upload correction request: remove the `Stay for the final song` instruction, replace spoken `tap-tap-tap` with musical sound, and make flat narration respond to the images. The queued audio-v2 pair is preserved in ignored correction hold and was removed from scheduler reach before work began; ledger checks showed no upload.
- The 123.49-second revision opens with only `Meet our orchestra!`. Both `Carry a little!` lines trigger three wooden musical taps; all `tap-tap` speech is gone. Three `Play a little!` lines still trigger three real claps each with no spoken clap syllables.
- Summer narration uses `natasha-bright`, autumn/rescue uses `natasha-excited`, and snow/welcome uses `natasha-cozy`. Rewritten lines explicitly match the berry roll, daisy hop, basket pass, autumn gust, seed rescue, snowy knock, soup welcome and seed-plan imagery, with sound words, questions and character reactions.
- The revised master passed full decode, 1080p/stereo AAC, zero gaps, all speech/effects contained by matching visuals, maximum 14-second shots, no forbidden narration, two three-tap cues, three three-clap cues, three expressive delivery profiles, audience questions, action sound words and the distinct final chorus. Visual and audio evidence sheets were re-reviewed.

## Ant/Grasshopper character-led musical story revision (2026-08-27)

- A third pre-upload review found remaining spoken sound imitations and a flat host-style start. The prior audio-v2 pair remains intact in ignored correction hold; it was never uploaded and must not be restored.
- The replacement is a 128.30-second first-person musical story. Ant opens directly over the image of her carrying a seed, Ant and Grasshopper alternate scene-matched storytelling, and the spoken narrative ends before the distinct spring chorus. There is no generic host introduction, final-song retention instruction or spoken onomatopoeia.
- Original effects perform what the images show: three claps in the daisy scene, autumn wind during the gust, seed rattle during the final pour, three knocks at the winter door, and wooden beats/real claps in the finale. `narration-visual-sync-audit.json` contains the exact start/end window for every voice and effect.
- The reviewed 1920x1080 H.264/48 kHz stereo AAC master has SHA-256 `4b5293d6e3500c37511353a3338928fa0456fb0f3476595297f14b2e409609da`. Full decode, zero gaps, ten narration/effect-contained scenes, the 14-second shot ceiling, forbidden-speech checks and distinct-finale checks all passed; general, transition, action-cut, waveform and spectrum evidence were visually reviewed.
- Only this story-audio-v3 master may return to the public/made-for-kids safeguarded queue. Confirm the copied MP4 hash and the updated sidecar, then perform a dry run that sends no upload. Preserve all held predecessors for audit.
- Queue release is complete: the pending copy matches the production SHA-256. The post-stability dry run attempted zero uploads, found no failures, and selected Ant/Grasshopper next; the normal scheduler remains responsible for any real upload.

## New varied video batch checkpoint (2026-08-27)

- The user requested several more videos. The locked batch plan is `metadata/new-video-batch-plan-2026-08-27-b.json`: Lina/feelings (`natasha-au`), Five Little Ducks (`maisie-uk`), and Rory/planets (`ryan-uk`). These formats, voices and visual systems are intentionally distinct.
- `Lina's Feelings Weather Studio | Emotional Story for Kids` is complete at 82.00 seconds. Producer: `automation/production/produce_lina_feelings_weather.py`; exact scene/audio plan: `metadata/linas-feelings-weather-studio-01-plan.json`; asset review: `metadata/linas-feelings-weather-studio-01-asset-review.json`. Six premium weather-studio scenes map every line and original sound effect to the visible wheel, ribbon, breath, blanket, flashlight step or rainbow action.
- Lina passed its full 1080p H.264/48 kHz stereo AAC decode, zero-gap timeline, six-scene uniqueness, effect/narration containment, 14-second ceiling, final-card-only and forbidden-spoken-sound gates. Reviewed SHA-256: `b2204144141feaf2ca36edb3ab0792a594890797cc6c4bb95e065cbfdbaaa062`. Contact sheets and the `WHAT'S YOUR WEATHER?` thumbnail passed visual review; the guarded runner released it to the normal queue without uploading.
- `Five Little Ducks' River Countdown | Nursery Song for Kids` is complete at 81.90 seconds. Producer: `automation/production/produce_five_ducks_river_countdown.py`; exact plan: `metadata/five-little-ducks-river-countdown-01-plan.json`; asset review: `metadata/five-little-ducks-river-countdown-01-asset-review.json`. Seven handcrafted felt-and-wood tableaux show exact counts `5,4,3,2,1,0,5` with active paddling/search action.
- Duck calls are original synthesized effects rather than spoken `quack` words. The new Tiny Tales musical treatment also contains original paddle, waterfall, lantern and walking effects. Full decode, 1080p/stereo AAC, zero gaps, exact-count, uniqueness, containment, 14-second, final-card and no-spoken-quack gates passed. Reviewed SHA-256: `dcfcd303da15db73841ad27c0dbd52963176afd1f53c77b51651fc03135c0b2b`. Contact sheets and `CAN YOU COUNT THEM?` thumbnail passed; the guarded runner queued it without uploading.
- Both queue copies match their production SHA-256 exactly. A post-stability dry run sent no upload, reported no failures, found four eligible queue items, and selected Five Ducks next under the normal public/made-for-kids safeguards.
- Rory's Eight-Planet Postcard Adventure is active, not complete or queued. `automation/production-assets/rory-planets-opening-v1.png` is the accepted identity/style anchor: a premium 3D pop-up-paper backyard observatory, consistent Rory, and a cream/cobalt/orange postcard rocket. Continue by generating distinct accurate Mercury-through-Neptune postcard dioramas, then lock the exact line-to-image plan before narration. Lead must remain `ryan-uk` to preserve rotation.
- `COVERED-TOPICS.md` was rebuilt after the completed metadata and now records 60 concepts. The curated manifest has 17 completed, zero remaining and zero failed; Rory must not enter the manifest until its producer, reviewed assets and output are ready.

## Rory completion and next varied set (2026-08-28)

- `Rory's Eight-Planet Postcard Adventure | Space Story for Kids` is complete as `rorys-eight-planet-postcard-adventure-01` at 126.7 seconds. Producer: `automation/production/produce_rory_planet_postcards.py`; locked plan: `metadata/rorys-eight-planet-postcard-adventure-01-plan.json`; asset review: `metadata/rorys-eight-planet-postcard-adventure-01-asset-review.json`.
- Ryan (`ryan-uk`) leads with distinct curious, warm, wonder, awe and excited delivery profiles; Ana (`ana-us`) voices Rory. Ten premium 3D-style scenes show launch plus all eight planets in correct order and a home map. Original local effects perform launch, cloud, dust, storm, ring, wind and postcard stamps; no sound word is narrated.
- The first Uranus generation was rejected because its bright broad rings looked like Saturn. The accepted Uranus frame uses faint narrow rings and a strong sideways tilt. The final map is deterministic rather than generated: exactly eight reviewed postcard images appear left-to-right as Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus and Neptune.
- The master SHA-256 is `1bbf4ef2584bb15e6faac68363459e29133a439da8feaf9ca880a9f06825a207`. Full 1080p H.264/48 kHz stereo AAC decode, zero gaps, ten unique scenes, correct planet order, narration/effect containment, 14-second ceiling, final-card-only and no-spoken-sound gates passed. General, every-boundary, full-resolution final-map and truthful `8 PLANETS, 1 ADVENTURE!` thumbnail reviews passed.
- The normal runner preserved the reviewed output, marked the curated manifest 18 complete / zero remaining / zero failed, and released Rory to the safeguarded queue without a manual upload.
- Continued production is locked in `metadata/new-video-batch-plan-2026-08-28-c.json`. The lead sequence remains Eddie Excavator `ana-us`, Dad's Coming-Home Welcome Rhythm `natasha-au`, then Pick/Wash/Pack Fruit Picnic `maisie-uk`. Eddie now has an 84-second / 100 BPM musical-story plan with seven five-bar scenes and original emotion-mapped lyrics. All seven 1672x941 premium scenes—plan, scoop, carry, level, stopped-machine planting, water test and finale—are visually reviewed in `metadata/eddie-excavators-rain-garden-day-01-asset-review.json`. The first leveling variant was rejected for too many stones; the accepted frame has exactly three. Producer, synchronized musical voices/effects, final render and quality evidence remain unfinished. Nothing is queued or uploaded.

## Recent low-view thumbnail refresh (2026-08-28)

- The user asked to inspect the latest uploaded videos and replace thumbnails when current views were below 20. A live YouTube Data API query of the 12 most recent Tiny Tales uploads found five strictly below the threshold; seven with 28 to 113 views were intentionally unchanged.
- Replacements uploaded successfully for `tDj0S6Q29GU` / 18 views / `CAN YOU GUESS?`, `TWjnF0jcfYk` / 10 / `FIX THEIR COLOURS!`, `CghTDo-6Sm4` / 9 / `BIRD COLOUR RESCUE!`, `d4TBF0P6DXs` / 9 / `OCEAN ACTION!`, and `Hgr9t3mGQsw` / 13 / `HOP, REACH, STRETCH!`.
- New artwork was based on each archived video's real species, lesson and action. Notably, Friendly Animal Movement now truthfully shows rabbit hopping, monkey reaching, giraffe stretching and squirrel balancing instead of unrelated animals. Exact hooks were rendered locally rather than generated as text.
- Immediately before upload, all five remained below 20 views and matched immutable Tiny Tales channel `UCEn9N-ITQHshjgt6fy7fxnw`, exact title, public status and made-for-kids status. YouTube confirmed all five thumbnail sets. Served max-resolution copies were fetched at 1280x720, visually reviewed and matched local JPEGs with RMS 2.925 to 4.618.
- The complete audit is `metadata/low-view-thumbnail-refresh-2026-08-28.json`; the five final JPEGs and manifest entries are tracked. Do not treat this one-time instruction as authority for an unattended recurring thumbnail-change task.

## Rory opening correction and current fifteen-minute queue (2026-08-28)

- The original reviewed Rory audio files were complete, but the edit had a 3.8-second silent title over the same opening composition, delayed narration until 4.08 seconds, held that composition for 17.4 seconds, and overlapped the launch effect with the first spoken phrase. The user correctly perceived this as an unclear or apparently incomplete opening. The exact original queue MP4/sidecar were moved to ignored `automation/production-work/rorys-eight-planet-postcard-adventure-01/correction-hold/opening-v1/` before upload; no defective YouTube copy exists.
- `automation/production/produce_rory_planet_postcards.py` and `metadata/rorys-eight-planet-postcard-adventure-01-plan.json` now start the visual story at zero, start Ryan at 0.32 seconds beneath a short title overlay, clear the title at 2.35 seconds, delay the launch response to 2.45 seconds, and cut to Mercury at 13.958 seconds. The new story explicitly describes the postcard insertion, rocket light and map; Rory says, `Eight planets, eight postcards—let's visit them in order!`
- The corrected master is 123.3 seconds with SHA-256 `a8d268876155760e6c635f94dbbc845d302097cf1a96e27ab28ac0fac7f0c37c`. It passed full decode, H.264 1080p, 48 kHz stereo AAC, zero gaps, all narration/effect containment, correct planet order, ten-scene uniqueness, every story scene below 14 seconds, final-card-only and no-spoken-sound-word checks. The general sheet, every-boundary sheet, opening 0-15-second sheet, opening waveform and existing thumbnail were visually reviewed. Full correction evidence is `metadata/rorys-eight-planet-postcard-adventure-01-opening-correction-review.json`.
- The corrected queue copy matches the reviewed production hash. Read-only OAuth verification returned Tiny Tales and immutable channel `UCEn9N-ITQHshjgt6fy7fxnw`. The immediate no-upload dry run reported four age-eligible files and selected Five Ducks; corrected Rory was only waiting for the mandatory five-minute stability age.
- At the user's explicit request, `Tiny Tales - Daily Private Upload` is Ready on a repeating `PT15M` trigger beginning 10:15 Australia/Sydney on 2026-08-28. It uploads no more than one eligible video per run with all existing public/made-for-kids, channel-lock, confirmation, duplicate, ambiguity, quality, thumbnail and quota safeguards. `Tiny Tales - Hourly Upload Retry` remains Disabled to prevent competing schedules. At installation, the pending set was corrected Rory, Five Ducks, Lina, Ant/Grasshopper and Jungle Animal Clue Detectives.
- The 10:15 run attempted zero uploads and sent no video data because Rory's regenerated quality report lacked the uploader-required alias fields `continuous_visual_timeline` and `end_card_is_final_event_only`. The producer now records those aliases from the same zero-gap/final-card checks; local uploader validation then passed both Rory's quality evidence and reviewed thumbnail before the 10:30 slot. Preserve this schema contract in future producer revisions.
- The 10:30 slot successfully uploaded corrected Rory publicly/made-for-kids as `25sHX9AceLo` (`https://youtu.be/25sHX9AceLo`), applied its reviewed thumbnail, recorded/archived exact hash `a8d268876155760e6c635f94dbbc845d302097cf1a96e27ab28ac0fac7f0c37c`, and removed only the identical production-output copy after success.
- Preflight of the remaining queue found the same missing aliases in Five Ducks, Lina and Ant/Grasshopper despite their underlying zero-gap/final-card checks already passing. All three producers now emit the canonical fields; their evidence was refreshed from unchanged masters. The uploader's local quality and prepared-thumbnail validators subsequently passed Five Ducks, Lina, Ant/Grasshopper and legacy Jungle Animal Clue Detectives without performing an upload.
- Subsequent scheduled uploads succeeded at fifteen-minute boundaries: Five Ducks at 10:45 as `RjHEcm4aWUs` (`https://youtu.be/RjHEcm4aWUs`), Lina at 11:00 as `IljnXnB_5X0` (`https://youtu.be/IljnXnB_5X0`), and Ant/Grasshopper at 11:15 as `9vvghOKhipo` (`https://youtu.be/9vvghOKhipo`). All were public/made-for-kids on verified Tiny Tales, received reviewed thumbnails, matched their documented reviewed hashes, and archived after ledgered success.
- Jungle's 11:30 run performed no upload because SHA-256 `a2d8dd594c729c329bafc6537096faa645553e09f7bd1641e88439c893502253` retained an unresolved `started` attempt from 2026-08-23. The required read-only full uploads-playlist query verified Tiny Tales and returned zero exact-title matches. Only that exact attempt was then recorded `failed_confirmed_absent`; the regular 11:45 slot uploaded Jungle publicly/made-for-kids as `4ZVRvlEP5uU` (`https://youtu.be/4ZVRvlEP5uU`), set the reviewed thumbnail and archived the source.
- Final channel verification returned Tiny Tales `UCEn9N-ITQHshjgt6fy7fxnw`. The final dry run attempted zero uploads, had no failures, reported `remaining_upload_count: 0` and `next_video: null`. `Tiny Tales - Daily Private Upload` is Ready on `PT15M`, last ran 11:45 with result `0`, and next checks at 12:00; `Tiny Tales - Hourly Upload Retry` remains Disabled. The regular task may safely no-op on the empty queue and will handle future reviewed queue items at the same cadence.

## Eddie Excavator musical story completed locally (2026-08-28)

- `Eddie Excavator's Rain-Garden Day` is complete as `eddie-excavators-rain-garden-day-01`: 84 seconds of story plus a four-second garden resolve, 88.00 seconds total. Producer: `automation/production/produce_eddie_rain_garden_musical.py`; plan: `metadata/eddie-excavators-rain-garden-day-01-plan.json`; output metadata: `metadata/eddie-excavators-rain-garden-day-01.json`.
- Seven reviewed premium compositions remain visible for exactly 12 seconds each. Ana and Ryan alternate across ten emotion-specific melodic/rhythmic profiles on a 100 BPM grid. The original score moves from curiosity through focused construction, tender planting, suspenseful testing, relief and full celebration. Rain, diesel, hydraulics, soil, stone, gate, planting, water and bird actions use synchronized effects rather than spoken sound words.
- Full decode, 1920x1080 H.264, 48 kHz stereo AAC, zero gaps, seven unique story scenes, lyric/effect containment, eighth-grid line starts, voice variation, final-card and prepared-thumbnail checks passed. Manual visual review corrected a compositor bug that made translucent accents opaque, then rechecked the planting scene at 48.5, 54 and 59.5 seconds and restored the completed garden behind the final refrain.
- After the user reported rushed delivery, Eddie was rebuilt with 21 short slow-v2 phrases. It now averages 108.5 WPM, peaks at 126.1 WPM and leaves at least 0.561 seconds between phrases. Final SHA-256 is `4f5567f6d7029ef41df4403e1c4e264b7cd917f25b042c9b0c7c900b9705bcc3`; audio measures -15.9 LUFS and -0.8 dB true peak. Nothing is queued or uploaded.

## Dad welcome rhythm completed locally (2026-08-28)

- `dads-coming-home-welcome-rhythm-01` is complete at 91.50 seconds: seven exact five-bar / 12.5-second scenes plus a four-second resolve at 96 BPM. Its distinct system is a premium stop-motion-inspired layered paper-and-fabric apartment, progressing from golden afternoon through peach suspense to blue evening rather than repeating Eddie's outdoor construction miniatures. Producer: `automation/production/produce_dads_welcome_rhythm.py`; metadata: `metadata/dads-coming-home-welcome-rhythm-01.json`.
- Mina is a five-year-old South Asian-Australian child with a dark wavy bob, mustard star clip, teal dungarees, coral shirt and striped socks. Dad Arun has short dark curls, a neat beard, navy rain jacket, rust jumper and canvas bag. Preserve their exact identity and the apartment landmarks from `automation/production-assets/dads-coming-home-*-v1.png`.
- The seven actions are picture-clock anticipation, slipper/drawing preparation, exactly three picture-card greeting choices, closed-door key suspense, a Mina-initiated mirrored wave with no touching, a one-drum/two-cushion three-beat rhythm, and the drawing-display/viewer-wave finale. The full continuity audit and hashes are in `metadata/dads-coming-home-welcome-rhythm-01-asset-review.json`; the exact music/emotion plan is `metadata/dads-coming-home-welcome-rhythm-01-plan.json`.
- Natasha leads, Maisie is Mina and Ryan is Dad across emotion-specific delivery profiles. The slow-v2 version uses 21 short lines on the local eighth-note grid; every scene cut still lands on beat one after five bars. Twenty-three real clock, pencil, paper, slipper, card, key, footstep, door, bag, fabric, drum and cushion effects remain inside the visible supporting scene and no imitation sound is spoken.
- Full decode, H.264 1920x1080, 48 kHz stereo AAC, zero gaps, scene uniqueness, lyric/effect containment, voice variation, exact phrase cuts and uploader-contract aliases passed. Manual review covered the general and transition sheets, opening, choice, suspense, mirrored wave, rhythm, finale, end card, thumbnail, waveform and spectrum. A large translucent door glow was rejected and removed before the final render.
- Dad Welcome now averages 111.1 WPM, peaks at 140.1 WPM and leaves at least 0.631 seconds between phrases. Final SHA-256 is `eb65a90c369e11df00a4976f409f668087338fa5a7c39769fd5e8d6b304d6e14`; audio measures -15.4 LUFS and -0.5 dB true peak. Nothing is queued or uploaded.

## Fruit Picnic completed locally (2026-08-28)

- `pick-wash-pack-fruit-picnic-01` is complete at 97.40 seconds: seven exact five-bar / 13.333-second orchard scenes plus a four-second resolve at 90 BPM. Its distinct system is luminous layered watercolour-and-gouache storybook art with restrained crop travel and leaf/light accents. Rebuild it with `automation/production/produce_fruit_picnic.py`.
- All seven exact assets and hashes are recorded in `metadata/pick-wash-pack-fruit-picnic-01-asset-review.json`. The visible arc is permission, one supported-branch pick, an exact two-apple/two-pear/two-plum count, washing the same six, red-gold-purple repeated twice, shared level-basket carrying and the six-fruit picnic with a leaf-only compost action. Extra-fruit count and wash variants were rejected and not retained.
- Maisie leads, Ryan performs Kai and Ana performs Rosa across 12 emotional delivery profiles. The corrected 21 lyric lines start on the 90 BPM eighth grid and stay inside their matching scene. More than 28 real leaf, gate, fruit, basket, water, cloth, latch, step and compost cues replace spoken sound words.
- Full decode, 1080p H.264, 48 kHz stereo AAC, zero gaps, exact musical cuts, voice rotation, lyric/effect containment and contact-sheet review passed. Fruit Picnic now averages 110.2 WPM, peaks at 131.5 WPM and leaves at least 0.751 seconds between phrases. Final SHA-256 is `7c6914fdfff973f60bbd1c4e170604478315dd26ee9baa21eaa180575420042d`; audio is -16.1 LUFS and -0.7 dB true peak. Thumbnail hook: `PICK, WASH, PACK!` Nothing is queued or uploaded.
- `COVERED-TOPICS.md` was rebuilt and now records 65 concepts. Choose the next story only after comparing its format, interaction, art system, presenter and setting progression against the latest five completed entries.

## Lumi Shadow Theatre active production (2026-08-28)

- The next deliberately different story is `lumi-shadow-theatre-surprise-01`, an original 84-second / 84 BPM backlit paper-theatre musical. Seven four-bar scenes stay at 11.428571 seconds each, followed by a four-second resolve. Ryan leads; Natasha performs Lumi and Ana performs Ms Noor.
- Its visual world is handcrafted indigo velvet, amber silk, layered cut paper and a protected brass theatre lamp. The exact plan is `metadata/lumi-shadow-theatre-surprise-01-plan.json`; the accepted-asset ledger is `metadata/lumi-shadow-theatre-surprise-01-asset-review.json`.
- Scene 1 establishes Lumi, Ms Noor, one rabbit puppet, three marked distances, an unlit/safely protected lamp, screen and the one-circle/two-triangle shape rack. Scene 2 preserves the identities and shows the lit supervised experiment with one small crisp rabbit shadow near the screen. Continue with near-lamp large shadow, then owl shapes, safe reveal, three-size rehearsal and finale. Nothing is queued or uploaded.

## Narration pacing correction (2026-08-29)

- The newest unreleased musical masters were objectively too compressed despite passing older sync gates: Eddie averaged 183.3 WPM, Dad Welcome 149.6 WPM and Fruit Picnic 175.5 WPM. The cause was four phrases forced into 12-13 second scenes, positive TTS speed boosts and 2.4-3.0 second maximum line windows.
- All three producers now use three short phrases per scene, negative/natural TTS rates, isolated `slow-v2` caches, a 140 WPM target, a hard 145 WPM per-line ceiling and at least 0.4 seconds between phrases. `narration-pacing-audit.json` is required quality evidence and the build fails if pacing is too fast.
- Corrected results: Eddie 108.5 weighted / 126.1 maximum WPM / 0.561-second minimum gap; Dad 111.1 / 140.1 / 0.631; Fruit 110.2 / 131.5 / 0.751. All outputs still pass full decode, 1080p/stereo AAC, zero gaps, scene containment and visual contact-sheet review. None is queued or uploaded.
- The recently uploaded Rory, Five Ducks, Lina and Ant/Grasshopper videos measured 127.2, 138.8, 136.1 and 132.3 weighted WPM. No live YouTube video was deleted or replaced during this correction. Lumi's plan is now three short lines per 11.428571-second scene and must obey the same pacing gate before rendering.

## Safe continuation checklist

1. Read this file and `AGENTS.md`.
2. Inspect `git status`, manifest, generation state, pending queue, archive, ledger, and recent logs without exposing secret contents.
3. Query all three exact Scheduled Tasks and their next/last run information.
4. Run the generation count-only command before generating anything.
5. Verify the OAuth channel with the uploader's read-only verify command before any upload work.
6. Report live state and discrepancies to the user.
7. Continue only unfinished work. Do not regenerate or re-upload completed ledger entries.
8. Visually inspect each new quality contact sheet before manually approving an immediate upload; scheduled uploads still enforce technical checks, channel lock, stability age, duplicate ledger, configured visibility, and made-for-kids.
9. Update this handoff after material architecture, schedule, channel, recipient, safety, or editorial changes.

Useful read-only commands from the project folder:

```powershell
C:\Animation\Animation\.venv\Scripts\python.exe -B automation\generation_runner.py --count-only
C:\Animation\Animation\.venv\Scripts\python.exe -B automation\uploader.py verify
C:\Animation\Animation\.venv\Scripts\python.exe -B automation\uploader.py dry-run --report-json automation\runtime\handoff-dry-run.json
Get-ScheduledTask -TaskName 'Tiny Tales - Continuous Generation','Tiny Tales - Daily Private Upload','Tiny Tales - Hourly Upload Retry'
```

## Separate new-channel request

The user wants to create another channel/project in a separate folder, but has not yet supplied the new folder/channel name, channel ID, or concept. Do not reuse any Tiny Tales OAuth token, channel lock, ledger, archive, runtime state, or Scheduled Tasks. Create a clean isolated project only after obtaining the new identity details.

## Blender pilot ready for episode development (2026-08-28)

- The first six-second Blender render of `Milo's Melody Garden`, project ID `milos-melody-garden-blender-pilot-01`, was technically valid but the user rejected its visual direction as much too basic. Do not treat that MP4 or its prior hash as an approved Tiny Tales quality reference.
- Milo performs three musical strikes at frames 48, 72 and 96. Blue, gold and pink mushroom caps squash on contact and their matching flowers bloom after the hits. The source was corrected so the third pink payoff remains visible beside Milo's tail and the nearest hand performs that strike.
- V2 is now planned as eight seconds / 192 frames with hits at frames 72, 104 and 136. It replaces the flat disc, empty sky, primitive trees, undressed character and simple drums with a physical night cyclorama, distant hills/stars, multi-level terrain, pond/path, foreground foliage, illuminated vine arch, performance rug, costumed and more expressive Milo, crafted brass/wood drums, visible blooms, music-note reactions and colored hit lights.
- Reproducible source is `automation/blender/milos_melody_garden_pilot.py`. It creates named Milo controls, three modular drums, three modular flowers, a camera target, materials, lights, animation, synchronized WAV, PNG sequence and reusable `.blend` file from scratch.
- At the user's request, only V2 hero frame 144 was rendered at `automation/production-work/milos-melody-garden-blender-pilot-01/frames/frame_0144.png`; the full V2 animation has not been rendered. Await explicit visual-direction feedback on that frame before spending time on the complete sequence. Nothing is queued or uploaded.
- Continue it as a full six-zone Tiny Tales music story: introduce Milo and the sleeping garden, teach colour and pitch, let viewers copy a short rhythm, add a turn-taking friend, then resolve with an original garden song using the stable final pose as the transition point.

## Active temporary musical-narration preference (2026-08-28)

- For the next several days, the user wants new Tiny Tales stories delivered musically rather than as simple read-aloud narration. Use an original story-song, melodic character performance or expressive rhythmic chant as the primary voice treatment; do not default to a flat narrator over generic background music.
- Lyrics, melody, arrangement and visuals must be planned as one timeline. Each lyric/effect belongs inside the exact shot that visibly supports it. Record BPM, beat-one offset, phrase boundaries, lyric windows, emotion and important visual-hit frames before rendering the final edit.
- Vary emotion with the situation: bright and buoyant for happiness, softer/slower/lower for sadness or tenderness, tighter rhythm and harmony for suspense, widening harmony for discovery or relief, and the fullest arrangement for the climax/final song. Avoid constant tempo, constant intensity and repeated identical vocal delivery.
- Preserve voice rotation between videos and distinct character voices within a video. Short spoken bridges are acceptable only when expressively acted and necessary for clarity; effects such as claps, taps, knocks, splashes, wind and animal calls remain real synchronized sounds, never spoken imitation words.
- Require a lyric-to-visual-and-emotion audit plus final playback review proving intelligible words, exact scene containment, emotional variation, phrase-aligned edits and a distinct musical climax. Reconfirm this temporary direction with the user on or after 2026-09-01 before changing it.
