const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const query = new URLSearchParams(window.location.search);
const API_ORIGIN = (query.get("api") || (window.location.protocol === "file:" ? "http://127.0.0.1:8000" : window.location.origin)).replace(/\/$/, "");
const WS_ORIGIN = API_ORIGIN.replace(/^http/, "ws");

const SPEEDS = [0.5, 0.6, 0.8, 1];
const BASE_BEAT_MS = 320;
const SCORE_RING_LENGTH = 138.23;
const FOCUS = "full";

// COCO-17: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles.
const COCO_BONES = [
  [0, 1], [0, 2], [1, 3], [2, 4],
  [3, 5], [4, 6],
  [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],
  [5, 11], [6, 12], [11, 12],
  [11, 13], [13, 15], [12, 14], [14, 16],
];

const SCORE_BONES = [
  { name: "left_upper_arm", label: "Left shoulder", pair: [5, 7] },
  { name: "left_forearm", label: "Left wrist", pair: [7, 9] },
  { name: "right_upper_arm", label: "Right shoulder", pair: [6, 8] },
  { name: "right_forearm", label: "Right wrist", pair: [8, 10] },
  { name: "left_thigh", label: "Left knee", pair: [11, 13] },
  { name: "left_shin", label: "Left ankle", pair: [13, 15] },
  { name: "right_thigh", label: "Right knee", pair: [12, 14] },
  { name: "right_shin", label: "Right ankle", pair: [14, 16] },
];

const JOINT_LABELS = [
  "Nose", "Left eye", "Right eye", "Left ear", "Right ear",
  "Left shoulder", "Right shoulder", "Left elbow", "Right elbow",
  "Left wrist", "Right wrist", "Left hip", "Right hip",
  "Left knee", "Right knee", "Left ankle", "Right ankle",
];

const REFERENCE_KEYFRAMES = [
  [[.50,.16],[.485,.15],[.515,.15],[.47,.16],[.53,.16],[.42,.29],[.58,.29],[.36,.43],[.64,.43],[.32,.57],[.68,.57],[.45,.55],[.55,.55],[.39,.72],[.61,.72],[.35,.89],[.65,.89]],
  [[.48,.15],[.465,.14],[.495,.14],[.45,.15],[.515,.15],[.40,.29],[.56,.30],[.32,.20],[.65,.42],[.26,.10],[.72,.51],[.43,.54],[.54,.56],[.37,.70],[.64,.72],[.34,.88],[.69,.87]],
  [[.50,.15],[.485,.14],[.515,.14],[.47,.15],[.53,.15],[.41,.29],[.59,.29],[.28,.30],[.72,.30],[.15,.34],[.85,.34],[.44,.55],[.56,.55],[.36,.71],[.64,.71],[.31,.88],[.69,.88]],
  [[.52,.16],[.505,.15],[.535,.15],[.49,.16],[.55,.16],[.43,.30],[.61,.29],[.36,.17],[.67,.18],[.43,.09],[.60,.08],[.46,.56],[.57,.54],[.39,.73],[.64,.68],[.35,.90],[.70,.83]],
  [[.52,.16],[.505,.15],[.535,.15],[.49,.16],[.55,.16],[.44,.29],[.60,.30],[.35,.43],[.69,.20],[.31,.57],[.75,.10],[.46,.55],[.57,.56],[.39,.71],[.65,.74],[.34,.87],[.71,.90]],
  [[.50,.15],[.485,.14],[.515,.14],[.47,.15],[.53,.15],[.41,.29],[.59,.29],[.29,.35],[.71,.35],[.18,.43],[.82,.43],[.44,.54],[.56,.54],[.38,.66],[.62,.76],[.31,.80],[.68,.92]],
  [[.48,.16],[.465,.15],[.495,.15],[.45,.16],[.515,.16],[.40,.30],[.57,.29],[.34,.43],[.65,.41],[.42,.51],[.72,.50],[.43,.55],[.54,.54],[.35,.74],[.61,.68],[.29,.91],[.67,.83]],
  [[.50,.14],[.485,.13],[.515,.13],[.47,.14],[.53,.14],[.41,.28],[.59,.28],[.35,.16],[.65,.16],[.47,.08],[.53,.08],[.44,.53],[.56,.53],[.38,.70],[.62,.70],[.34,.87],[.66,.87]],
];

const state = {
  mode: "demo",
  playing: false,
  analyzing: false,
  speedIndex: 0,
  phase: 0,
  currentCount: 1,
  completedLoops: 0,
  cleanLoops: 0,
  loopMinimum: 1,
  elapsedPlayingMs: 0,
  sessionStartedAt: null,
  lastFrameAt: performance.now(),
  lastObservationAt: 0,
  observationInFlight: false,
  lastChartAt: 0,
  sessionId: null,
  remoteSession: false,
  sessionRequest: null,
  socket: null,
  socketReady: false,
  socketReconnects: 0,
  cameraStream: null,
  cameraReady: false,
  serverPose: null,
  score: null,
  boneScores: {},
  latestReference: clonePose(REFERENCE_KEYFRAMES[0]),
  latestLive: null,
  timingOffset: null,
  chartScores: [],
  memories: [],
  policyVersion: 1,
  remoteCoaching: null,
  remoteLearning: null,
  lastSocketSentAt: 0,
  routineKeyframes: REFERENCE_KEYFRAMES,
};

const elements = {
  referenceCanvas: $("#referenceCanvas"),
  liveCanvas: $("#liveCanvas"),
  captureCanvas: $("#captureCanvas"),
  cameraVideo: $("#cameraVideo"),
  playButton: $("#playButton"),
  analyzeButton: $("#analyzeButton"),
  routineUrl: $("#routineUrl"),
  routineName: $("#routineName"),
  routineBpm: $("#routineBpm"),
  referenceLoading: $("#referenceLoading"),
  cameraEmpty: $("#cameraEmpty"),
  cameraError: $("#cameraError"),
  cameraErrorText: $("#cameraErrorText"),
  demoModeButton: $("#demoModeButton"),
  cameraModeButton: $("#cameraModeButton"),
  enableCameraButton: $("#enableCameraButton"),
  useDemoFallbackButton: $("#useDemoFallbackButton"),
  connectionDot: $("#connectionDot"),
  connectionLabel: $("#connectionLabel"),
  sessionClock: $("#sessionClock"),
  statusBanner: $("#statusBanner"),
  statusBannerText: $("#statusBannerText"),
  stageScore: $("#stageScore"),
  scoreRing: $("#scoreRing"),
  latencyLabel: $("#latencyLabel"),
  livePanelTitle: $("#livePanelTitle"),
  liveBadge: $("#liveBadge"),
  watermarkCount: $("#watermarkCount"),
  timelineFill: $("#timelineFill"),
  transportTitle: $("#transportTitle"),
  transportHint: $("#transportHint"),
  cleanLoops: $("#cleanLoops"),
  accuracyMetric: $("#accuracyMetric"),
  accuracyDelta: $("#accuracyDelta"),
  timingMetric: $("#timingMetric"),
  timingDelta: $("#timingDelta"),
  attentionMetric: $("#attentionMetric"),
  attentionDelta: $("#attentionDelta"),
  agentStateText: $("#agentStateText"),
  coachMessage: $("#coachMessage"),
  coachCue: $("#coachCue"),
  messageConfidence: $("#messageConfidence"),
  memoryEmpty: $("#memoryEmpty"),
  memoryList: $("#memoryList"),
  memoryCount: $("#memoryCount"),
  policyVersion: $("#policyVersion"),
  policyStatus: $("#policyStatus"),
  policyRule: $("#policyRule"),
  chartLine: $("#chartLine"),
  chartArea: $("#chartArea"),
  privacyDialog: $("#privacyDialog"),
  toastRegion: $("#toastRegion"),
};

function clonePose(pose) {
  return pose.map(([x, y]) => [x, y]);
}

function clamp(value, min = 0, max = 1) {
  return Math.max(min, Math.min(max, value));
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function smoothstep(t) {
  return t * t * (3 - 2 * t);
}

function formatTime(milliseconds) {
  const total = Math.floor(milliseconds / 1000);
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

function getReferencePose(phase) {
  const keyframes = state.routineKeyframes;
  const position = phase * keyframes.length;
  const index = Math.floor(position) % keyframes.length;
  const nextIndex = (index + 1) % keyframes.length;
  const amount = smoothstep(position - Math.floor(position));
  return keyframes[index].map(([x, y], joint) => [
    lerp(x, keyframes[nextIndex][joint][0], amount),
    lerp(y, keyframes[nextIndex][joint][1], amount),
  ]);
}

function createDemoPose(reference, timestamp) {
  const pose = clonePose(reference);
  const progress = clamp((state.elapsedPlayingMs - 900) / 6800);
  const error = lerp(0.105, 0.026, progress);
  const wave = Math.sin(timestamp / 370);
  const counterWave = Math.cos(timestamp / 490);

  // Stable, deterministic mistakes: the agent can visibly diagnose and reduce them.
  pose[8][0] -= error * 0.32;
  pose[8][1] += error * 0.22;
  pose[10][0] -= error * (0.95 + wave * 0.12);
  pose[10][1] += error * 0.55;
  pose[7][0] += error * 0.18;
  pose[9][0] += error * (0.55 + counterWave * 0.1);
  pose[13][0] += error * 0.42;
  pose[15][0] += error * 0.58;
  pose[14][1] += error * 0.16;
  pose[16][0] -= error * 0.18;

  const bodySway = Math.sin(timestamp / 720) * 0.008;
  return pose.map(([x, y]) => [clamp(x + bodySway, 0.04, 0.96), clamp(y, 0.04, 0.96)]);
}

function cosineSimilarity(a, b) {
  const dot = a[0] * b[0] + a[1] * b[1];
  const lengthA = Math.hypot(a[0], a[1]);
  const lengthB = Math.hypot(b[0], b[1]);
  if (lengthA < 0.0001 || lengthB < 0.0001) return 0;
  return clamp(dot / (lengthA * lengthB));
}

function calculatePoseScore(live, reference, demoPenalty = 0) {
  const boneScores = {};
  for (const bone of SCORE_BONES) {
    const [start, end] = bone.pair;
    if (!live[start] || !live[end] || !reference[start] || !reference[end]) {
      boneScores[bone.name] = 0;
      continue;
    }
    const liveVector = [live[end][0] - live[start][0], live[end][1] - live[start][1]];
    const refVector = [reference[end][0] - reference[start][0], reference[end][1] - reference[start][1]];
    boneScores[bone.name] = clamp(cosineSimilarity(liveVector, refVector) - demoPenalty);
  }
  return {
    score: Object.values(boneScores).reduce((sum, value) => sum + value, 0) / SCORE_BONES.length,
    boneScores,
  };
}

function resizeCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.round(rect.width * dpr);
  const height = Math.round(rect.height * dpr);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const context = canvas.getContext("2d");
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
  context.clearRect(0, 0, rect.width, rect.height);
  return { context, width: rect.width, height: rect.height };
}

function mappedPoint(point, width, height) {
  return [width * (0.07 + point[0] * 0.86), height * (0.035 + point[1] * 0.92)];
}

function colorForScore(score) {
  if (score == null) return "#b7ff5a";
  if (score >= 0.9) return "#b7ff5a";
  if (score >= 0.78) return "#ffd36b";
  return "#ff7d69";
}

function scoreForJoint(index, boneScores) {
  const relevant = SCORE_BONES.filter((bone) => bone.pair.includes(index));
  if (!relevant.length) return null;
  const values = relevant.map((bone) => boneScores[bone.name]).filter(Number.isFinite);
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function scoreForBone(pair, boneScores) {
  const found = SCORE_BONES.find((bone) => bone.pair[0] === pair[0] && bone.pair[1] === pair[1]);
  return found ? boneScores[found.name] : null;
}

function renderSkeleton(canvas, pose, options = {}) {
  const resized = resizeCanvas(canvas);
  if (!resized || !pose?.length) return;
  const { context: ctx, width, height } = resized;
  const points = pose.map((point) => mappedPoint(point, width, height));
  const primary = options.primary || "#b7ff5a";
  const boneScores = options.boneScores || {};

  if (options.trailPose) {
    const trailPoints = options.trailPose.map((point) => mappedPoint(point, width, height));
    ctx.save();
    ctx.globalAlpha = 0.12;
    ctx.strokeStyle = primary;
    ctx.lineWidth = 2;
    for (const [start, end] of COCO_BONES) {
      ctx.beginPath();
      ctx.moveTo(...trailPoints[start]);
      ctx.lineTo(...trailPoints[end]);
      ctx.stroke();
    }
    ctx.restore();
  }

  for (const pair of COCO_BONES) {
    const [start, end] = pair;
    if (!points[start] || !points[end]) continue;
    const score = scoreForBone(pair, boneScores);
    const color = options.feedback ? colorForScore(score) : primary;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(...points[start]);
    ctx.lineTo(...points[end]);
    ctx.lineCap = "round";
    ctx.lineWidth = options.feedback && score != null && score < 0.78 ? 5 : 3.4;
    ctx.strokeStyle = color;
    ctx.shadowBlur = options.feedback && score != null && score < 0.78 ? 14 : 9;
    ctx.shadowColor = color;
    ctx.stroke();
    ctx.restore();
  }

  points.forEach(([x, y], index) => {
    const jointScore = scoreForJoint(index, boneScores);
    const color = options.feedback ? colorForScore(jointScore) : primary;
    if (options.feedback && jointScore != null && jointScore < 0.78) {
      ctx.beginPath();
      ctx.arc(x, y, 11, 0, Math.PI * 2);
      ctx.fillStyle = `${color}20`;
      ctx.fill();
    }
    ctx.beginPath();
    ctx.arc(x, y, index <= 4 ? 2.6 : 4.1, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.shadowBlur = 9;
    ctx.shadowColor = color;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.beginPath();
    ctx.arc(x, y, index <= 4 ? 1 : 1.4, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255,255,255,.9)";
    ctx.fill();
  });

  // A subtle center-of-mass guide makes the pose output feel analytical.
  const hipCenter = [(points[11][0] + points[12][0]) / 2, (points[11][1] + points[12][1]) / 2];
  ctx.save();
  ctx.setLineDash([2, 5]);
  ctx.strokeStyle = options.feedback ? "rgba(183,255,90,.18)" : "rgba(159,131,255,.18)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(hipCenter[0], hipCenter[1]);
  ctx.lineTo(hipCenter[0], height * .88);
  ctx.stroke();
  ctx.restore();
}

function clearCanvas(canvas) {
  const resized = resizeCanvas(canvas);
  if (!resized) return;
}

function updateScoreUI() {
  if (!Number.isFinite(state.score)) {
    elements.stageScore.textContent = "--";
    elements.accuracyMetric.textContent = "--";
    elements.scoreRing.style.strokeDashoffset = SCORE_RING_LENGTH;
    return;
  }
  const percent = Math.round(state.score * 100);
  elements.stageScore.textContent = percent;
  elements.accuracyMetric.textContent = `${percent}%`;
  elements.scoreRing.style.strokeDashoffset = SCORE_RING_LENGTH * (1 - state.score);
  elements.scoreRing.style.stroke = colorForScore(state.score);
  elements.accuracyDelta.textContent = percent >= 90 ? "Mastery range" : percent >= 85 ? "Building consistency" : "One correction at a time";

  const weakest = SCORE_BONES
    .map((bone) => ({ ...bone, score: state.boneScores[bone.name] }))
    .filter((bone) => Number.isFinite(bone.score))
    .sort((a, b) => a.score - b.score)[0];
  const remoteWeakest = state.remoteSession ? state.remoteLearning?.weakest : null;
  if (remoteWeakest) {
    elements.attentionMetric.textContent = remoteWeakest.label;
    elements.attentionDelta.textContent = remoteWeakest.detail;
  } else if (weakest) {
    elements.attentionMetric.textContent = weakest.label;
    elements.attentionDelta.textContent = `${Math.round(weakest.score * 100)}% aligned · active cue`;
  }
}

function updateTimingUI() {
  state.timingOffset = null;
  if (state.mode === "camera") {
    elements.timingMetric.textContent = "--";
    elements.timingDelta.textContent = "Timing analysis not implemented";
    return;
  }
  if (!state.playing) return;
  elements.timingMetric.textContent = "Scripted";
  elements.timingDelta.textContent = "Demo timing preview";
}

function updateCountUI() {
  elements.watermarkCount.textContent = state.currentCount;
  elements.timelineFill.style.width = `${state.phase * 100}%`;
  $$(".count-marker").forEach((marker, index) => {
    marker.classList.toggle("active", index + 1 === state.currentCount);
    marker.classList.toggle("done", index + 1 < state.currentCount);
  });
}

function setAgentStep(step) {
  const mapping = {
    observe: ["#stepObserve", "Observing"],
    diagnose: ["#stepDiagnose", "Diagnosing"],
    adapt: ["#stepAdapt", "Adapting policy"],
  };
  ["#stepObserve", "#stepDiagnose", "#stepAdapt"].forEach((id) => $(id).classList.remove("active"));
  $(mapping[step][0]).classList.add("active");
  elements.agentStateText.textContent = mapping[step][1];
}

function updateAgentUI() {
  if (!state.playing) {
    setAgentStep("observe");
    elements.agentStateText.textContent = state.score == null ? "Ready to observe" : "Paused safely";
    return;
  }
  const cycle = state.phase % 1;
  if (cycle < .52) setAgentStep("observe");
  else if (cycle < .83) setAgentStep("diagnose");
  else setAgentStep("adapt");

  const elapsed = state.elapsedPlayingMs;
  if (state.remoteSession && state.remoteCoaching) {
    elements.coachMessage.textContent = state.remoteCoaching;
    elements.messageConfidence.textContent = "server policy";
  } else if (state.remoteSession) {
    elements.coachMessage.textContent = "Evaluating this loop against your learned movement profile.";
    elements.messageConfidence.textContent = "agent evaluating";
  } else if (elapsed < 900) {
    elements.coachMessage.textContent = "Reading your range, rhythm, and stable joints. Keep moving naturally.";
    elements.messageConfidence.textContent = "scripted setup";
  } else if (elapsed < 3600) {
    elements.coachMessage.textContent = "Lift your right wrist through the count instead of reaching sideways.";
    elements.messageConfidence.textContent = "scripted demo cue";
  } else if (elapsed < 7200) {
    elements.coachMessage.textContent = "That wrist path is cleaner. Land the left knee a fraction earlier on count six.";
    elements.messageConfidence.textContent = "scripted demo cue";
  } else {
    elements.coachMessage.textContent = "Your shape is stable at this tempo. Repeat two clean loops to unlock the next speed.";
    elements.messageConfidence.textContent = "scripted demo cue";
  }
  elements.coachCue.hidden = elapsed < 900;

  if (!state.remoteSession) {
    const desiredMemories = [];
    if (elapsed >= 1100) desiredMemories.push({ title: "Scripted right-wrist pattern", detail: "Demo fallback cue", score: "preview" });
    if (elapsed >= 3200) desiredMemories.push({ title: "Demo cue preference", detail: "Scripted fallback state", score: "preview" });
    if (elapsed >= 5900) desiredMemories.push({ title: "Scripted timing preview", detail: "Not measured from audio", score: "demo" });
    if (desiredMemories.length !== state.memories.length) {
      state.memories = desiredMemories;
      renderMemories();
    }
  }

  if (state.remoteSession && state.remoteLearning?.policy) {
    elements.policyRule.textContent = state.remoteLearning.policy;
    elements.policyStatus.textContent = "Server applied";
  } else if (state.remoteSession) {
    elements.policyRule.textContent = "Waiting for enough live evidence to revise the coaching policy.";
    elements.policyStatus.textContent = "Evaluating";
  } else if (elapsed < 2500) {
    elements.policyRule.innerHTML = "<b>Baseline:</b> scan full body equally.";
    elements.policyStatus.textContent = "Learning";
  } else if (elapsed < 6500) {
    elements.policyRule.innerHTML = "<b>Updated:</b> prioritize right-arm path for 2 counts.";
    elements.policyStatus.textContent = "Applied";
  } else {
    elements.policyRule.innerHTML = "<b>Updated:</b> fade solved cues; shift attention to timing.";
    elements.policyStatus.textContent = "Applied";
  }
}

function renderMemories() {
  const remoteCount = state.remoteSession ? Number(state.remoteLearning?.memoryCount) : NaN;
  elements.memoryCount.textContent = Number.isFinite(remoteCount)
    ? `${remoteCount} signal${remoteCount === 1 ? "" : "s"}`
    : `${state.memories.length} signal${state.memories.length === 1 ? "" : "s"}`;
  elements.memoryEmpty.hidden = state.memories.length > 0;
  elements.memoryList.hidden = state.memories.length === 0;
  elements.memoryList.replaceChildren();
  state.memories.forEach((memory) => {
    const item = document.createElement("div");
    item.className = "memory-item";
    const dot = document.createElement("i");
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const detail = document.createElement("small");
    const score = document.createElement("span");
    title.textContent = memory.title;
    detail.textContent = memory.detail;
    score.textContent = memory.score;
    copy.append(title, detail);
    item.append(dot, copy, score);
    elements.memoryList.append(item);
  });
}

function updateChart(now) {
  if (!state.playing || !Number.isFinite(state.score) || now - state.lastChartAt < 420) return;
  state.lastChartAt = now;
  state.chartScores.push(state.score);
  if (state.chartScores.length > 28) state.chartScores.shift();
  const values = state.chartScores;
  if (values.length < 2) return;
  const points = values.map((value, index) => {
    const x = (index / (values.length - 1)) * 280;
    const y = 58 - clamp((value - .55) / .45) * 51;
    return [x, y];
  });
  const path = points.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  elements.chartLine.setAttribute("d", path);
  elements.chartArea.setAttribute("d", `${path} L280,64 L0,64 Z`);
}

function handleCompletedLoop() {
  state.completedLoops += 1;
  const passed = state.loopMinimum >= .85;
  state.cleanLoops = passed ? Math.min(2, state.cleanLoops + 1) : 0;
  state.loopMinimum = 1;
  elements.cleanLoops.textContent = state.cleanLoops;

  if (passed) {
    toast(`Clean loop ${state.cleanLoops}/2 · minimum frame score held above 85%`);
  } else {
    elements.transportHint.textContent = "The coach isolated one cue; repeat without adding new changes.";
  }

  if (state.cleanLoops >= 2 && state.speedIndex < SPEEDS.length - 1) {
    const previous = state.speedIndex;
    state.speedIndex += 1;
    state.cleanLoops = 0;
    state.policyVersion += 1;
    elements.cleanLoops.textContent = "0";
    elements.policyVersion.textContent = `Policy v1.${state.policyVersion - 1}`;
    updateSpeedUI(previous);
    toast(`Mastery unlocked · coach speed is now ${SPEEDS[state.speedIndex].toFixed(1)}×`);
  }
}

function updateSpeedUI(previousIndex = null) {
  $$(".speed-tier").forEach((button, index) => {
    button.classList.toggle("active", index === state.speedIndex);
    if (previousIndex != null && index <= previousIndex) button.classList.add("passed");
  });
}

function normalizeScore(value) {
  if (value == null || value === "") return null;
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return clamp(number > 1 ? number / 100 : number);
}

function normalizeBoneScores(payload) {
  const source = payload?.bone_scores ?? payload?.joint_scores ?? payload?.scores?.bones ?? payload?.pose?.bone_scores;
  if (!source) return {};
  if (Array.isArray(source)) {
    const normalized = {};
    source.forEach((entry, index) => {
      if (entry && typeof entry === "object") {
        const rawName = String(entry.name ?? entry.bone ?? entry.segment ?? SCORE_BONES[index]?.name ?? "")
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "_")
          .replace(/^_|_$/g, "");
        const matched = SCORE_BONES.find((bone) => bone.name === rawName)
          ?? SCORE_BONES.find((bone) => rawName.includes(bone.name))
          ?? SCORE_BONES[index];
        const value = normalizeScore(entry.similarity ?? entry.score ?? entry.value ?? entry.accuracy);
        if (matched && value != null) normalized[matched.name] = value;
      } else if (SCORE_BONES[index]) {
        normalized[SCORE_BONES[index].name] = normalizeScore(entry) ?? 0;
      }
    });
    return normalized;
  }
  const normalized = {};
  for (const bone of SCORE_BONES) {
    const value = source[bone.name] ?? source[bone.label] ?? source[bone.name.replaceAll("_", " ")];
    if (value != null) normalized[bone.name] = normalizeScore(value);
  }
  return normalized;
}

function normalizePose(raw, payload = {}) {
  if (!raw) return null;
  const points = Array.isArray(raw) ? raw : raw.keypoints ?? raw.points ?? raw.xy;
  if (!Array.isArray(points) || points.length < 17) return null;
  const parsed = points.slice(0, 17).map((point) => {
    if (Array.isArray(point)) return [Number(point[0]), Number(point[1])];
    return [Number(point.x), Number(point.y)];
  });
  if (parsed.some(([x, y]) => !Number.isFinite(x) || !Number.isFinite(y))) return null;
  const maxCoordinate = Math.max(...parsed.flat().map(Math.abs));
  if (maxCoordinate <= 2) return parsed.map(([x, y]) => [clamp(x), clamp(y)]);
  const width = Number(payload.width ?? payload.image_width ?? payload.frame_width ?? elements.cameraVideo.videoWidth ?? 1);
  const height = Number(payload.height ?? payload.image_height ?? payload.frame_height ?? elements.cameraVideo.videoHeight ?? 1);
  return parsed.map(([x, y]) => [clamp(x / width), clamp(y / height)]);
}

function extractCoaching(payload) {
  const candidate = payload?.coaching ?? payload?.coach_message ?? payload?.feedback ?? payload?.agent?.message ?? payload?.observation?.coaching;
  if (typeof candidate === "string") return candidate;
  if (candidate && typeof candidate === "object") return candidate.message ?? candidate.text ?? candidate.next_best_action ?? null;
  return null;
}

function applyBackendPayload(payload, source = "api") {
  if (!payload || typeof payload !== "object") return;
  const nested = payload.data ?? payload.result ?? payload.observation ?? payload;
  const backendState = nested.state && typeof nested.state === "object" ? nested.state : {};
  const pose = normalizePose(
    nested.user_keypoints ?? nested.keypoints ?? nested.pose?.keypoints ?? nested.pose,
    nested,
  );
  if (pose) {
    // The camera preview is mirrored, so its pose overlay must mirror as well.
    state.serverPose = pose.map(([x, y]) => [1 - x, y]);
  }

  const backendScore = normalizeScore(nested.score ?? nested.accuracy ?? nested.frame_score ?? nested.pose_score);
  const backendBones = normalizeBoneScores(nested);
  if (backendScore != null) state.score = backendScore;
  if (Object.keys(backendBones).length) state.boneScores = backendBones;
  const coaching = extractCoaching(nested);
  if (coaching) state.remoteCoaching = coaching;

  const speedValue = nested.speed
    ?? nested.current_speed
    ?? nested.playback_speed
    ?? nested.speed_tier
    ?? nested.mastery?.speed
    ?? nested.policy?.speed
    ?? backendState.speed;
  const parsedSpeed = Number.parseFloat(String(speedValue ?? "").replace("×", ""));
  const remoteSpeedIndex = SPEEDS.findIndex((speed) => Math.abs(speed - parsedSpeed) < .001);
  if (remoteSpeedIndex >= 0 && remoteSpeedIndex !== state.speedIndex) {
    const previous = state.speedIndex;
    state.speedIndex = remoteSpeedIndex;
    updateSpeedUI(remoteSpeedIndex > previous ? previous : null);
    toast(`Agent policy set coach speed to ${SPEEDS[remoteSpeedIndex].toFixed(1)}×`);
  }

  const remoteCleanLoops = Number(
    nested.clean_loops
    ?? nested.mastery_streak
    ?? nested.mastery?.clean_loops
    ?? nested.mastery?.streak
    ?? backendState.qualifying_streak
    ?? backendState.clean_loops,
  );
  if (Number.isFinite(remoteCleanLoops)) {
    state.cleanLoops = clamp(Math.round(remoteCleanLoops), 0, 2);
    elements.cleanLoops.textContent = state.cleanLoops;
  }

  const policy = nested.policy ?? nested.agent?.policy ?? nested.coaching_policy ?? backendState.policy;
  const version = nested.policy_version ?? nested.agent?.policy_version ?? policy?.version;
  if (version != null) elements.policyVersion.textContent = String(version).startsWith("v") ? `Policy ${version}` : `Policy v${version}`;
  const policyRule = typeof policy === "string" ? policy : policy?.rule ?? policy?.description ?? policy?.change;
  if (policyRule) {
    state.remoteLearning = { ...(state.remoteLearning || {}), policy: String(policyRule) };
    elements.policyRule.textContent = policyRule;
    elements.policyStatus.textContent = "Server applied";
  }

  const weakestRaw = nested.weakest_bone
    ?? nested.weakest_joint
    ?? nested.diagnosis?.weakest_bone
    ?? nested.agent?.weakest_bone
    ?? backendState.weakest_bone;
  let normalizedWeakest = null;
  if (weakestRaw) {
    const rawName = typeof weakestRaw === "string"
      ? weakestRaw
      : weakestRaw.name ?? weakestRaw.bone ?? weakestRaw.joint ?? weakestRaw.label;
    if (rawName) {
      const label = String(rawName)
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
      const weakestScore = normalizeScore(typeof weakestRaw === "object" ? weakestRaw.similarity ?? weakestRaw.score : null);
      state.remoteLearning = {
        ...(state.remoteLearning || {}),
        weakest: {
          label,
          detail: weakestScore == null ? "Agent-selected attention joint" : `${Math.round(weakestScore * 100)}% aligned · server diagnosis`,
        },
      };
      normalizedWeakest = { raw: String(rawName), label, score: weakestScore };
    }
  }

  const memoryObject = nested.memory && typeof nested.memory === "object" ? nested.memory : {};
  const memoryEvents = Array.isArray(nested.session_memory)
    ? nested.session_memory
    : Array.isArray(memoryObject.events)
      ? memoryObject.events
      : Array.isArray(backendState.memory)
        ? backendState.memory
        : [];
  const memoryCount = Number(nested.memory_count ?? memoryObject.signal_count ?? backendState.memory_count);
  const jointEma = nested.joint_ema ?? memoryObject.joint_ema ?? {};
  const remoteMemories = [];
  if (normalizedWeakest) {
    const rollingScore = normalizeScore(jointEma[normalizedWeakest.raw] ?? normalizedWeakest.score);
    if (rollingScore != null && state.remoteLearning?.weakest) {
      state.remoteLearning.weakest.detail = `${Math.round(rollingScore * 100)}% rolling alignment · server diagnosis`;
    }
    remoteMemories.push({
      title: `${normalizedWeakest.label} is the current weak point`,
      detail: Number.isFinite(memoryCount) ? `${memoryCount} observed frame signals · rolling pattern` : "Rolling pose pattern",
      score: rollingScore == null ? "tracked" : `${Math.round(rollingScore * 100)}%`,
    });
  }
  memoryEvents.slice(-2).forEach((event, index) => {
    if (typeof event === "string") {
      remoteMemories.push({ title: event, detail: "Server session memory", score: "saved" });
      return;
    }
    const loop = event.loop ?? event.loop_id ?? index + 1;
    remoteMemories.push({
      title: event.title ?? `Loop ${loop} updated the coaching policy`,
      detail: event.detail ?? event.reason ?? event.event ?? (event.qualified ? "Mastery gate passed" : "Agent retained the current speed"),
      score: event.score ?? (event.policy_version ? `v${event.policy_version}` : "saved"),
    });
  });
  if (remoteMemories.length || Number.isFinite(memoryCount)) {
    state.memories = remoteMemories.slice(-3);
    state.remoteLearning = {
      ...(state.remoteLearning || {}),
      memories: state.memories,
      memoryCount: Number.isFinite(memoryCount) ? memoryCount : state.memories.length,
    };
    renderMemories();
  }

  const latency = Number(nested.latency_ms ?? nested.inference_ms);
  if (Number.isFinite(latency)) elements.latencyLabel.textContent = `Pose engine · ${Math.round(latency)} ms`;
  else if (source === "ws" && state.lastSocketSentAt) elements.latencyLabel.textContent = `Round trip · ${Math.round(performance.now() - state.lastSocketSentAt)} ms`;
}

async function fetchJson(path, options = {}, timeoutMs = 2400) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_ORIGIN}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", Accept: "application/json", ...(options.headers || {}) },
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    const text = await response.text();
    return text ? JSON.parse(text) : {};
  } finally {
    window.clearTimeout(timeout);
  }
}

async function ensureSession(routineUrl = elements.routineUrl.value.trim()) {
  if (state.sessionId) return state.sessionId;
  if (state.sessionRequest) return state.sessionRequest;
  const localId = `local-${Date.now().toString(36)}`;
  state.sessionRequest = fetchJson("/api/sessions", {
    method: "POST",
    body: JSON.stringify({
      routine_url: routineUrl || null,
      mode: state.mode,
      focus: FOCUS,
      privacy: { store_frames: false, memory_scope: "session" },
      client: "tempodance-static-spa",
    }),
  })
    .then((payload) => {
      const nested = payload?.data ?? payload?.session ?? payload;
      state.sessionId = nested.session_id ?? nested.id ?? payload.session_id ?? payload.id ?? localId;
      state.remoteSession = state.sessionId !== localId;
      applyBackendPayload(payload);
      setConnection(state.remoteSession ? "connected" : "demo");
      return state.sessionId;
    })
    .catch(() => {
      state.sessionId = localId;
      state.remoteSession = false;
      setConnection("demo");
      return localId;
    })
    .finally(() => { state.sessionRequest = null; });
  return state.sessionRequest;
}

async function postObservation() {
  if (!state.remoteSession || !state.sessionId || !Number.isFinite(state.score) || state.observationInFlight) return;
  state.observationInFlight = true;
  const payload = {
    mode: state.mode,
    count: state.currentCount,
    speed: SPEEDS[state.speedIndex],
    focus: FOCUS,
    score: state.score,
    bone_scores: state.boneScores,
    reference_keypoints: state.latestReference,
    user_keypoints: state.latestLive,
    timing_offset_ms: state.timingOffset,
    loop_id: state.completedLoops + 1,
    loop_progress: state.phase,
    frame_index: Math.floor(state.elapsedPlayingMs / 150),
    ephemeral: true,
  };
  try {
    const response = await fetchJson(`/api/sessions/${encodeURIComponent(state.sessionId)}/observe`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, 1100);
    applyBackendPayload(response);
  } catch {
    // Observation is additive. Local coaching remains fully functional if it fails.
  } finally {
    state.observationInFlight = false;
  }
}

function connectSocket() {
  if (state.socket && [WebSocket.OPEN, WebSocket.CONNECTING].includes(state.socket.readyState)) return;
  setConnection("connecting");
  try {
    const socket = new WebSocket(`${WS_ORIGIN}/ws/pose`);
    state.socket = socket;
    socket.addEventListener("open", () => {
      state.socketReady = true;
      state.socketReconnects = 0;
      setConnection("connected");
      elements.liveBadge.innerHTML = "<i></i> Pose live";
    });
    socket.addEventListener("message", (event) => {
      try {
        applyBackendPayload(JSON.parse(event.data), "ws");
      } catch {
        // Ignore malformed optional telemetry; the next frame can recover.
      }
    });
    socket.addEventListener("close", () => {
      state.socketReady = false;
      if (state.mode !== "camera" || !state.cameraReady) return;
      setConnection("error");
      if (state.socketReconnects < 2) {
        state.socketReconnects += 1;
        window.setTimeout(connectSocket, 750 * state.socketReconnects);
      } else {
        showBanner("Pose service is offline. This interface does not save the frame; switch to Demo mode for the full coaching flow.");
      }
    });
    socket.addEventListener("error", () => {
      state.socketReady = false;
    });
  } catch {
    setConnection("error");
  }
}

function sendCameraFrame(now) {
  if (!state.cameraReady || !state.socketReady || !state.playing || now - state.lastSocketSentAt < 185) return;
  if (state.socket.bufferedAmount > 350_000) return;
  const video = elements.cameraVideo;
  if (!video.videoWidth || !video.videoHeight) return;
  const canvas = elements.captureCanvas;
  const targetWidth = 480;
  const targetHeight = Math.round(targetWidth * video.videoHeight / video.videoWidth);
  canvas.width = targetWidth;
  canvas.height = targetHeight;
  const ctx = canvas.getContext("2d", { alpha: false });
  ctx.drawImage(video, 0, 0, targetWidth, targetHeight);
  const image = canvas.toDataURL("image/jpeg", .68);
  const message = {
    image,
    reference_keypoints: state.latestReference,
    focus: FOCUS,
    session_id: state.sessionId,
  };
  state.lastSocketSentAt = now;
  try {
    state.socket.send(JSON.stringify(message));
  } catch {
    // A close event handles recovery.
  }
}

function setConnection(kind) {
  elements.connectionDot.className = "connection-dot";
  if (kind === "connecting") {
    elements.connectionDot.classList.add("connecting");
    elements.connectionLabel.textContent = "Connecting pose engine";
  } else if (kind === "connected") {
    elements.connectionLabel.textContent = state.mode === "camera" ? "Pose engine connected" : "Agent session connected";
  } else if (kind === "error") {
    elements.connectionDot.classList.add("error");
    elements.connectionLabel.textContent = "Service unavailable";
  } else {
    elements.connectionLabel.textContent = "Demo engine ready";
  }
}

async function analyzeRoutine() {
  if (state.analyzing) return;
  const url = elements.routineUrl.value.trim();
  try {
    const parsed = new URL(url);
    if (!/^https?:$/.test(parsed.protocol)) throw new Error();
  } catch {
    showBanner("Paste a valid http(s) video URL. The built-in 8-count remains ready for Demo mode.");
    elements.routineUrl.focus();
    return;
  }

  state.analyzing = true;
  state.sessionId = null;
  state.remoteSession = false;
  elements.analyzeButton.classList.add("loading");
  elements.analyzeButton.disabled = true;
  elements.referenceLoading.hidden = false;
  elements.analyzeButton.querySelector(".button-label").textContent = "Preparing";
  setConnection("connecting");
  pausePractice();

  const started = performance.now();
  await ensureSession(url);
  const remaining = 950 - (performance.now() - started);
  if (remaining > 0) await new Promise((resolve) => window.setTimeout(resolve, remaining));

  let hostname = "Imported video";
  try { hostname = new URL(url).hostname.replace(/^www\./, ""); } catch { /* validated above */ }
  elements.routineName.textContent = `${hostname} noted · built-in 8-count`;
  elements.routineBpm.textContent = "112";
  elements.referenceLoading.hidden = true;
  elements.analyzeButton.classList.remove("loading");
  elements.analyzeButton.disabled = false;
  elements.analyzeButton.querySelector(".button-label").textContent = "Prepared";
  state.analyzing = false;
  toast(state.remoteSession ? "Practice session linked · built-in reference loaded" : "Built-in practice loop ready · backend optional");
  if (!state.remoteSession) showBanner("Backend did not answer, so the deterministic browser demo took over. Every pitch interaction still works.");
}

async function setMode(mode) {
  if (mode === state.mode) return;
  pausePractice();
  state.mode = mode;
  if (mode === "demo" && state.cameraStream) stopCamera();
  state.serverPose = null;
  state.latestLive = null;
  state.score = null;
  state.boneScores = {};
  updateScoreUI();
  elements.demoModeButton.classList.toggle("active", mode === "demo");
  elements.demoModeButton.setAttribute("aria-pressed", String(mode === "demo"));
  elements.cameraModeButton.classList.toggle("active", mode === "camera");
  elements.cameraModeButton.setAttribute("aria-pressed", String(mode === "camera"));
  elements.cameraEmpty.hidden = mode !== "camera" || state.cameraReady;
  elements.cameraError.hidden = true;
  elements.cameraVideo.hidden = mode !== "camera" || !state.cameraReady;
  elements.livePanelTitle.textContent = mode === "demo" ? "Deterministic dancer" : "Your movement";
  elements.liveBadge.innerHTML = mode === "demo" ? "<i></i> Ready" : "<i></i> Camera off";
  elements.latencyLabel.textContent = mode === "demo" ? "Local simulation · 0 ms" : "Waiting for camera";
  elements.timingMetric.textContent = "--";
  elements.timingDelta.textContent = mode === "demo" ? "Demo timing is scripted" : "Timing analysis not implemented";
  setConnection(mode === "demo" ? "demo" : "connecting");
  if (mode === "camera" && state.cameraReady) connectSocket();
}

async function enableCamera() {
  elements.cameraEmpty.hidden = true;
  elements.cameraError.hidden = true;
  elements.liveBadge.innerHTML = "<i></i> Requesting";
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error("This browser does not expose camera access.");
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 960 }, height: { ideal: 720 } },
      audio: false,
    });
    state.cameraStream = stream;
    state.cameraReady = true;
    elements.cameraVideo.srcObject = stream;
    await elements.cameraVideo.play();
    elements.cameraVideo.hidden = false;
    elements.liveBadge.innerHTML = "<i></i> Camera ready";
    elements.latencyLabel.textContent = "Camera active · not recording";
    await ensureSession();
    connectSocket();
    toast("Camera enabled · frames remain ephemeral");
  } catch (error) {
    state.cameraReady = false;
    elements.cameraError.hidden = false;
    elements.cameraErrorText.textContent = error?.name === "NotAllowedError"
      ? "Camera permission was declined. You can change it in browser settings or use the full Demo mode."
      : `${error?.message || "Camera could not start."} Demo mode remains available.`;
    elements.liveBadge.innerHTML = "<i></i> Unavailable";
    setConnection("error");
  }
}

function stopCamera() {
  state.cameraStream?.getTracks().forEach((track) => track.stop());
  state.cameraStream = null;
  state.cameraReady = false;
  elements.cameraVideo.srcObject = null;
  elements.cameraVideo.hidden = true;
  if (state.socket) state.socket.close(1000, "Session ended");
  state.socket = null;
  state.socketReady = false;
}

async function startPractice() {
  if (state.analyzing) return;
  if (state.mode === "camera" && !state.cameraReady) {
    await enableCamera();
    if (!state.cameraReady) return;
  }
  ensureSession();
  state.playing = true;
  state.sessionStartedAt ??= Date.now();
  state.lastFrameAt = performance.now();
  elements.playButton.classList.add("playing");
  elements.playButton.setAttribute("aria-label", "Pause practice");
  elements.transportTitle.textContent = `Loop ${state.completedLoops + 1} · count ${state.currentCount}`;
  elements.transportHint.textContent = "Hold the shape through each beat; the coach watches consistency.";
  if (state.mode === "camera") connectSocket();
}

function pausePractice() {
  state.playing = false;
  elements.playButton.classList.remove("playing");
  elements.playButton.setAttribute("aria-label", "Start practice");
  if (Number.isFinite(state.score)) {
    elements.transportTitle.textContent = `Paused on count ${state.currentCount}`;
    elements.transportHint.textContent = "Your visible session state is held until you resume or end this run.";
  }
}

function resetSession({ keepMode = true } = {}) {
  pausePractice();
  stopCamera();
  Object.assign(state, {
    mode: keepMode ? state.mode : "demo",
    phase: 0,
    currentCount: 1,
    completedLoops: 0,
    cleanLoops: 0,
    loopMinimum: 1,
    elapsedPlayingMs: 0,
    sessionStartedAt: null,
    sessionId: null,
    remoteSession: false,
    score: null,
    boneScores: {},
    latestLive: null,
    serverPose: null,
    timingOffset: null,
    chartScores: [],
    memories: [],
    policyVersion: 1,
    remoteCoaching: null,
    remoteLearning: null,
    observationInFlight: false,
    speedIndex: 0,
  });
  elements.cleanLoops.textContent = "0";
  elements.sessionClock.textContent = "00:00";
  elements.timingMetric.textContent = "--";
  elements.timingDelta.textContent = "Demo timing is scripted";
  elements.attentionMetric.textContent = "None yet";
  elements.attentionDelta.textContent = "Full-body scan";
  elements.transportTitle.textContent = "Ready for your first loop";
  elements.transportHint.textContent = "Press play — the coach will adapt after each pass.";
  elements.coachMessage.textContent = "Start a loop and I’ll find the smallest correction with the biggest impact.";
  elements.messageConfidence.textContent = "calibrating";
  elements.coachCue.hidden = true;
  elements.policyVersion.textContent = "Policy v1.0";
  elements.policyRule.innerHTML = "<b>Baseline:</b> scan full body equally.";
  elements.chartLine.setAttribute("d", "");
  elements.chartArea.setAttribute("d", "");
  renderMemories();
  updateSpeedUI();
  updateScoreUI();
  updateCountUI();
  if (!keepMode) {
    elements.demoModeButton.classList.add("active");
    elements.demoModeButton.setAttribute("aria-pressed", "true");
    elements.cameraModeButton.classList.remove("active");
    elements.cameraModeButton.setAttribute("aria-pressed", "false");
    elements.cameraEmpty.hidden = true;
    elements.cameraError.hidden = true;
    elements.livePanelTitle.textContent = "Deterministic dancer";
    elements.liveBadge.innerHTML = "<i></i> Ready";
    elements.latencyLabel.textContent = "Local simulation · 0 ms";
  }
  setConnection("demo");
  if (state.mode === "camera") setMode("demo");
}

function showBanner(message) {
  elements.statusBannerText.textContent = message;
  elements.statusBanner.hidden = false;
}

function toast(message, type = "success") {
  const item = document.createElement("div");
  item.className = `toast ${type === "error" ? "error" : ""}`;
  const dot = document.createElement("i");
  const text = document.createElement("span");
  text.textContent = message;
  item.append(dot, text);
  elements.toastRegion.append(item);
  window.setTimeout(() => item.remove(), 3600);
}

function tick(now) {
  const delta = Math.min(now - state.lastFrameAt, 100);
  state.lastFrameAt = now;

  if (state.playing) {
    state.elapsedPlayingMs += delta;
    const speed = SPEEDS[state.speedIndex];
    const loopDuration = (BASE_BEAT_MS * 8) / speed;
    const previousPhase = state.phase;
    state.phase = (state.phase + delta / loopDuration) % 1;
    if (state.phase < previousPhase) handleCompletedLoop();
    state.currentCount = Math.min(8, Math.floor(state.phase * 8) + 1);
    state.loopMinimum = Math.min(state.loopMinimum, state.score ?? 1);
    elements.transportTitle.textContent = `Loop ${state.completedLoops + 1} · count ${state.currentCount}`;
    elements.sessionClock.textContent = formatTime(state.elapsedPlayingMs);
  }

  state.latestReference = getReferencePose(state.phase);
  const trailReference = getReferencePose((state.phase - .035 + 1) % 1);
  renderSkeleton(elements.referenceCanvas, state.latestReference, { primary: "#a98aff", trailPose: trailReference });

  if (state.mode === "demo") {
    state.latestLive = createDemoPose(state.latestReference, now);
    const learningPenalty = state.playing ? lerp(.075, .008, clamp(state.elapsedPlayingMs / 7000)) : .075;
    const result = calculatePoseScore(state.latestLive, state.latestReference, learningPenalty);
    state.score = state.playing ? result.score : state.score;
    state.boneScores = result.boneScores;
    renderSkeleton(elements.liveCanvas, state.latestLive, {
      primary: "#b7ff5a",
      feedback: true,
      boneScores: state.boneScores,
      trailPose: createDemoPose(getReferencePose((state.phase - .035 + 1) % 1), now - 35),
    });
  } else if (state.serverPose) {
    state.latestLive = state.serverPose;
    if (!Number.isFinite(state.score) || !Object.keys(state.boneScores).length) {
      const localResult = calculatePoseScore(state.serverPose, state.latestReference);
      state.score = localResult.score;
      state.boneScores = localResult.boneScores;
    }
    renderSkeleton(elements.liveCanvas, state.serverPose, { primary: "#b7ff5a", feedback: true, boneScores: state.boneScores });
  } else {
    clearCanvas(elements.liveCanvas);
  }

  updateCountUI();
  updateScoreUI();
  updateTimingUI(now);
  updateAgentUI();
  updateChart(now);

  if (state.playing && now - state.lastObservationAt > 150) {
    state.lastObservationAt = now;
    postObservation();
  }
  if (state.mode === "camera") sendCameraFrame(now);
  requestAnimationFrame(tick);
}

function initialize() {
  const markers = $("#countMarkers");
  for (let index = 1; index <= 8; index += 1) {
    const marker = document.createElement("i");
    marker.className = "count-marker";
    marker.dataset.count = index;
    markers.append(marker);
  }

  elements.playButton.addEventListener("click", () => state.playing ? pausePractice() : startPractice());
  elements.analyzeButton.addEventListener("click", analyzeRoutine);
  elements.routineUrl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") analyzeRoutine();
  });
  elements.demoModeButton.addEventListener("click", () => setMode("demo"));
  elements.cameraModeButton.addEventListener("click", () => setMode("camera"));
  elements.enableCameraButton.addEventListener("click", enableCamera);
  elements.useDemoFallbackButton.addEventListener("click", () => setMode("demo"));
  $$(".speed-tier").forEach((button, index) => {
    button.addEventListener("click", () => {
      const wasHigher = index > state.speedIndex;
      state.speedIndex = index;
      state.cleanLoops = 0;
      elements.cleanLoops.textContent = "0";
      updateSpeedUI();
      toast(wasHigher ? `Manual control · speed set to ${SPEEDS[index].toFixed(1)}×` : `Coach speed set to ${SPEEDS[index].toFixed(1)}×`);
    });
  });
  $("#privacyButton").addEventListener("click", () => {
    if (typeof elements.privacyDialog.showModal === "function") elements.privacyDialog.showModal();
    else elements.privacyDialog.setAttribute("open", "");
  });
  $("#endSessionButton").addEventListener("click", () => {
    resetSession({ keepMode: false });
    toast("Browser session cleared · camera and connection closed; server memory lasts until restart");
  });
  $("#dismissBanner").addEventListener("click", () => { elements.statusBanner.hidden = true; });
  window.addEventListener("beforeunload", stopCamera);
  window.addEventListener("resize", () => {
    // Canvas dimensions are refreshed by the next animation frame.
  }, { passive: true });

  renderMemories();
  updateCountUI();
  requestAnimationFrame(tick);
}

initialize();
