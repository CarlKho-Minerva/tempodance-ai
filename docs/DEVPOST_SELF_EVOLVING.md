# Self-Evolving Agents Devpost draft

> **DO NOT SUBMIT TempoDance AI TO THIS HACKATHON UNTIL THE ORGANIZER CONFIRMS ELIGIBILITY IN WRITING.**

The published rules say: “All projects must be created during the event — no previously started projects are permitted.” TempoDance had a concept and architecture blueprint before the event, and it may also be entered in Daytona. Neither event page explicitly bans cross-submission, and the Self-Evolving rules do not say that the GitHub repository itself must be newly created, but neither fact overrides the no-previously-started-project rule. Only the organizer can resolve whether a pre-existing concept with event-day implementation qualifies.

Organizer contact: [team@creatorscorner.co](mailto:team@creatorscorner.co)

## Ask for eligibility confirmation now

**Subject:** Eligibility check — event-day implementation of a prior TempoDance concept

> Hi Self-Evolving Agents team,
>
> Before July 24, TempoDance AI existed as a concept and architecture blueprint. The working prototype and adaptive coaching implementation were created during today's build session. We may also submit the prototype to the Daytona HackSprint, whose rules allow an existing base when a new event-day feature is identified.
>
> Does TempoDance satisfy your rule that all projects must be created during the event and that no previously started projects are permitted? Is entering the same event-day implementation in both hackathons allowed? We will not submit it to Self-Evolving Agents without your written confirmation.
>
> Repository: [PUBLIC REPOSITORY URL]
> Event-day commits: [COMMIT OR COMPARE URL]
>
> Thank you,
> [NAME / TEAM]

Save the response. If approval is qualified, follow every condition exactly. Silence is not approval.

## Official pages

- [Devpost overview, requirements, prizes, and judging](https://self-evolving-agents.devpost.com/)
- [Official rules](https://self-evolving-agents.devpost.com/rules)
- [Official dates](https://self-evolving-agents.devpost.com/details/dates)
- [Luma event page](https://luma.com/swarmhack)
- [Open the submission editor](https://devpost.com/submit-to/30800-self-evolving-agents-hackathon/manage/submissions)
- Hackathon manager: [team@creatorscorner.co](mailto:team@creatorscorner.co)

Deadline: **Friday, July 24, 2026 at 4:30 PM PDT.** Devpost lists demos and judging at 5:00 PM and awards at approximately 7:00 PM. The event is at DG717, 717 Market Street, San Francisco; the attendee notice warned that physical capacity would fill around 9:45 AM even for registered attendees.

## Eligibility and submission requirements

- All projects must be created during the event; previously started projects are prohibited.
- Maximum team size is four.
- The submission must link a **public GitHub repository**.
- The submission must include a **three-minute demo video**.
- All required Devpost project details must be complete before 4:30 PM PDT.
- Participants retain ownership of their submission IP.

The rules do not expressly say the repository must be newly created, nor do they expressly address dual submission. Do not interpret that silence as permission. Project/code provenance and cross-entry eligibility need organizer confirmation.

Devpost's [official participant guide](https://help.devpost.com/article/126-know-your-submission-steps) says the video must be publicly hosted on YouTube or Vimeo so it embeds for judges. Set it to Public, permit embedding, and verify playback while logged out. Aim for `2:50–2:55`, not a frame over `3:00`.

The published judging criteria have no displayed weights:

- **Idea:** meaningful problem or real-world value.
- **Technical Implementation:** quality of implementation.
- **Tool Use:** effective use of sponsor tools.
- **Presentation:** demonstration within the allotted time.
- **Autonomy:** acting on real-time data without manual intervention.

## Conditional copy-paste fields

Use this section **only after written organizer approval** and only after verifying every technical statement against the final running build.

### Project name

TempoDance AI

### Tagline

A dance-coaching agent that evaluates each completed server-side loop and initializes, retains, revises, or holds its teaching focus from measured evidence.

### Two-to-three-sentence summary

TempoDance AI is a local-first coaching agent that observes a dance attempt, diagnoses the lowest-scoring tracked motion, selects one predefined focus and cue strategy, and records the next loop's target delta. Its session memory and policy events are visible, while deterministic mastery gates keep progress tied to measured evidence. The result is an inspectable loop that adapts its teaching focus instead of replaying generic advice.

### Problem and impact

Movement tutorials are one-way: they show the same sequence to every learner but cannot identify the specific error blocking one person. A learner may repeat an entire routine when one arm angle, weight transfer, or confidence gap is responsible for most of the failure.

TempoDance converts practice into a closed feedback loop. It measures body geometry, focuses the next coaching rule on the weakest reliable signal, records the next loop's target delta, and updates the policy from that evidence. In the documented localhost setup, frames go to the local FastAPI process for in-memory inference and are not persisted by application code. The prototype is not a medical or rehabilitation product.

### Architecture and autonomous loop

The browser presents a built-in COCO-17 reference and learner skeleton plus pose score, per-bone alignment, attention target, session memory, policy version, speed, and clean-loop streak. A deterministic geometry engine compares normalized bone directions, handles mirror orientation, and confidence-gates missing joints. At each reliable loop boundary, the server aggregates per-bone medians, selects a weak-motion focus, and retains or rotates among predefined coaching rules; scoring weights and mastery gates remain fixed.

The no-camera demo uses scripted landmark perturbations and a browser cosine scorer. With the local API connected, its score and per-bone values feed the server-side policy and mastery session; without the API, a scripted UI fallback keeps the walkthrough usable. An optional Fireworks adapter can parse a structured routine plan from caller-provided frame images, but it is not connected to coaching or mastery.

### What was built during the July 24 event

TempoDance's concept and architecture blueprint existed before the event. During the July 24 build session, the team implemented the judge-facing workspace, scale-invariant pose comparison, confidence-aware loop summaries, adaptive mastery state machine, visible memory and policy versions, deterministic fallback flow, and optional analysis-provider boundary. The central event-day implementation is an evidence-driven agent loop that changes the next focus or cue strategy from the next loop's target delta rather than rewriting a prompt.

That disclosure is also the reason organizer approval is required. Do not soften it or present the project as starting from zero.

### Safeguards

- In the localhost setup, frames go to the local FastAPI process and are not persisted by application code; a hosted API would receive them remotely.
- Confidence and coverage gates prevent missing joints from becoming positive evidence.
- Automatic speed increases require consecutive qualifying loops; manual controls remain available.
- Numeric evidence controls mastery and server-side policy retention.
- The scripted path is visibly labeled **Demo mode / Deterministic dancer**.
- Deterministic fallback preserves the demo when an external service is unavailable.
- Visible state lets judges inspect what the agent observed, changed, and why.
- No medical, diagnostic, or rehabilitation claims.

## Built-with and sponsor integrations

Delete every unchecked sponsor from the final Devpost built-with list. Planned use, an account, event credits, or a logo does not count as effective tool use.

### Core technology — final verification still required

- Python
- FastAPI and Uvicorn — **TODO / verify final running service**
- HTML, CSS, and browser Canvas
- COCO-17 pose landmarks and scale-invariant scoring
- Ultralytics pose inference on Apple MPS — **TODO / verify live path before claiming**

### Event sponsors — currently unverified

- Guild AI — **TODO / UNVERIFIED; not currently implemented.** The award requires the best use of agents in Guild; run a real agent through Guild and show its role before claiming it.
- Pioneer — **TODO / UNVERIFIED; not currently implemented.** Claim only if real inference traffic plus feedback/correction is captured through Pioneer.
- Replay — **TODO / UNVERIFIED; QA not completed.** Its award specifically requires a well-designed SaaS app for a complex need, completed Replay QA, and **all discovered bugs fixed**. A scan without fixes is not enough.
- Actian VectorAI DB — **TODO / UNVERIFIED; not currently implemented.** Claim only if agent memory is actually written to and retrieved from Actian in the demo.
- Band — **TODO / UNVERIFIED; not currently implemented.** Claim only if the project actually uses Band for agent communication; a planned multi-agent diagram is insufficient.
- Senso.ai — **TODO / UNVERIFIED; not currently implemented.** Claim only if the running agent retrieves and uses Senso-hosted context.
- Google DeepMind / Gemini — **TODO / UNVERIFIED; not currently implemented.** Do not list event sponsorship as product integration.

Published sponsor-track conditions and awards are listed on the [Self-Evolving Devpost overview](https://self-evolving-agents.devpost.com/): Guild best use of agents in Guild; Replay SaaS with completed QA and all bugs fixed; Actian best use of VectorAI DB; Band best project using Band; and Senso best use. No Pioneer or DeepMind track conditions are published there. The page headline says `$19,000` cash, while its visible cash tracks total `$7,000`; do not repeat an inferred prize total as fact.

After a sponsor path is verified, describe it with evidence:

> We use **[verified sponsor]** for **[specific runtime action]**. When the learner completes a loop, **[input]** is sent/stored/traced through the sponsor tool and **[observable output]** changes **[specific agent behavior]**. The demo shows this at **[timestamp or screen]**.

## Three-minute recording shot list

Do not record a Self-Evolving submission video until eligibility is approved. If approved, target **2:54**.

| Time | Show | Narration goal |
|---|---|---|
| `0:00–0:16` | Product title and full workspace | Define the one-way tutorial problem and the autonomous coaching loop. |
| `0:16–0:36` | Start **Demo mode** with the circular play button | Explain that the browser scorer feeds the server policy when connected and has a scripted UI fallback. |
| `0:36–1:00` | Pose score, per-bone evidence, weak motion, and selected focus | Explain how the agent observes and selects the next coaching action from reliable data. |
| `1:00–1:28` | First loop completes; memory and policy version update | Show the precise state change and why it occurred. |
| `1:28–1:56` | Next loop target metric vs. its baseline | Demonstrate the server's retain/revise rule without claiming the cue caused the scripted improvement. |
| `1:56–2:17` | Mastery gate/speed result or safe retry | Show that autonomous progress has deterministic guardrails. |
| `2:17–2:35` | Agent audit trail or architecture view | Separate measurement, policy adaptation, and optional structured routine analysis. |
| `2:35–2:46` | **Only verified** sponsor runtime evidence | Show the concrete sponsor-mediated action and result. Omit if none is verified. |
| `2:46–2:54` | Final workspace state | “TempoDance is the coach that learns how you learn.” |

Recording rules:

- Demonstrate an uninterrupted observe → diagnose → adapt → evaluate cycle.
- Keep all state changes visible; autonomy must be observable, not merely described.
- Do not hide manual clicks. Explain which actions start a session and which decisions the agent makes on its own.
- Do not expose secrets, private URLs, attendee information, or notifications.
- Do not claim scripted input is a live camera or call a deterministic state transition an LLM decision.
- Include sponsor footage only after a successful integration run.

## Conditional final checklist

- [ ] Organizer provided written approval for the prior concept/event-day implementation and any dual submission.
- [ ] Every organizer condition is reflected in the repository and submission.
- [ ] Team has at most four people and all members are listed.
- [ ] Public repository opens while logged out and clearly shows event-day provenance.
- [ ] All submitted project details are complete.
- [ ] Fresh launch and the full autonomous loop pass twice.
- [ ] Every sponsor claim has working code and visible evidence.
- [ ] Public/embeddable video plays while logged out and is no longer than three minutes.
- [ ] Submission is finalized before **4:30 PM PDT**, and the confirmation page is saved.
- [ ] If written approval was not received: **do not submit**.
