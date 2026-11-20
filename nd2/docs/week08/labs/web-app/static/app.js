// RobotOS Edge AI Studio - Industrial SCADA Dashboard Frontend

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const wsStatusBadge = document.getElementById("wsStatusBadge");
  const footerWsStatus = document.getElementById("footerWsStatus");
  const headerThresholdBadge = document.getElementById("headerThresholdBadge");
  const threshDisplay = document.getElementById("threshDisplay");
  const thresholdSlider = document.getElementById("thresholdSlider");
  const presetLow = document.getElementById("presetLow");
  const presetRelaxed = document.getElementById("presetRelaxed");
  const presetBalanced = document.getElementById("presetBalanced");
  const presetStrict = document.getElementById("presetStrict");

  // Voice Interaction Controller Elements
  const pttButton = document.getElementById("pttButton");
  const pttPulseHalo = document.getElementById("pttPulseHalo");
  const pttIcon = document.getElementById("pttIcon");
  const pttText = document.getElementById("pttText");
  const continuousToggleBtn = document.getElementById("continuousToggleBtn");
  const continuousStatusDot = document.getElementById("continuousStatusDot");
  const continuousToggleText = document.getElementById("continuousToggleText");
  const liveDbfsText = document.getElementById("liveDbfsText");
  const liveVuBar = document.getElementById("liveVuBar");
  const activeStreamBadge = document.getElementById("activeStreamBadge");
  const activeStreamDot = document.getElementById("activeStreamDot");
  const activeStreamLabel = document.getElementById("activeStreamLabel");
  const enableMicBtn = document.getElementById("enableMicBtn");

  const stateBanner = document.getElementById("stateBanner");
  const stateIcon = document.getElementById("stateIcon");
  const stateTitle = document.getElementById("stateTitle");
  const stateDesc = document.getElementById("stateDesc");
  const lastTriggerTime = document.getElementById("lastTriggerTime");
  const eventLog = document.getElementById("eventLog");
  const clearLogBtn = document.getElementById("clearLogBtn");
  const probBarsContainer = document.getElementById("probBarsContainer");
  const uploadForm = document.getElementById("uploadForm");
  const audioFileInput = document.getElementById("audioFileInput");
  const restResult = document.getElementById("restResult");
  const useSampleBtn = document.getElementById("useSampleBtn");
  const recordBrowserMicBtn = document.getElementById("recordBrowserMicBtn");
  const recordMicIcon = document.getElementById("recordMicIcon");
  const recordMicText = document.getElementById("recordMicText");
  const audioDbfsMeter = document.getElementById("audioDbfsMeter");
  const audioCanvas = document.getElementById("audioVisualizer");

  // Terminal Tabs
  const tabBtnWs = document.getElementById("tabBtnWs");
  const tabBtnRest = document.getElementById("tabBtnRest");
  const tabBtnThresh = document.getElementById("tabBtnThresh");
  const tabBtnCurl = document.getElementById("tabBtnCurl");

  const DEFAULT_LABELS = ["red", "green", "blue", "off", "_silence_", "_unknown_"];
  let knownLabels = [...DEFAULT_LABELS];
  let currentThreshold = 0.80;
  let modelMetaData = null;
  let lastRestPayload = null;

  // Real Web Audio API Nodes & Analyzer State
  let audioCtx = null;
  let micMediaStream = null;
  let micSourceNode = null;
  let analyserNode = null;
  let audioProcessor = null;
  let freqDataArray = null;
  let timeDataArray = null;

  let isAudioStreaming = false;  // Whether actively transmitting chunks to server
  let isContinuousMode = false;  // Whether in continuous hands-free streaming
  let isPttActive = false;       // Whether PTT button / spacebar is held

  // 1. Initialize Probability Meters with Industrial Styling & Threshold Marker
  function initProbBars(labels) {
    probBarsContainer.innerHTML = "";
    const threshPct = Math.round(currentThreshold * 100);

    labels.forEach((label) => {
      const colorClass =
        label === "red" ? "bg-red-500" :
        label === "green" ? "bg-emerald-500" :
        label === "blue" ? "bg-sky-500" :
        label === "off" ? "bg-slate-400" :
        label === "_silence_" ? "bg-amber-600" : "bg-purple-600";

      const badgeColor =
        label === "red" ? "text-red-400" :
        label === "green" ? "text-emerald-400" :
        label === "blue" ? "text-sky-400" :
        label === "off" ? "text-slate-300" : "text-slate-500";

      const row = document.createElement("div");
      row.className = "space-y-1.5 font-mono";
      row.innerHTML = `
        <div class="flex justify-between text-xs items-center">
          <span class="font-bold tracking-wider ${badgeColor}">${label}</span>
          <span id="prob-val-${label}" class="text-slate-300 font-bold">0.0%</span>
        </div>
        <div class="w-full bg-[#0a0e16] rounded-md h-3.5 relative overflow-hidden border border-[#232e42] p-[1px]">
          <!-- Dynamic Softmax Bar -->
          <div id="prob-bar-${label}" class="h-full rounded-sm ${colorClass} transition-all duration-150" style="width: 0%"></div>
          <!-- Threshold Marker Vertical Line -->
          <div class="threshold-marker" id="threshMarker-${label}" style="left: ${threshPct}%" title="Threshold: ${threshPct}%"></div>
        </div>
      `;
      probBarsContainer.appendChild(row);
    });
  }
  initProbBars(knownLabels);

  // 2. Threshold Dynamic Controller
  function updateThresholdUI(val) {
    currentThreshold = parseFloat(val);
    const pct = Math.round(currentThreshold * 100);
    if (threshDisplay) threshDisplay.textContent = `${currentThreshold.toFixed(2)} (${pct}%)`;
    if (headerThresholdBadge) headerThresholdBadge.textContent = `${pct}%`;
    if (thresholdSlider) thresholdSlider.value = currentThreshold;

    // Update threshold markers on all probability bars
    knownLabels.forEach((label) => {
      const marker = document.getElementById(`threshMarker-${label}`);
      if (marker) {
        marker.style.left = `${pct}%`;
        marker.title = `Threshold: ${pct}%`;
      }
    });

    // Update preset button highlights
    if (presetLow && presetRelaxed && presetBalanced && presetStrict) {
      const activeClass = "py-1 px-1 rounded bg-sky-950/50 border border-sky-500/40 text-[10px] font-mono text-sky-300 font-bold text-center";
      const inactiveClass = "py-1 px-1 rounded bg-[#182335] hover:bg-[#22314a] border border-[#273852] text-[10px] font-mono text-slate-300 text-center";

      presetLow.className = Math.abs(currentThreshold - 0.10) < 0.03 ? activeClass : inactiveClass;
      presetRelaxed.className = Math.abs(currentThreshold - 0.50) < 0.05 ? activeClass : inactiveClass;
      presetBalanced.className = Math.abs(currentThreshold - 0.80) < 0.03 ? activeClass : inactiveClass;
      presetStrict.className = Math.abs(currentThreshold - 0.95) < 0.03 ? activeClass : inactiveClass;
    }
  }

  let thresholdDebounceTimer = null;
  async function pushThresholdToServer(val) {
    try {
      const res = await fetch("/api/v1/model/threshold", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ threshold: parseFloat(val) }),
      });
      const data = await res.json();
      addLogEntry("THRESH", `Threshold updated to ${data.threshold} (${Math.round(data.threshold * 100)}%)`);
    } catch (err) {
      console.error("Failed to update threshold:", err);
    }
  }

  if (thresholdSlider) {
    thresholdSlider.addEventListener("input", (e) => {
      const val = e.target.value;
      updateThresholdUI(val);
      clearTimeout(thresholdDebounceTimer);
      thresholdDebounceTimer = setTimeout(() => pushThresholdToServer(val), 250);
    });
  }

  if (presetLow) {
    presetLow.addEventListener("click", () => {
      updateThresholdUI(0.10);
      pushThresholdToServer(0.10);
    });
  }
  if (presetRelaxed) {
    presetRelaxed.addEventListener("click", () => {
      updateThresholdUI(0.50);
      pushThresholdToServer(0.50);
    });
  }
  if (presetBalanced) {
    presetBalanced.addEventListener("click", () => {
      updateThresholdUI(0.80);
      pushThresholdToServer(0.80);
    });
  }
  if (presetStrict) {
    presetStrict.addEventListener("click", () => {
      updateThresholdUI(0.95);
      pushThresholdToServer(0.95);
    });
  }

  // 3. Connect to WebSocket Stream
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/kws`;
  let socket = null;

  function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      wsStatusBadge.className =
        "inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25";
      wsStatusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> LIVE WS (16kHz)';
      if (footerWsStatus) footerWsStatus.textContent = "WS: Connected (16kHz)";
      addLogEntry("SYSTEM", "WebSocket channel opened. Real-time edge stream active.");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === "connected") {
          if (data.labels && data.labels.length > 0) {
            knownLabels = data.labels;
            initProbBars(knownLabels);
          }
          if (data.threshold) {
            updateThresholdUI(data.threshold);
          }
        } else if (data.event === "live_stream_update") {
          // CONTINUOUS STREAMING UPDATE: Softmax bars!
          handleLiveStreamUpdate(data);
        } else if (data.event === "keyword_detected") {
          handleKeywordDetected(data.keyword, data.confidence, data.timestamp, data.source || "mic");
        } else if (data.event === "threshold_updated") {
          updateThresholdUI(data.threshold);
        }
      } catch (err) {
        console.error("Failed to parse WS message:", err);
      }
    };

    socket.onclose = () => {
      wsStatusBadge.className =
        "inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/25";
      wsStatusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span> Reconnecting...';
      if (footerWsStatus) footerWsStatus.textContent = "WS: Disconnected";
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      socket.close();
    };
  }
  connectWebSocket();

  // 4. Real-Time Audio Downsampling Utility
  function downsampleToInt16(float32Array, inRate, outRate = 16000) {
    if (inRate === outRate) {
      const pcm16 = new Int16Array(float32Array.length);
      for (let i = 0; i < float32Array.length; i++) {
        const s = Math.max(-1, Math.min(1, float32Array[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      return pcm16;
    }
    const ratio = inRate / outRate;
    const newLen = Math.round(float32Array.length / ratio);
    const pcm16 = new Int16Array(newLen);
    for (let i = 0; i < newLen; i++) {
      const orig = i * ratio;
      const i1 = Math.floor(orig);
      const i2 = Math.min(i1 + 1, float32Array.length - 1);
      const frac = orig - i1;
      const s = Math.max(-1, Math.min(1, float32Array[i1] * (1 - frac) + float32Array[i2] * frac));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return pcm16;
  }

  // 5. Initialize Live Web Audio Context & FFT Analyser
  async function initMicrophoneMonitor() {
    if (micSourceNode && analyserNode) return true;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      micMediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      micSourceNode = audioCtx.createMediaStreamSource(micMediaStream);

      // Create Real-Time AnalyserNode for live spectrum & waveform
      analyserNode = audioCtx.createAnalyser();
      analyserNode.fftSize = 256;
      analyserNode.smoothingTimeConstant = 0.70;
      micSourceNode.connect(analyserNode);

      freqDataArray = new Uint8Array(analyserNode.frequencyBinCount);
      timeDataArray = new Uint8Array(analyserNode.fftSize);

      // Create ScriptProcessorNode for streaming audio chunks to WebSocket server
      audioProcessor = audioCtx.createScriptProcessor(2048, 1, 1);
      audioProcessor.onaudioprocess = (e) => {
        if (!isAudioStreaming || !socket || socket.readyState !== WebSocket.OPEN) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const pcm16 = downsampleToInt16(inputData, audioCtx.sampleRate, 16000);
        if (pcm16 && pcm16.length > 0) {
          socket.send(pcm16.buffer);
        }
      };
      micSourceNode.connect(audioProcessor);
      audioProcessor.connect(audioCtx.destination);

      if (enableMicBtn) {
        enableMicBtn.className = "px-2.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 font-mono text-[11px] font-bold cursor-default";
        enableMicBtn.innerHTML = "✓ Live FFT Mic Connected";
      }
      addLogEntry("SYSTEM", "Live Web Audio Analyser initialized. Spectrum & dBFS meter active.");
      return true;
    } catch (err) {
      console.error("Microphone initialization error:", err);
      alert("Microphone permission required for spectrum and voice recognition: " + err.message);
      return false;
    }
  }

  if (enableMicBtn) {
    enableMicBtn.addEventListener("click", () => {
      initMicrophoneMonitor();
    });
  }
  if (audioCanvas) {
    audioCanvas.addEventListener("click", () => {
      initMicrophoneMonitor();
    });
  }

  // 6. Voice Stream Transmit UI Controllers
  function setVoiceStreamActiveUI(active) {
    if (active) {
      if (activeStreamBadge) {
        activeStreamBadge.className = "hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/50 border border-emerald-500/50 font-mono text-xs text-emerald-300";
        activeStreamDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse";
        activeStreamLabel.textContent = "Stream: Transmitting (16 kHz)";
      }
    } else {
      if (activeStreamBadge) {
        activeStreamBadge.className = "hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#141d2c] border border-[#26374f] font-mono text-xs text-slate-300";
        activeStreamDot.className = "w-2 h-2 rounded-full bg-slate-500";
        activeStreamLabel.textContent = "Stream: Idle (Monitoring)";
      }
    }
  }

  // 7. Push-to-Talk (PTT) Event Handlers
  async function activatePtt() {
    if (isContinuousMode || isPttActive) return;
    const ok = await initMicrophoneMonitor();
    if (!ok) return;

    isPttActive = true;
    isAudioStreaming = true;
    pttButton.className = "relative select-none flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-mono font-bold text-xs sm:text-sm text-white shadow-2xl transition-all bg-gradient-to-r from-red-600 to-rose-600 border border-red-400 scale-105";
    pttPulseHalo.className = "absolute -inset-1 rounded-xl bg-red-500/50 opacity-100 transition duration-150 blur-md pointer-events-none";
    pttIcon.textContent = "🔴";
    pttText.textContent = "TRANSMITTING (SPEAK)";
    setVoiceStreamActiveUI(true);
  }

  function deactivatePtt() {
    if (isContinuousMode || !isPttActive) return;
    isPttActive = false;
    isAudioStreaming = false;
    pttButton.className = "relative select-none flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-mono font-bold text-xs sm:text-sm text-white shadow-lg transition-all bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-500 hover:to-sky-500 active:scale-95 border border-sky-400/40 cursor-pointer";
    pttPulseHalo.className = "absolute -inset-1 rounded-xl bg-sky-500/30 opacity-0 transition duration-200 blur-sm pointer-events-none";
    pttIcon.textContent = "🎙️";
    pttText.textContent = "HOLD TO TALK";
    setVoiceStreamActiveUI(false);
  }

  if (pttButton) {
    // Mouse / Touch hold
    pttButton.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      activatePtt();
    });
    window.addEventListener("pointerup", () => deactivatePtt());
    window.addEventListener("pointercancel", () => deactivatePtt());

    // Keyboard Spacebar Push-To-Talk
    window.addEventListener("keydown", (e) => {
      if (e.code === "Space" && e.target === document.body && !isPttActive && !isContinuousMode) {
        e.preventDefault();
        activatePtt();
      }
    });
    window.addEventListener("keyup", (e) => {
      if (e.code === "Space" && isPttActive && !isContinuousMode) {
        e.preventDefault();
        deactivatePtt();
      }
    });
  }

  // 8. Continuous Speech Stream Toggle Handler
  if (continuousToggleBtn) {
    continuousToggleBtn.addEventListener("click", async () => {
      if (!isContinuousMode) {
        const ok = await initMicrophoneMonitor();
        if (!ok) return;

        isContinuousMode = true;
        isAudioStreaming = true;
        continuousToggleBtn.className = "flex items-center gap-2.5 px-4 py-3.5 rounded-xl font-mono text-xs font-bold transition-all border border-emerald-500/50 bg-emerald-950/40 text-emerald-200 cursor-pointer";
        continuousStatusDot.className = "w-3 h-3 rounded-full bg-emerald-400 animate-pulse";
        continuousToggleText.textContent = "Continuous Speech: LIVE";
        if (pttButton) {
          pttButton.classList.add("opacity-50", "pointer-events-none");
        }
        setVoiceStreamActiveUI(true);
        addLogEntry("STREAM", "Continuous speech mode engaged. Listening continuously.");
      } else {
        isContinuousMode = false;
        isAudioStreaming = false;
        continuousToggleBtn.className = "flex items-center gap-2.5 px-4 py-3.5 rounded-xl font-mono text-xs font-bold transition-all border border-[#283852] bg-[#141d2d] text-slate-300 hover:bg-[#1b273d] hover:text-white cursor-pointer";
        continuousStatusDot.className = "w-3 h-3 rounded-full bg-slate-500";
        continuousToggleText.textContent = "Continuous Speech: OFF";
        if (pttButton) {
          pttButton.classList.remove("opacity-50", "pointer-events-none");
        }
        setVoiceStreamActiveUI(false);
      }
    });
  }

  // 9. Live Continuous Streaming Updates from Server
  function handleLiveStreamUpdate(data) {
    // 1. Update live meters for all classes continuously
    if (data.probabilities) {
      Object.entries(data.probabilities).forEach(([lb, p]) => {
        const bar = document.getElementById(`prob-bar-${lb}`);
        const val = document.getElementById(`prob-val-${lb}`);
        if (bar && val) {
          const pct = Math.round(p * 100);
          bar.style.width = `${pct}%`;
          val.textContent = `${pct}%`;

          // Threshold crossing glow
          if (p >= currentThreshold && lb !== "_silence_" && lb !== "_unknown_") {
            bar.classList.add("ring-2", "ring-white", "brightness-125");
          } else {
            bar.classList.remove("ring-2", "ring-white", "brightness-125");
          }
        }
      });
    }

    // 2. Keyword trigger event
    if (data.triggered && data.keyword) {
      handleKeywordDetected(data.keyword, data.confidence, data.timestamp, "live_stream");
    }
  }

  // 10. Handle Keyword Detections & Reactive Industrial State Updates
  function handleKeywordDetected(keyword, confidence, timestamp, source = "mic") {
    const timeStr = new Date().toLocaleTimeString();
    lastTriggerTime.textContent = `Last trigger: ${timeStr} (${confidence >= 0 ? (confidence * 100).toFixed(1) + '%' : ''})`;

    // Reset styles
    stateBanner.className = "p-8 sm:p-10 rounded-2xl border-2 border-[#26334a] bg-[#0e1422]/95 flex flex-col items-center justify-center text-center transition-all duration-300 relative overflow-hidden shadow-2xl";

    const kw = keyword.toLowerCase();
    if (kw === "red") {
      stateBanner.classList.add("glow-red", "hazard-stripes");
      stateIcon.className = "w-24 h-24 rounded-2xl flex items-center justify-center text-5xl font-black mb-4 bg-red-600 text-white shadow-xl scale-105 transition-all";
      stateIcon.textContent = "🛑";
      stateTitle.textContent = "EMERGENCY STOP";
      stateTitle.className = "text-4xl sm:text-5xl font-black tracking-tight text-red-400 font-mono";
      stateDesc.textContent = "Safety Interlock Tripped! All motor outputs disabled (0.0 m/s). Active electromagnetic brake locked.";
    } else if (kw === "green") {
      stateBanner.classList.add("glow-green");
      stateIcon.className = "w-24 h-24 rounded-2xl flex items-center justify-center text-5xl font-black mb-4 bg-emerald-600 text-white shadow-xl scale-105 transition-all";
      stateIcon.textContent = "🚀";
      stateTitle.textContent = "DRIVE FORWARD";
      stateTitle.className = "text-4xl sm:text-5xl font-black tracking-tight text-emerald-400 font-mono";
      stateDesc.textContent = "Patrol Navigation Active. Linear velocity nominal: 0.50 m/s. Obstacle avoidance LiDAR engaged.";
    } else if (kw === "blue") {
      stateBanner.classList.add("glow-blue");
      stateIcon.className = "w-24 h-24 rounded-2xl flex items-center justify-center text-5xl font-black mb-4 bg-sky-600 text-white shadow-xl scale-105 transition-all";
      stateIcon.textContent = "🧭";
      stateTitle.textContent = "MANUAL NAVIGATION";
      stateTitle.className = "text-4xl sm:text-5xl font-black tracking-tight text-sky-400 font-mono";
      stateDesc.textContent = "Waypoint Heading Adjust. Angular velocity: +0.35 rad/s. Operator manual steering active.";
    } else if (kw === "off") {
      stateBanner.classList.add("glow-amber");
      stateIcon.className = "w-24 h-24 rounded-2xl flex items-center justify-center text-5xl font-black mb-4 bg-slate-800 text-slate-300 shadow-xl transition-all";
      stateIcon.textContent = "💤";
      stateTitle.textContent = "SYSTEM STANDBY";
      stateTitle.className = "text-4xl sm:text-5xl font-black tracking-tight text-slate-300 font-mono";
      stateDesc.textContent = "Low-power park mode entered. Sensors idling at 1.0 Hz telemetry heartbeat.";
    }

    const srcTag = source === "simulated" ? "SIM" : source === "live_stream" ? "LIVE" : "MIC";
    addLogEntry(keyword.toUpperCase(), `[${srcTag}] Conf: ${(confidence * 100).toFixed(1)}% | T: ${timestamp}s -> FSM State Triggered`);
  }

  // 11. Append Log Entry to Terminal
  function addLogEntry(tag, msg) {
    if (eventLog.children.length === 1 && eventLog.children[0].classList.contains("italic")) {
      eventLog.innerHTML = "";
    }
    const entry = document.createElement("div");
    entry.className = "p-1.5 rounded bg-[#0e141f] border border-[#1a2333] flex items-center justify-between font-mono text-xs";

    const tagBadge =
      tag === "RED" ? "bg-red-500/20 text-red-400 border border-red-500/30 font-bold" :
      tag === "GREEN" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold" :
      tag === "BLUE" ? "bg-sky-500/20 text-sky-400 border border-sky-500/30 font-bold" :
      tag === "OFF" ? "bg-slate-700/30 text-slate-300 border border-slate-600/30 font-bold" :
      tag === "STREAM" ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-bold" :
      tag === "REST" ? "bg-purple-500/20 text-purple-400 border border-purple-500/30 font-bold" :
      tag === "THRESH" ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold" :
      "bg-slate-800 text-slate-400 border border-slate-700 font-bold";

    entry.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-[11px] text-slate-500">${new Date().toLocaleTimeString()}</span>
        <span class="px-2 py-0.5 rounded text-[11px] ${tagBadge}">[${tag}]</span>
        <span class="text-slate-200">${msg}</span>
      </div>
      <span class="text-[10px] text-slate-600 font-mono">0x${Math.floor(Math.random() * 0xffff).toString(16)}</span>
    `;
    eventLog.insertBefore(entry, eventLog.firstChild);
    while (eventLog.children.length > 50) {
      eventLog.removeChild(eventLog.lastChild);
    }
  }

  clearLogBtn.addEventListener("click", () => {
    eventLog.innerHTML = '<div class="text-slate-500 italic p-1">[system] Telemetry log cleared. Stream listening...</div>';
  });

  // 12. Global Interactive Keyword Simulation Dispatcher
  window.triggerKeywordSim = async function(keyword) {
    try {
      const resp = await fetch("/api/v1/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword: keyword, confidence: 0.96 }),
      });
      const data = await resp.json();
      if (data && data.payload) {
        handleKeywordDetected(data.payload.keyword, data.payload.confidence, data.payload.timestamp, "simulated");
      }
    } catch (err) {
      console.error("Simulation error:", err);
      handleKeywordDetected(keyword, 0.95, 0.0, "simulated");
    }
  };

  // 13. Terminal Panel Tab Switching
  if (tabBtnWs && tabBtnRest && tabBtnThresh && tabBtnCurl) {
    function resetTabs() {
      [tabBtnWs, tabBtnRest, tabBtnThresh, tabBtnCurl].forEach((t) => (t.className = "term-tab"));
    }

    tabBtnWs.addEventListener("click", () => {
      resetTabs();
      tabBtnWs.className = "term-tab active flex items-center gap-2";
    });

    tabBtnRest.addEventListener("click", () => {
      resetTabs();
      tabBtnRest.className = "term-tab active";
      if (lastRestPayload) {
        addLogEntry("REST", `Cached REST Output: Top='${lastRestPayload.top_class}' (${(lastRestPayload.confidence * 100).toFixed(1)}%)`);
      } else {
        addLogEntry("REST", "No REST payload cached yet. Click 'Use Built-in Sample' or 'Record Mic' to test.");
      }
    });

    tabBtnThresh.addEventListener("click", () => {
      resetTabs();
      tabBtnThresh.className = "term-tab active";
      addLogEntry("THRESH", `Active Sensitivity Threshold: ${currentThreshold.toFixed(2)} (${Math.round(currentThreshold * 100)}%)`);
    });

    tabBtnCurl.addEventListener("click", () => {
      resetTabs();
      tabBtnCurl.className = "term-tab active";
      addLogEntry("CURL", 'curl -X POST "http://127.0.0.1:8000/api/v1/classify" -F "file=@sample_audio.wav"');
      addLogEntry("CURL", 'curl -X POST "http://127.0.0.1:8000/api/v1/model/threshold" -H "Content-Type: application/json" -d \'{"threshold": 0.85}\'');
      addLogEntry("CURL", 'curl -X POST "http://127.0.0.1:8000/api/v1/simulate" -H "Content-Type: application/json" -d \'{"keyword": "red", "confidence": 0.98}\'');
    });
  }

  // 14. REST API Audio Dispatcher
  async function sendAudioBlobForClassification(blob, filename = "audio.wav") {
    const formData = new FormData();
    formData.append("file", blob, filename);
    restResult.classList.remove("hidden");
    restResult.innerHTML = '<span class="text-slate-400 font-mono">POST /api/v1/classify &bull; Running DS-CNN int8 inference...</span>';

    try {
      const resp = await fetch("/api/v1/classify", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      lastRestPayload = data;
      restResult.innerHTML = `<pre class="text-emerald-400 font-mono text-xs">${JSON.stringify(data, null, 2)}</pre>`;

      if (data.probabilities) {
        Object.entries(data.probabilities).forEach(([lb, p]) => {
          const bar = document.getElementById(`prob-bar-${lb}`);
          const val = document.getElementById(`prob-val-${lb}`);
          if (bar && val) {
            const pct = Math.round(p * 100);
            bar.style.width = `${pct}%`;
            val.textContent = `${pct}%`;
          }
        });
      }

      addLogEntry("REST", `Classified '${filename}': Top='${data.top_class}' (${(data.confidence * 100).toFixed(1)}%)`);

      if (data.top_class && data.confidence >= currentThreshold) {
        handleKeywordDetected(data.top_class, data.confidence, 0.0, "rest");
      }
    } catch (err) {
      restResult.innerHTML = `<span class="text-red-400 font-mono text-xs">Error: ${err.message}</span>`;
      addLogEntry("ERROR", `REST error: ${err.message}`);
    }
  }

  // 14.1 Built-in Sample Audio Button
  if (useSampleBtn) {
    useSampleBtn.addEventListener("click", async () => {
      restResult.classList.remove("hidden");
      restResult.innerHTML = '<span class="text-slate-400 font-mono">Fetching sample_audio.wav from server...</span>';
      try {
        const res = await fetch("/api/v1/sample-audio");
        if (!res.ok) throw new Error("sample_audio.wav not found on server");
        const blob = await res.blob();
        await sendAudioBlobForClassification(blob, "sample_audio.wav");
      } catch (err) {
        restResult.innerHTML = `<span class="text-red-400 font-mono text-xs">Error: ${err.message}</span>`;
      }
    });
  }

  // 14.2 Single Take Mic Recorder (1s)
  function encodeWav(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    function writeString(offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    }
    writeString(0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, "WAVE");
    writeString(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, "data");
    view.setUint32(40, samples.length * 2, true);
    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      offset += 2;
    }
    return new Blob([buffer], { type: "audio/wav" });
  }

  if (recordBrowserMicBtn) {
    recordBrowserMicBtn.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        recordMicIcon.textContent = "🔴";
        recordMicText.textContent = "Listening... (1s)";
        recordBrowserMicBtn.classList.add("bg-red-950/60", "border-red-500/60");

        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const source = ctx.createMediaStreamSource(stream);
        const proc = ctx.createScriptProcessor(4096, 1, 1);
        const recorded = [];
        const needed = Math.floor(ctx.sampleRate * 1.0);

        proc.onaudioprocess = (e) => {
          const input = e.inputBuffer.getChannelData(0);
          for (let i = 0; i < input.length; i++) {
            recorded.push(input[i]);
            if (recorded.length >= needed) break;
          }
        };

        source.connect(proc);
        proc.connect(ctx.destination);

        setTimeout(async () => {
          proc.disconnect();
          source.disconnect();
          stream.getTracks().forEach((t) => t.stop());

          recordMicIcon.textContent = "🎙️";
          recordMicText.textContent = "Record Browser Mic (1s)";
          recordBrowserMicBtn.classList.remove("bg-red-950/60", "border-red-500/60");

          const rawFloat32 = new Float32Array(recorded);
          const ratio = 16000 / ctx.sampleRate;
          const newLength = Math.round(rawFloat32.length * ratio);
          const resampled = new Float32Array(newLength);
          for (let i = 0; i < newLength; i++) {
            const orig = i / ratio;
            const i1 = Math.floor(orig);
            const i2 = Math.min(i1 + 1, rawFloat32.length - 1);
            const frac = orig - i1;
            resampled[i] = rawFloat32[i1] * (1 - frac) + rawFloat32[i2] * frac;
          }

          const wavBlob = encodeWav(resampled, 16000);
          await sendAudioBlobForClassification(wavBlob, "browser_mic.wav");
        }, 1100);
      } catch (err) {
        alert("Microphone permission denied: " + err.message);
      }
    });
  }

  // 14.3 Custom File Upload Form
  if (uploadForm && audioFileInput) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!audioFileInput.files || audioFileInput.files.length === 0) {
        alert("Please choose a .wav file first");
        return;
      }
      const file = audioFileInput.files[0];
      await sendAudioBlobForClassification(file, file.name);
    });
  }

  // 15. Real-Time 60 FPS Audio Spectrum & Waveform Oscilloscope
  if (audioCanvas) {
    const ctx = audioCanvas.getContext("2d");

    function renderAudioVisualizer() {
      requestAnimationFrame(renderAudioVisualizer);

      const width = audioCanvas.width = audioCanvas.offsetWidth || 500;
      const height = audioCanvas.height = 56;

      ctx.clearRect(0, 0, width, height);

      // 1. Draw Technical Background Grid
      ctx.strokeStyle = "rgba(56, 189, 248, 0.08)";
      ctx.lineWidth = 1;
      for (let x = 0; x < width; x += 32) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 14) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // If Analyser is connected, read REAL microphone audio!
      if (analyserNode && freqDataArray && timeDataArray) {
        analyserNode.getByteFrequencyData(freqDataArray);
        analyserNode.getByteTimeDomainData(timeDataArray);

        // Compute Real Instantaneous Energy (RMS -> dBFS)
        let sumSquares = 0;
        for (let i = 0; i < timeDataArray.length; i++) {
          const norm = (timeDataArray[i] - 128) / 128.0;
          sumSquares += norm * norm;
        }
        const rms = Math.sqrt(sumSquares / timeDataArray.length);
        const dbfs = rms > 1e-4 ? 20 * Math.log10(rms) : -75.0;
        const clampedDbfs = Math.max(-75, Math.min(0, dbfs));

        // Update real-time dBFS readings in header & VU bar
        if (audioDbfsMeter) {
          const statusTag = isAudioStreaming ? "• STREAMING" : "• MONITOR";
          audioDbfsMeter.textContent = `MIC: ${clampedDbfs.toFixed(1)} dBFS ${statusTag}`;
          audioDbfsMeter.className =
            clampedDbfs > -20 ? "text-red-400 font-bold" :
            clampedDbfs > -45 ? "text-amber-400 font-bold" : "text-emerald-400 font-bold";
        }
        if (liveDbfsText) {
          liveDbfsText.textContent = `${clampedDbfs.toFixed(1)} dBFS`;
        }
        if (liveVuBar) {
          const vuPct = Math.max(4, Math.min(100, Math.round(((clampedDbfs + 75) / 75) * 100)));
          liveVuBar.style.width = `${vuPct}%`;
          liveVuBar.className =
            vuPct > 75 ? "h-full rounded-full bg-red-500" :
            vuPct > 45 ? "h-full rounded-full bg-amber-400" : "h-full rounded-full bg-emerald-500";
        }

        // 2. Draw Real Frequency Spectrum Bars (48 Bins across audible frequencies)
        const numBars = 48;
        const barWidth = Math.floor(width / numBars) - 2;
        for (let i = 0; i < numBars; i++) {
          const binIndex = Math.floor(i * (freqDataArray.length / numBars));
          const val = freqDataArray[binIndex] / 255.0; // 0..1 scale
          const barHeight = Math.max(3, val * (height - 8));
          const x = i * (barWidth + 2) + 2;
          const y = height - barHeight - 2;

          // Color coded: Peak (Red) -> Loud (Amber) -> Active Stream (Green) -> Monitor (Cyan)
          if (val > 0.72) {
            ctx.fillStyle = "#ef4444";
          } else if (val > 0.42) {
            ctx.fillStyle = "#f59e0b";
          } else if (isAudioStreaming) {
            ctx.fillStyle = "#10b981";
          } else {
            ctx.fillStyle = "#38bdf8";
          }
          ctx.fillRect(x, y, barWidth, barHeight);
        }

        // 3. Draw Real Time-Domain Waveform Overlay Line
        ctx.lineWidth = 1.8;
        ctx.strokeStyle = isAudioStreaming ? "rgba(16, 185, 129, 0.95)" : "rgba(56, 189, 248, 0.85)";
        ctx.shadowColor = isAudioStreaming ? "#10b981" : "#38bdf8";
        ctx.shadowBlur = 8;
        ctx.beginPath();

        const sliceWidth = width / timeDataArray.length;
        let x = 0;
        for (let i = 0; i < timeDataArray.length; i++) {
          const v = timeDataArray[i] / 128.0;
          const y = (v * height) / 2;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
          x += sliceWidth;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

      } else {
        // Standby prompt before mic permission granted
        ctx.fillStyle = "rgba(148, 163, 184, 0.75)";
        ctx.font = "12px JetBrains Mono, monospace";
        ctx.textAlign = "center";
        ctx.fillText("Microphone Standby. Click 'Enable Mic Monitor' or hold 'HOLD TO TALK' to activate live spectrum.", width / 2, height / 2 + 4);
      }
    }

    renderAudioVisualizer();
  }
});
