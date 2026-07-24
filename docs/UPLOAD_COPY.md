# Upload-ready media and copy

## Recommended YouTube upload

**Video:** `artifacts/tempodance-demo-voiced.mp4`  
**Thumbnail:** `artifacts/youtube-thumbnail.png`

### Title

TempoDance AI — The Dance Coach That Learns How You Learn | 30-Second Demo

### Alternate title

I Built an AI Dance Coach That Gives One Fix at a Time

### Description

TempoDance AI is a local-first dance coach that turns a tutorial into a source-synchronized pose reference, compares it with the learner's movement, and gives one correction at a time.

This demo shows:

- a native-rate 30 FPS COCO-17 coach overlay;
- source audio with detected 114 BPM counts;
- upper-body, lower-body, and combined practice steps;
- local pose comparison and per-limb feedback;
- session memory that evaluates whether a coaching cue worked before adapting.

The default demo runs without a camera or cloud API. In camera mode, frames are processed by the local FastAPI pose service and are not persisted by application code.

Live demo: https://tempodance-ai.vercel.app<br>
Code: https://github.com/CarlKho-Minerva/tempodance-ai<br>
Reference tutorial: https://www.youtube.com/shorts/jrUsvBKemBU

#AI #DanceTech #BuildInPublic

### Suggested YouTube settings

- Category: Science & Technology
- Visibility: Public, or Unlisted if the submission form requires it
- Audience: Not made for kids
- Language: English
- Thumbnail: `artifacts/youtube-thumbnail.png`
- Add the repository link in the first three lines
- If the source music triggers Content ID, upload `artifacts/tempodance-demo-voiced-clean.mp4` instead

## X / Twitter post

Built TempoDance AI: a local-first dance coach that turns a tutorial into a 30 FPS, beat-synced pose coach. It teaches upper body → lower body → full move, then adapts one cue at a time.

🎥 [YOUTUBE URL]<br>
🌐 https://tempodance-ai.vercel.app<br>
💻 https://github.com/CarlKho-Minerva/tempodance-ai

#BuildInPublic #AI #DanceTech

### Optional four-post thread

1. Dance tutorials can show a move, but they cannot see why you keep missing it. I built TempoDance AI to close that loop.
2. It overlays a 30 FPS pose track on the source, keeps counts tied to the audio beat, and teaches upper body → lower body → full move to avoid cognitive overload.
3. A local pose scorer identifies the weakest limb. Session memory then checks whether the cue actually improved that target before the policy changes.
4. Next step: I am testing it with my own dancing. Demo: [YOUTUBE URL] · Try it: https://tempodance-ai.vercel.app · Code: https://github.com/CarlKho-Minerva/tempodance-ai

## Submission media

- `assets/cover.png` — 1600×900 project cover
- `artifacts/youtube-thumbnail.png` — 1280×720 upload thumbnail
- `artifacts/tempodance-demo-voiced.mp4` — 29-second male-voiced demo with quiet source audio
- `artifacts/tempodance-demo-voiced-clean.mp4` — voice-only audio alternative
- `artifacts/tempodance-demo-raw.mp4` — silent editable master
- `artifacts/demo-ui-v2.png` — full workspace screenshot
- `artifacts/agent-memory-v2.png` — agent-memory close-up
- `artifacts/social-card-v2.png` — 1080×1350 social card
- `artifacts/demo-script.txt` — narration source

## Final actions before submitting

1. Add a five-second selfie or dancing intro if the form values founder presence; keep the product demo unchanged after it.
2. Credit the reference tutorial and use the clean-audio cut if a platform flags the music.
3. Test the repository from a fresh clone and confirm `./run.sh` opens the demo.
4. Put the video and repository links near the top of every submission description.
5. Upload the cover, full workspace screenshot, and agent-memory close-up—not three visually similar screenshots.
6. Save the submission confirmation page and pin the X post until judging ends.
