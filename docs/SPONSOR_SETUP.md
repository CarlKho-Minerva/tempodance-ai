# Sponsor setup and proof checklist

Treat an integration as real only after its credentialed path succeeds and you save visible evidence. Never commit keys, credit codes, `.env`, response dumps containing secrets, or signed Daytona preview URLs.

## Fireworks AI — client implemented, credentialed run unverified

Official docs: [firectl setup](https://docs.fireworks.ai/tools-sdks/firectl/firectl), [redeem credits](https://docs.fireworks.ai/tools-sdks/firectl/commands/credit-redemption-redeem), [create an API key](https://docs.fireworks.ai/tools-sdks/firectl/commands/api-key-create), and [current vision-model example](https://docs.fireworks.ai/guides/querying-vision-language-models).

### 1. Redeem the credit code, then create a real API key

```bash
brew tap fw-ai/firectl
brew install firectl
firectl signin
firectl whoami
firectl credit-redemption redeem '<event-credit-code>'
firectl api-key create --key-name 'TempoDance Hackathon'
```

The redemption code adds credit to the signed-in account; it is **not** a bearer credential. Copy the newly created API key once and store it in a password manager, or create it from the [Fireworks API Keys dashboard](https://app.fireworks.ai/settings/users/api-keys).

### 2. Configure the app

Use a local `.env` that stays ignored. Leave the key blank in templates, put the real API key only in your ignored local copy, and never put the credit code in an environment file.

```dotenv
FIREWORKS_API_KEY=
FIREWORKS_MODEL=accounts/fireworks/models/kimi-k2p5
FIREWORKS_API_URL=https://api.fireworks.ai/inference/v1/chat/completions
TEMPO_ANALYZER_PROVIDER=fireworks
```

`accounts/fireworks/models/kimi-k2p5` is the model used by Fireworks' current vision guide. The client accepts `FIREWORKS_API_URL` for a full endpoint or `FIREWORKS_BASE_URL` for the API base; `FIREWORKS_API_URL` takes precedence. Start with:

```bash
./run.sh
```

### 3. Smoke-test through TempoDance

In another terminal:

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8000/api/sessions \
  -H 'Content-Type: application/json' \
  --data '{"routine_url":"smoke://eight-count","mode":"full","analysis_provider":"fireworks"}' \
  | jq -e '.analysis.provider == "fireworks" and .analysis.degraded_reason == null'
```

Success prints `true` and exits `0`. Any response with `analysis.provider` equal to `deterministic` is a fallback and does **not** prove Fireworks worked. This smoke test proves the credentialed routine-analyzer call; capture a successful image/keyframe request separately before claiming Fireworks vision.

## Braintrust — optional TODO, not implemented

Official docs: [tracing quickstart](https://www.braintrust.dev/docs/tracing-quickstart), [trace LLM calls](https://www.braintrust.dev/docs/instrument/trace-llm-calls), and [trace application logic](https://www.braintrust.dev/docs/instrument/trace-application-logic).

Shortest setup if there is time:

```bash
python -m pip install braintrust
export BRAINTRUST_API_KEY='<real Braintrust API key>'
```

Then initialize a `TempoDance AI` logger and trace the Fireworks analysis plus the observe → diagnose → policy-update loop with Braintrust's Python `@traced` decorator or `logger.start_span(...)`. This requires code changes that are **not present now**. Do not claim Braintrust until a real run appears in the Braintrust project Logs with inputs, outputs, timing, and the policy decision.

## Daytona — run the repository Dockerfile in a sandbox

Official docs: [Daytona CLI](https://www.daytona.io/docs/en/tools/cli/), [Dockerfile builder](https://www.daytona.io/docs/en/declarative-builder/), and [signed preview URLs](https://www.daytona.io/docs/en/preview/).

```bash
brew install daytonaio/cli/daytona
daytona login
daytona create --name tempodance-ai --dockerfile Dockerfile --context .
daytona exec tempodance-ai -- curl --fail --silent --show-error http://127.0.0.1:8000/api/health
daytona preview-url tempodance-ai --port 8000 --expires 3600
```

If the health check reports that nothing is listening, start the Dockerfile's service explicitly, then retry it:

```bash
daytona exec tempodance-ai --cwd /app -- sh -lc \
  'nohup python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 >/tmp/tempodance.log 2>&1 &'
daytona exec tempodance-ai -- curl --fail --silent --show-error http://127.0.0.1:8000/api/health
```

Save the successful sandbox health output and a screenshot of the app through the preview URL. A local `docker build` alone is not evidence of Daytona usage. Stop the sandbox when the demo is over with `daytona stop tempodance-ai`; this preserves its filesystem.

## Self-Evolving Agents sponsors — all unimplemented

Do nothing here unless the organizer first confirms TempoDance is eligible. If approval arrives, choose **at most one** integration that can be completed, tested, and shown end to end; several shallow SDK installs will weaken the demo and do not satisfy “effective tool use.”

- **Guild AI — unimplemented:** run the adaptive coach as an actual Guild agent/session. [Official Guild docs](https://docs.guild.ai/)
- **Pioneer — unimplemented:** route a real inference through Pioneer and capture feedback/correction if using the self-improvement story. [Official Pioneer quickstart](https://docs.pioneer.ai/quickstart)
- **Replay — unimplemented:** deploy a reachable app, complete Replay QA, and fix every reported bug; merely launching a scan does not meet the published prize condition. [Official Replay QA overview](https://docs.replay.io/basics/replay-qa/overview)
- **Actian VectorAI DB — unimplemented:** persist and retrieve actual coaching memory from VectorAI DB. [Official Actian quickstart](https://docs.vectoraidb.actian.com/home/quickstart/quickstart)
- **Band — unimplemented:** use genuine agent communication; a receiving agent needs both REST and WebSocket connectivity, while MCP alone cannot receive messages. [Official Band integration overview](https://docs.band.ai/integrations/overview)
- **Senso.ai — unimplemented:** retrieve grounded coaching or routine knowledge from an ingested source. [Official Senso quickstart](https://docs.senso.ai/docs/hello-world)
- **Google DeepMind / Gemini — unimplemented:** use a real Gemini multimodal or agent call only if it replaces a core path rather than duplicating Fireworks. [Official Gemini API docs](https://ai.google.dev/gemini-api/docs)

For this product, Pioneer is the clearest self-improvement fit; Replay is the fastest alternative only if a public deployment is already stable and there is enough time to complete QA and fix every finding. Keep all Self sponsor claims marked unimplemented until the running evidence exists.
