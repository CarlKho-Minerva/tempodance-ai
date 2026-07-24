# Daytona Devpost submission draft

> Deadline: **Friday, July 24, 2026 at 3:30 PM PDT.** Submit early; Devpost locks edits at the deadline.

This is prepared copy, not proof that every feature or sponsor path works. Run the final build, replace every placeholder, and delete every `TODO / UNVERIFIED` claim before pasting it into Devpost.

## Official pages

- [Devpost overview, requirements, prizes, and judging](https://daytona-hacksprint-sf-jul-2026.devpost.com/)
- [Official rules](https://daytona-hacksprint-sf-jul-2026.devpost.com/rules)
- [Official dates](https://daytona-hacksprint-sf-jul-2026.devpost.com/details/dates)
- [Luma event page](https://luma.com/hacksprint-sf)
- [Open the submission editor](https://devpost.com/submit-to/30557-daytona-hacksprint-w-braintrust-sf-july-2026/manage/submissions)
- Hackathon manager: [marijan@daytona.io](mailto:marijan@daytona.io)

## Eligibility check before submitting

- Only an **in-person team registered and approved on Luma** is eligible. The team must create and demo the project in person; remote participation is not allowed.
- Maximum team size is four.
- The code must be in a **public GitHub repository**. The rules do not require a newly created repository.
- Existing work is allowed only if the team created **at least one completely new feature during the hackathon** and clearly identifies that feature.
- Work must be primarily the team's own.
- The attendee update said the venue had reached capacity. Confirm that the team was actually admitted before representing the entry as eligible.

The copy below transparently distinguishes the earlier concept from today's implementation. Keep it only if repository history and the team's actual work support it.

## Copy-paste fields

### Project name

TempoDance AI

### Tagline

The private dance coach that measures every loop—and learns how to teach you better.

### Two-to-three-sentence summary

TempoDance AI is a local-first prototype that compares a learner with a built-in animated COCO-17 eight-count, identifies the lowest-scoring tracked limb, and evaluates the next loop's target delta. Its session memory and policy events are visible, and automatic speed progression requires stable mastery. A scripted Demo mode works without a camera, pose-model download, or cloud dependency.

### Problem and impact

Video tutorials can replay a move, but they cannot see why a learner keeps missing it. Most movement products give everyone the same instruction and one opaque score, leaving beginners to guess whether timing, an arm line, or a weight transfer is holding them back.

TempoDance turns each practice loop into an evaluated coaching trial. It finds the lowest-scoring tracked body segment, gives one focused correction, and records the next loop's target delta. Each reliable loop can initialize, retain, or revise a predefined focus and cue strategy; insufficient evidence holds it. In the documented localhost setup, frames go to the local FastAPI process for in-memory inference and are not persisted by application code. The hackathon prototype makes no medical or rehabilitation claims.

### Architecture and components

TempoDance separates measurement, coaching policy, and mastery. A browser workspace renders a built-in COCO-17 reference and learner skeleton and exposes pose score, per-bone alignment, selected focus, session memory, policy version, speed, and clean-loop streak. The live/API Python scorer compares normalized bone-direction vectors, handles mirror orientation, and confidence-gates missing joints; loop summaries feed an adaptive mastery state machine that moves through `0.5x → 0.6x → 0.8x → 1.0x` only after repeated qualifying evidence.

The no-camera path uses scripted landmark perturbations and a browser cosine scorer. With the local API connected, its score and per-bone values feed the server-side policy and mastery session; without the API, a scripted UI fallback keeps the walkthrough usable. Live camera frames use the Python pose/scoring path. An optional server adapter can send caller-provided frame images to Fireworks and parse a structured routine plan, but the browser does not yet supply those frames or display that result. Coaching cues and mastery are deterministic.

Before submitting, verify that the final running build supports every sentence above, especially camera pose extraction, the API route, and any Fireworks result.

### What was genuinely new on July 24, 2026

Before the event, TempoDance existed as a concept and architecture blueprint. During the hackathon we built its first working prototype: the judge-facing practice workspace, scale-invariant COCO-17 comparison with confidence and mirror handling, loop-level mastery gates, visible session memory and policy versions, deterministic failure-safe demo, and the optional provider boundary for routine analysis. The specifically new event-day feature is the evidence-driven coaching policy loop: it diagnoses a repeated weak motion, changes the next focus or cue strategy, evaluates the next loop's target delta, and unlocks speed only after consecutive qualifying loops.

Do not use that paragraph if any listed implementation predates the event or is not present in the submitted repository. Replace it with the narrower, provable event-day change and point judges to its commits.

### Safeguards

- In the localhost setup, camera frames go to the local FastAPI process and are not persisted by application code; a hosted API would receive those frames remotely.
- Missing or low-confidence bones reduce score and coverage; loops below the configured coverage or consistency gates cannot automatically promote speed.
- Automatic speed increases require consecutive qualifying loops; manual controls remain available.
- Numeric scoring, coaching cues, policy updates, and mastery gates are deterministic.
- The scripted path is visibly labeled **Demo mode / Deterministic dancer**.
- External calls have a deterministic fallback, so provider failure cannot break the core demo.
- The prototype is a learning aid, not a medical, diagnostic, or rehabilitation product.

### Built-with and sponsor integrations

Delete all unchecked sponsor lines before submission. A client file, environment variable, planned architecture, sponsor credit, or logo is **not** a verified integration; require a successful run and visible evidence.

#### Core technology — final verification still required

- Python
- FastAPI and Uvicorn — **TODO / verify that the final server starts and health/demo routes work**
- HTML, CSS, and browser Canvas
- COCO-17 pose landmarks and scale-invariant cosine scoring
- Ultralytics pose inference on Apple MPS — **TODO / verify live camera path before claiming**

#### Sponsor technology — do not claim until checked

- Fireworks AI — **TODO / UNVERIFIED.** A provider client exists, but record a successful credentialed vision request and resulting routine plan before claiming it. Redeem the event code separately; it is not an API key.
- Braintrust — **TODO / UNVERIFIED.** Add and capture a real trace or evaluation of the agent loop before claiming it.
- Daytona — **TODO / UNVERIFIED.** Run the project or its tests in an actual Daytona sandbox and retain the workspace/run evidence before claiming it.
- ElevenLabs — **TODO / UNVERIFIED; not currently implemented.** Claim only if generated coaching audio works in the submitted demo.
- CodeRabbit — **TODO / UNVERIFIED.** Claim only if the repository has an actual CodeRabbit review and the team can show what it improved.
- CopilotKit — **TODO / UNVERIFIED; not currently implemented.** Claim only if the submitted product uses a working CopilotKit interaction.
- WorkOS — **TODO / UNVERIFIED; not currently implemented.** Do not list venue hosting or an event benefit as product integration.

After verification, a concise sponsor paragraph can use this structure:

> We use **[verified sponsor]** to **[specific runtime job]**. In the demo, **[visible action]** produces **[visible result]**; if it fails, **[fallback behavior]** preserves safe operation. We used **[second verified sponsor]** to **[specific job and evidence]**.

## Exact submission requirements

The published Daytona requirements call for:

- A unique team name.
- Every team member listed; Devpost profiles should include contact email and social details so organizers can reach or tag the team.
- A public GitHub repository.
- A short screen-recorded demo **under two minutes**.
- A two-to-three-sentence project summary.
- The problem being solved and its impact.
- Key architecture and technical components.
- Every sponsor tool or protocol used and how it was integrated.

Devpost's [official participant guide](https://help.devpost.com/article/126-know-your-submission-steps) says the video must be publicly hosted on YouTube or Vimeo so it embeds for judges. Set it to Public, verify playback in a logged-out/private browser window, permit embedding, and upload early enough for processing. Keep the final cut below `2:00`; `1:50–1:55` is safer.

## Under-two-minute recording shot list

Target runtime: **1:52**.

| Time | Show | Narration goal |
|---|---|---|
| `0:00–0:09` | Title, product workspace, one-line problem | "Tutorials replay the move; TempoDance sees what I am missing and adapts the next coaching focus." |
| `0:09–0:24` | Leave **Demo mode** selected and press the circular play button | State that scripted landmarks use the browser scorer and feed the server policy when connected. |
| `0:24–0:43` | Pose score, per-bone alignment, and selected focus | Explain normalized bone geometry and the lowest-scoring tracked bone. |
| `0:43–1:04` | First loop completes; memory entry and policy version change | Show observation → diagnosis → intervention and name exactly what changed. |
| `1:04–1:25` | Next loop target delta and speed-gate evidence | Show that the server compares the target metric with its baseline and retains or revises the cue by rule. |
| `1:25–1:37` | Current speed and clean-loop streak, or retry outcome | Emphasize consecutive-loop mastery and coverage safeguards. |
| `1:37–1:46` | **Only verified** sponsor evidence: trace, sandbox run, or Fireworks result | Name the sponsor's concrete runtime role. Skip this shot if no integration is proven. |
| `1:46–1:52` | Final state/product mark | “TempoDance is the dance coach that learns how you learn.” |

Recording rules:

- Use the deterministic demo path unless live camera and every dependency have already passed twice.
- Keep browser zoom and text large enough for a judge watching in the Devpost player.
- Do not show API keys, `.env` values, private URLs, personal notifications, or unrelated tabs.
- Do not call scripted landmarks "live AI vision." Say exactly what is scripted and what logic is measured.
- If a sponsor path is not visible and successful, omit the claim rather than narrating planned work.

## Final pre-submit checklist

- [ ] Team is Luma-approved, physically admitted, and present to demo.
- [ ] Team has at most four people and all members are listed on Devpost.
- [ ] Public repository opens in a logged-out browser and contains the submitted code and run instructions.
- [ ] Event-day feature is identified honestly and supported by commit history.
- [ ] Fresh install or documented local launch succeeds.
- [ ] Full judge demo succeeds twice from a fresh session.
- [ ] Every sponsor named in Devpost has working code plus captured evidence.
- [ ] Video is public/embeddable, plays logged out, and is strictly under two minutes.
- [ ] Summary, impact, architecture, and sponsor-use fields are complete.
- [ ] Submission is finalized before **3:30 PM PDT**, then the confirmation page is saved.
