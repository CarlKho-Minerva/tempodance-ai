# Submission kit

## Copy-paste project description

**TempoDance AI** is a local-first dance coach. In the default localhost setup, a pose model turns webcam frames into landmarks; a scale-invariant scorer compares normalized limb directions with a built-in animated eight-count; and a session policy uses per-bone loop medians to choose a focus and coaching rule. It records whether the targeted metric improved and automatically raises speed only after stable mastery.

Most movement apps give everyone the same replay and one opaque score. TempoDance exposes the loop: observation → diagnosis → intervention → evaluation → policy update. The learner can see pose score, per-bone alignment, selected focus, session memory, policy version, current speed, and clean-loop streak. In the localhost setup, frames go only to the local FastAPI process and are not persisted by application code. A scripted no-camera mode demonstrates the flow without a model download or cloud API.

## One-line pitch

TempoDance AI is the dance coach that learns how you learn.

## Three-minute pitch

**0:00–0:25 — Problem**

"Dance tutorials can show the move, but they cannot see why I keep missing it. Rewatching at half speed gives every learner the same instruction, even when our errors are different."

**0:25–0:50 — Product**

"TempoDance watches body geometry, not body size. It compares normalized limb directions with the built-in reference, finds the limb that costs the most score, and selects a focused coaching rule for that error."

**0:50–1:45 — Live demo**

1. Leave **Demo mode** selected and press the circular play button.
2. Point out the reference and learner skeletons plus the per-bone error colors.
3. Let one loop finish; show the agent memory naming the repeated weak motion.
4. Show policy version increment and the cue changing for the next loop.
5. Let mastery stabilize; show the reasoned speed increase from `0.5x` to `0.6x`.

**1:45–2:25 — Self-evolution**

"This is not a chat wrapper. After each completed server-side loop, the agent compares the targeted bone's median with its prior baseline and initializes, retains, revises, or holds a predefined focus and coaching-rule strategy. A reliable improvement of at least 1.5 percentage points retains the intervention; scoring weights and mastery gates stay fixed."

**2:25–2:45 — Safety and reliability**

"In this localhost demo, camera frames go to the local FastAPI process for in-memory inference and are not persisted by application code. Missing or low-confidence bones reduce score and coverage; loops below the coverage or consistency gates cannot automatically promote speed. The scripted demo removes camera, pose-model-download, and external-provider risk."

**2:45–3:00 — Close**

"Today it learns how to teach one eight-count. Next it becomes a reusable motor-learning layer for more dance styles and sport practice. TempoDance is the coach that learns how you learn."

## Daytona / Braintrust angle

- Agent behavior is measurable: per-bone score, loop delta, promotion decisions, and policy version.
- An optional Fireworks adapter can parse a structured routine plan from caller-supplied frame images, but the browser does not yet supply or render that result.
- The scripted trace could become a Braintrust eval, but Braintrust is not currently integrated.
- A Dockerfile is present, but no Daytona sandbox run has been captured; do not claim Daytona usage until it is verified.

Do not claim a sponsor integration in the final submission unless its credentialed path has actually been run and captured.

## Self-Evolving Agents angle

- State persists across loops rather than resetting after each prompt.
- The server policy retains or revises a predefined focus and coaching-rule strategy from the next loop's targeted-metric delta.
- Geometry, coaching cues, policy updates, and mastery gates are deterministic in the current build.
- The UI makes agent state legible, which lets a judge inspect what changed and why.

## Safeguards

- In the documented localhost setup, frames go to the local API for in-memory processing and are not persisted by application code.
- Confidence gating for missing/occluded joints.
- Stable multi-loop evidence before an automatic speed promotion; manual controls remain available.
- Deterministic fallback if an external model fails.
- The scripted path is visibly labeled **Demo mode / Deterministic dancer**.
- No medical or rehabilitation claims in the hackathon prototype.

## Final submission checklist

- [ ] Run the full judge demo twice from a fresh server.
- [ ] Record a 45–60 second backup video.
- [ ] Capture one workspace screenshot and one agent-memory close-up.
- [ ] Add the repository URL and live/local demo instructions.
- [ ] Name only sponsor APIs that were actually exercised.
- [ ] Verify project title, team members, and contact email.
- [ ] Submit before the event form closes; save the confirmation page.

## Judge questions

**Is the self-evolution just prompt rewriting?**
No. Policy updates are downstream of numeric loop outcomes. The current optional Fireworks adapter is isolated from scoring, coaching, policy, and mastery.

**How do you handle different body sizes?**
The scorer compares normalized bone directions rather than raw pixel distances.

**What happens when the pose model loses a wrist or ankle?**
Low-confidence bones are marked invalid, so score and coverage fall. Loops below the configured coverage or consistency gates cannot automatically promote speed.

**Why will users trust the coach?**
The UI exposes the weak motion, current score, selected focus and rule, recent policy event, speed tier, and clean-loop streak.

**What would you build next?**
Extract synchronized reference landmarks from uploaded/tutorial video, add beat alignment, then run controlled evaluation of cue policies across learners.
