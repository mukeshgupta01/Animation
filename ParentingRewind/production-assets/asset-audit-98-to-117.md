# Asset and topic audit: episodes 98-117

Requested 25 September 2026: twenty additional adult-facing Parenting Rewind videos and scheduled upload. Reviewed the complete topic registry, historical metadata, asset library and the live hourly uploader before production. The previous queue was empty after 98 ordinary uploads. Preserve all other projects.

## Decisions

- Seven preschool, seven school-age and six teenage lessons. Each has its own script, title, description, research record and caption track. Sources and review date are in `research-98-to-117.json`; complete specifications are in `scripts/produce_redesigned_bundle_98_to_117.py`.
- Five new built-in image-generation calls, one per storyboard below. Fifteen episodes reuse approved assets. The reused casts/settings are separated by different families and topics; no complete previous asset/order combination is reused. The first proposed sequence for 101 matched episode 90 and was changed before rendering.
- Topic distinctions include warming up rather than compulsory greetings; practical repair rather than extracting a confession; feelings vocabulary rather than reading tests; co-viewing rather than stopping media; keeping children out of adult messages rather than explaining separation; bystander support rather than responding to the child being targeted.
- Initial proposed reuse for co-viewing and playdate preparation was rejected during source-image review: the library did not show joint viewing or putting precious toys away. New storyboards were generated for 104 and 110.
- Sources support general educational suggestions, not guarantees, diagnoses or personalised treatment. Sample dialogue is original. The body-comment episode uses only communication guidance from the clinical-context source; it does not offer eating-disorder treatment. Cyberbullying evidence guidance excludes copying or sharing sexual images of minors.
- Source panels are preserved in full over softly blurred portrait backgrounds. New sheets for 103 and 110 have measured off-centre horizontal gutters; their crops are explicit in the producer. Review encoded contact sheets, not just the source image.
- No automatic mirror in this finite producer. Review first, then verified copy to the existing Business OneDrive queue. New assets start at zero published uses; local rendering is not publication.

## New storyboard prompt records

All five calls requested original photorealistic natural editorial photography for **adult parenting education**, six equal cells in a strict three-column/two-row 1536x1024 landscape sheet, narrow white gutters, consistent fictional cast/clothing within the episode, varied medium/wide framing, complete faces and meaningful hands, natural anatomy, no readable text, logos, brands or watermarks. No reference images were supplied.

### 100: teen privacy

`teen-privacy-father-son-storyboard-01.png`: father in his mid-40s with fair skin, short brown hair and navy knit shirt; 16-year-old son with curly brown hair, green shirt and full-length jeans. Contemporary apartment hallway, teen study bedroom and kitchen, warm daylight. Six requested beats: father about to push open closed bedroom door; teen turns uncomfortably toward interruption; father pauses outside; father knocks; teen voluntarily opens while father waits; respectful privacy discussion at kitchen table. Keep teenager age-appropriate, with no infantilisation or dramatic distress.

### 103: teen purchase

`teen-money-mother-daughter-storyboard-01.png`: mother in early 40s with medium-brown skin, loosely tied dark wavy hair and plum blouse; 15-year-old daughter with chin-length dark bob and denim shirt. Mint-accented bright apartment dining area. Beats: daughter shows unbranded headphones on tablet; mother's dismissive lecture deflates her; mother pauses; both compare costs using notebook/calculator/coins; daughter puts tablet face-down and waits; mother listens to daughter's simple savings plan. Natural supported decision-making, no financial recommendations or readable figures.

### 104: co-viewing

`preschool-coview-father-son-storyboard-01.png`: East Asian-appearance father in teal shirt, preschool son aged four in rust sweater and jeans; cream sofa and green rug. Beats: child watches tablet and father notices; father sets his phone aside; both watch together; child discusses screen showing simple geometric blocks; device switched off while they build real blocks; wider view of shared offscreen play. No branded media, distress or unsafe activity.

### 110: playdate preparation

`preschool-playdate-mother-son-storyboard-01.png`: mother with light-olive skin, dark bob and cream cardigan; four-year-old son in red shirt and blue overalls; preschool friend with curly fair hair and green sweater. Honey timber shelves and blue rug. Beats: boy holds precious bear by red truck; mother listens at child level; they put precious toys on shelf; set out ordinary cars and blocks; friends play side by side with mother nearby; build a road together while protected toys remain on shelf. Show preparation rather than forced surrender of a toy.

### 115: teen chore ownership

`teen-chores-father-daughter-storyboard-01.png`: dark-skinned father with close-cropped hair, beard and burgundy henley; 16-year-old daughter with natural curls in high puff, mustard shirt and jeans. Olive-green/pale-wood kitchen and laundry. Beats: tired reminder by laundry basket; mutual frustration beside towels; father pauses; shared discussion of blank weekly chart; daughter folds independently while father does his own task; father thanks her contribution. Respectful teenage responsibility, no childish reward performance.

## Validation and continuation

Production: `.venv-production/Scripts/python.exe scripts/produce_redesigned_bundle_98_to_117.py --start 98 --count 5` (then 103, 108 and 113). Shared helper imports media functions only from the historical module; the rejected batch entry point is never run.

Encoded validation: `scripts/review_bundle_98_to_117.py`. It checks full decode, captioned/spoken CTA, hashes and mixed audio levels, and exports seven-frame sheets. Independent offline speech recognition uses the existing local Whisper installation through `scripts/review_bundle_audio_98_to_117.py`; no model download or external speech recognition is needed. Record visual review only after inspecting the encoded frames. Exact changing completion and transfer state belongs in `PROJECT-HANDOFF.md`.
