// ==========================================================================
// RobotOS Edge AI Studio - Figma-Like UI Frontend Controller (ND02)
// Clean separation of UI state, real-time Web Audio API & WebSocket telemetry
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Navigation & Header
  const wsStatusBadge = document.getElementById("wsStatusBadge");
  const footerWsStatus = document.getElementById("footerWsStatus");
  const headerThresholdBadge = document.getElementById("headerThresholdBadge");
  const threshDisplay = document.getElementById("threshDisplay");
  const thresholdSlider = document.getElementById("thresholdSlider");
  const presetLow = document.getElementById("presetLow");
  const presetRelaxed = document.getElementById("presetRelaxed");
  const presetBalanced = document.getElementById("presetBalanced");
  const presetStrict = document.getElementById("presetStrict");

  // Left Panel Navigation
  const leftTabLayers = document.getElementById("leftTabLayers");
  const leftTabAssets = document.getElementById("leftTabAssets");
  const layersSection = document.getElementById("layersSection");
  const assetsSection = document.getElementById("assetsSection");

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

  // FSM Artboard Elements
  const stateBanner = document.getElementById("stateBanner");
  const stateIcon = document.getElementById("stateIcon");
  const stateTitle = document.getElementById("stateTitle");
  const stateDesc = document.getElementById("stateDesc");
  const lastTriggerTime = document.getElementById("lastTriggerTime");

  // Telemetry Console & Property Inspector
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

  // Terminal Drawer Tabs
  const tabBtnWs = document.getElementById("tabBtnWs");
  const tabBtnRest = document.getElementById("tabBtnRest");
  const tabBtnThresh = document.getElementById("tabBtnThresh");
  const tabBtnCurl = document.getElementById("tabBtnCurl");

  // Default labels and internal state
  const DEFAULT_LABELS = ["red", "green", "blue", "off", "_silence_", "_unknown_"];
  let knownLabels = [...DEFAULT_LABELS];
  let currentThreshold = 0.80;
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

  // 1. Left Panel Tab Switching (Layers vs Assets)
  if (leftTabLayers && leftTabAssets && layersSection && assetsSection) {
    leftTabLayers.addEventListener("click", () => {
      leftTabLayers.className = "text-white font-semibold flex items-center gap-1.5 border-b-2 border-[#0d99ff] pb-2 pt-2.5";
      leftTabAssets.className = "text-[#a1a1aa] hover:text-white flex items-center gap-1.5 pb-2 pt-2.5";
      layersSection.classList.remove("hidden");
      assetsSection.classList.remove("hidden"); // Keep visible in desktop scroll
    });

    leftTabAssets.addEventListener("click", () => {
      leftTabAssets.className = "text-white font-semibold flex items-center gap-1.5 border-b-2 border-[#0d99ff] pb-2 pt-2.5";
      leftTabLayers.className = "text-[#a1a1aa] hover:text-white flex items-center gap-1.5 pb-2 pt-2.5";
      assetsSection.scrollIntoView({ behavior: "smooth" });
    });
  }

  // 2. Initialize Probability Meters with Figma Minimalist Styling & Threshold Marker
  function initProbBars(labels) {
    if (!probBarsContainer) return;
    probBarsContainer.innerHTML = "";
    const threshPct = Math.round(currentThreshold * 100);

    labels.forEach((label) => {
      const barColorClass =
        label === "red" ? "bg-[#f43f5e]" :
        label === "green" ? "bg-[#10b981]" :
        label === "blue" ? "bg-[#0d99ff]" :
        label === "off" ? "bg-[#a1a1aa]" :
        label === "_silence_" ? "bg-[#71717a]" : "bg-[#8b5cf6]";

      const badgeColor =
        label === "red" ? "text-[#f43f5e]" :
        label === "green" ? "text-[#10b981]" :
        label === "blue" ? "text-[#0d99ff]" :
        label === "off" ? "text-[#f4f4f6]" : "text-[#a1a1aa]";

      const row = document.createElement("div");
      row.className = "space-y-1 font-mono text-xs";
      row.innerHTML = `
        <div class="flex justify-between items-center">
          <span class="font-semibold ${badgeColor}">${label}</span>
          <span id="prob-val-${label}" class="text-[#a1a1aa] font-medium text-[11px]">0.0%</span>
        </div>
        <div class="figma-meter-container">
          <!-- Dynamic Softmax Bar -->
          <div id="prob-bar-${label}" class="h-full rounded-xs ${barColorClass} transition-all duration-100" style="width: 0%"></div>
          <!-- Threshold Marker Guideline -->
          <div class="threshold-marker" id="threshMarker-${label}" style="left: ${threshPct}%" title="Threshold: ${threshPct}%"></div>
        </div>
      `;
      probBarsContainer.appendChild(row);
    });
  }
  initProbBars(knownLabels);

  // 3. Dynamic Threshold Controller
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

    // Update segmented preset button states
    if (presetLow && presetRelaxed && presetBalanced && presetStrict) {
      const activeClass = "figma-segmented-btn active";
      const inactiveClass = "figma-segmented-btn";

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

  // 4. WebSocket Real-Time Connection
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/kws`;
  let socket = null;

  function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      if (wsStatusBadge) {
        wsStatusBadge.className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#18181b] text-[#10b981] border border-[#10b981]/30 text-[11px] font-mono font-medium";
        wsStatusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span> LIVE WS';
      }
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
      if (wsStatusBadge) {
        wsStatusBadge.className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#18181b] text-[#f59e0b] border border-[#f59e0b]/30 text-[11px] font-mono font-medium";
        wsStatusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-[#f59e0b] animate-pulse"></span> Reconnecting...';
      }
      if (footerWsStatus) footerWsStatus.textContent = "WS: Disconnected";
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      socket.close();
    };
  }
  connectWebSocket();

  // 5. Real-Time Audio Downsampling Utility (AudioContext -> 16kHz PCM16)
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

  // 6. Initialize Live Web Audio Context & FFT Analyser
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
        enableMicBtn.className = "px-2 py-0.5 rounded bg-[#10b981]/15 border border-[#10b981]/30 text-[#10b981] font-mono text-[11px] font-medium cursor-default";
        enableMicBtn.innerHTML = "✓ Live FFT Active";
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

  // 7. Voice Stream Transmit UI Controllers
  function setVoiceStreamActiveUI(active) {
    if (active) {
      if (activeStreamBadge) {
        activeStreamBadge.className = "hidden sm:flex items-center gap-1.5 px-2 py-1 rounded bg-[#10b981]/10 border border-[#10b981]/30 font-mono text-[10px] text-[#10b981]";
        if (activeStreamDot) activeStreamDot.className = "w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse";
        if (activeStreamLabel) activeStreamLabel.textContent = "Stream: Transmitting (16 kHz)";
      }
    } else {
      if (activeStreamBadge) {
        activeStreamBadge.className = "hidden sm:flex items-center gap-1.5 px-2 py-1 rounded bg-[#19191d] border border-[#333339] font-mono text-[10px] text-[#a1a1aa]";
        if (activeStreamDot) activeStreamDot.className = "w-1.5 h-1.5 rounded-full bg-[#71717a]";
        if (activeStreamLabel) activeStreamLabel.textContent = "Stream: Idle";
      }
    }
  }

  // 8. Push-to-Talk (PTT) Event Handlers
  async function activatePtt() {
    if (isContinuousMode || isPttActive) return;
    const ok = await initMicrophoneMonitor();
    if (!ok) return;

    isPttActive = true;
    isAudioStreaming = true;
    if (pttButton) {
      pttButton.classList.add("transmitting");
    }
    if (pttIcon) pttIcon.textContent = "🔴";
    if (pttText) pttText.textContent = "TRANSMITTING";
    setVoiceStreamActiveUI(true);
  }

  function deactivatePtt() {
    if (isContinuousMode || !isPttActive) return;
    isPttActive = false;
    isAudioStreaming = false;
    if (pttButton) {
      pttButton.classList.remove("transmitting");
    }
    if (pttIcon) pttIcon.textContent = "🎙️";
    if (pttText) pttText.textContent = "HOLD TO TALK";
    setVoiceStreamActiveUI(false);
  }

  if (pttButton) {
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

  // 9. Continuous Speech Stream Toggle Handler
  if (continuousToggleBtn) {
    continuousToggleBtn.addEventListener("click", async () => {
      if (!isContinuousMode) {
        const ok = await initMicrophoneMonitor();
        if (!ok) return;

        isContinuousMode = true;
        isAudioStreaming = true;
        continuousToggleBtn.classList.add("live");
        if (continuousStatusDot) continuousStatusDot.className = "w-2 h-2 rounded-full bg-[#10b981] animate-pulse";
        if (continuousToggleText) continuousToggleText.textContent = "Continuous: LIVE";
        if (pttButton) {
          pttButton.classList.add("opacity-50", "pointer-events-none");
        }
        setVoiceStreamActiveUI(true);
        addLogEntry("STREAM", "Continuous speech mode engaged. Listening continuously.");
      } else {
        isContinuousMode = false;
        isAudioStreaming = false;
        continuousToggleBtn.classList.remove("live");
        if (continuousStatusDot) continuousStatusDot.className = "w-2 h-2 rounded-full bg-[#71717a]";
        if (continuousToggleText) continuousToggleText.textContent = "Continuous: OFF";
        if (pttButton) {
          pttButton.classList.remove("opacity-50", "pointer-events-none");
        }
        setVoiceStreamActiveUI(false);
      }
    });
  }

  // 10. Live Continuous Streaming Updates from Server
  function handleLiveStreamUpdate(data) {
    if (data.probabilities) {
      Object.entries(data.probabilities).forEach(([lb, p]) => {
        const bar = document.getElementById(`prob-bar-${lb}`);
        const val = document.getElementById(`prob-val-${lb}`);
        if (bar && val) {
          const pct = Math.round(p * 100);
          bar.style.width = `${pct}%`;
          val.textContent = `${pct}%`;

          // Threshold crossing highlight
          if (p >= currentThreshold && lb !== "_silence_" && lb !== "_unknown_") {
            bar.classList.add("brightness-125");
          } else {
            bar.classList.remove("brightness-125");
          }
        }
      });
    }

    // Keyword trigger event from streaming inference
    if (data.triggered && data.keyword) {
      handleKeywordDetected(data.keyword, data.confidence, data.timestamp, "live_stream");
    }
  }

  // 11. Handle Keyword Detections & Reactive FSM State Updates
  function handleKeywordDetected(keyword, confidence, timestamp, source = "mic") {
    const timeStr = new Date().toLocaleTimeString();
    if (lastTriggerTime) {
      lastTriggerTime.textContent = `Last trigger: ${timeStr} (${confidence >= 0 ? (confidence * 100).toFixed(1) + '%' : ''})`;
    }

    if (stateBanner) {
      stateBanner.className = "state-banner-container";
    }

    const kw = keyword.toLowerCase();
    if (kw === "red") {
      if (stateBanner) stateBanner.classList.add("state-red");
      if (stateIcon) {
        stateIcon.className = "w-20 h-20 rounded-xl flex items-center justify-center text-4xl mb-3 bg-[#f43f5e]/20 text-white border border-[#f43f5e]/50 shadow-sm transition-transform duration-200";
        stateIcon.textContent = "🛑";
      }
      if (stateTitle) {
        stateTitle.textContent = "EMERGENCY STOP";
        stateTitle.className = "text-3xl sm:text-4xl font-black tracking-tight text-[#f43f5e] font-mono";
      }
      if (stateDesc) {
        stateDesc.textContent = "Safety Interlock Tripped! All motor outputs disabled (0.0 m/s). Active electromagnetic brake locked.";
      }
    } else if (kw === "green") {
      if (stateBanner) stateBanner.classList.add("state-green");
      if (stateIcon) {
        stateIcon.className = "w-20 h-20 rounded-xl flex items-center justify-center text-4xl mb-3 bg-[#10b981]/20 text-white border border-[#10b981]/50 shadow-sm transition-transform duration-200";
        stateIcon.textContent = "🚀";
      }
      if (stateTitle) {
        stateTitle.textContent = "DRIVE FORWARD";
        stateTitle.className = "text-3xl sm:text-4xl font-black tracking-tight text-[#10b981] font-mono";
      }
      if (stateDesc) {
        stateDesc.textContent = "Patrol Navigation Active. Linear velocity nominal: 0.50 m/s. Obstacle avoidance LiDAR engaged.";
      }
    } else if (kw === "blue") {
      if (stateBanner) stateBanner.classList.add("state-blue");
      if (stateIcon) {
        stateIcon.className = "w-20 h-20 rounded-xl flex items-center justify-center text-4xl mb-3 bg-[#0d99ff]/20 text-white border border-[#0d99ff]/50 shadow-sm transition-transform duration-200";
        stateIcon.textContent = "🧭";
      }
      if (stateTitle) {
        stateTitle.textContent = "MANUAL NAVIGATION";
        stateTitle.className = "text-3xl sm:text-4xl font-black tracking-tight text-[#0d99ff] font-mono";
      }
      if (stateDesc) {
        stateDesc.textContent = "Waypoint Heading Adjust. Angular velocity: +0.35 rad/s. Operator manual steering active.";
      }
    } else if (kw === "off") {
      if (stateBanner) stateBanner.classList.add("state-off");
      if (stateIcon) {
        stateIcon.className = "w-20 h-20 rounded-xl flex items-center justify-center text-4xl mb-3 bg-[#24242a] text-[#f4f4f6] border border-[#333339] shadow-sm transition-transform duration-200";
        stateIcon.textContent = "💤";
      }
      if (stateTitle) {
        stateTitle.textContent = "SYSTEM STANDBY";
        stateTitle.className = "text-3xl sm:text-4xl font-black tracking-tight text-[#a1a1aa] font-mono";
      }
      if (stateDesc) {
        stateDesc.textContent = "Low-power park mode entered. Sensors idling at 1.0 Hz telemetry heartbeat.";
      }
    }

    const srcTag = source === "simulated" ? "SIM" : source === "live_stream" ? "LIVE" : "MIC";
    addLogEntry(keyword.toUpperCase(), `[${srcTag}] Conf: ${(confidence * 100).toFixed(1)}% | T: ${timestamp}s -> FSM State Triggered`);
  }

  // 12. Append Log Entry to Terminal Stream
  function addLogEntry(tag, msg) {
    if (!eventLog) return;
    if (eventLog.children.length === 1 && eventLog.children[0].classList.contains("italic")) {
      eventLog.innerHTML = "";
    }
    const entry = document.createElement("div");
    entry.className = "py-1 px-2 rounded bg-[#1c1c1f] border border-[#2d2d34] flex items-center justify-between font-mono text-[11px]";

    const tagBadge =
      tag === "RED" ? "bg-[#f43f5e]/15 text-[#f43f5e] border border-[#f43f5e]/30 font-bold" :
      tag === "GREEN" ? "bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30 font-bold" :
      tag === "BLUE" ? "bg-[#0d99ff]/15 text-[#0d99ff] border border-[#0d99ff]/30 font-bold" :
      tag === "OFF" ? "bg-[#333339] text-[#a1a1aa] border border-[#44444d] font-bold" :
      tag === "STREAM" ? "bg-[#06b6d4]/15 text-[#06b6d4] border border-[#06b6d4]/30 font-bold" :
      tag === "REST" ? "bg-[#a855f7]/15 text-[#a855f7] border border-[#a855f7]/30 font-bold" :
      tag === "THRESH" ? "bg-[#f59e0b]/15 text-[#f59e0b] border border-[#f59e0b]/30 font-bold" :
      "bg-[#28282e] text-[#a1a1aa] border border-[#38383e] font-bold";

    entry.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-[10px] text-[#71717a]">${new Date().toLocaleTimeString()}</span>
        <span class="px-1.5 py-0.2 rounded text-[10px] ${tagBadge}">[${tag}]</span>
        <span class="text-[#f4f4f6]">${msg}</span>
      </div>
      <span class="text-[10px] text-[#52525b] font-mono">0x${Math.floor(Math.random() * 0xffff).toString(16)}</span>
    `;
    eventLog.insertBefore(entry, eventLog.firstChild);
    while (eventLog.children.length > 50) {
      eventLog.removeChild(eventLog.lastChild);
    }
  }

  if (clearLogBtn) {
    clearLogBtn.addEventListener("click", () => {
      eventLog.innerHTML = '<div class="text-[#71717a] italic p-1">[system] Telemetry log cleared. Stream listening...</div>';
    });
  }

  // 13. Global Interactive Keyword Simulation Dispatcher
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

  // 14. Terminal Panel Tab Switching
  if (tabBtnWs && tabBtnRest && tabBtnThresh && tabBtnCurl) {
    function resetTabs() {
      [tabBtnWs, tabBtnRest, tabBtnThresh, tabBtnCurl].forEach((t) => (t.className = "term-tab"));
    }

    tabBtnWs.addEventListener("click", () => {
      resetTabs();
      tabBtnWs.className = "term-tab active";
    });

    tabBtnRest.addEventListener("click", () => {
      resetTabs();
      tabBtnRest.className = "term-tab active";
      if (lastRestPayload) {
        addLogEntry("REST", `Cached REST Output: Top='${lastRestPayload.top_class}' (${(lastRestPayload.confidence * 100).toFixed(1)}%)`);
      } else {
        addLogEntry("REST", "No REST payload cached yet. Click 'sample_audio.wav' or 'Record Mic' to test.");
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

  // 15. REST API Audio Dispatcher
  async function sendAudioBlobForClassification(blob, filename = "audio.wav") {
    const formData = new FormData();
    formData.append("file", blob, filename);
    if (restResult) {
      restResult.classList.remove("hidden");
      restResult.innerHTML = '<span class="text-[#a1a1aa] font-mono">POST /api/v1/classify • Running DS-CNN int8 inference...</span>';
    }

    try {
      const resp = await fetch("/api/v1/classify", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      lastRestPayload = data;
      if (restResult) {
        restResult.innerHTML = `<pre class="text-[#10b981] font-mono text-[11px] leading-snug">${JSON.stringify(data, null, 2)}</pre>`;
      }

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
      if (restResult) {
        restResult.innerHTML = `<span class="text-[#f43f5e] font-mono text-[11px]">Error: ${err.message}</span>`;
      }
      addLogEntry("ERROR", `REST error: ${err.message}`);
    }
  }

  // 15.1 Built-in Sample Audio Button
  if (useSampleBtn) {
    useSampleBtn.addEventListener("click", async () => {
      if (restResult) {
        restResult.classList.remove("hidden");
        restResult.innerHTML = '<span class="text-[#a1a1aa] font-mono">Fetching sample_audio.wav from server...</span>';
      }
      try {
        const res = await fetch("/api/v1/sample-audio");
        if (!res.ok) throw new Error("sample_audio.wav not found on server");
        const blob = await res.blob();
        await sendAudioBlobForClassification(blob, "sample_audio.wav");
      } catch (err) {
        if (restResult) {
          restResult.innerHTML = `<span class="text-[#f43f5e] font-mono text-[11px]">Error: ${err.message}</span>`;
        }
      }
    });
  }

  // 15.2 Single Take Mic Recorder (1s)
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
        if (recordMicIcon) recordMicIcon.textContent = "🔴";
        if (recordMicText) recordMicText.textContent = "Listening... (1s)";
        recordBrowserMicBtn.classList.add("border-[#f43f5e]");

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

          if (recordMicIcon) recordMicIcon.textContent = "🎙️";
          if (recordMicText) recordMicText.textContent = "Record Mic (1s)";
          recordBrowserMicBtn.classList.remove("border-[#f43f5e]");

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

  // 15.3 Custom File Upload Form
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

  // 16. Real-Time 60 FPS Audio Spectrum & Waveform Visualizer
  if (audioCanvas) {
    const ctx = audioCanvas.getContext("2d");

    function renderAudioVisualizer() {
      requestAnimationFrame(renderAudioVisualizer);

      const width = audioCanvas.width = audioCanvas.offsetWidth || 500;
      const height = audioCanvas.height = 56;

      ctx.clearRect(0, 0, width, height);

      // 1. Draw Subtle Grid
      ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
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

      // If Analyser is connected, read REAL microphone audio
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
            clampedDbfs > -20 ? "text-[#f43f5e] font-bold" :
            clampedDbfs > -45 ? "text-[#f59e0b] font-bold" : "text-[#10b981] font-bold";
        }
        if (liveDbfsText) {
          liveDbfsText.textContent = `${clampedDbfs.toFixed(1)} dBFS`;
        }
        if (liveVuBar) {
          const vuPct = Math.max(4, Math.min(100, Math.round(((clampedDbfs + 75) / 75) * 100)));
          liveVuBar.style.width = `${vuPct}%`;
          liveVuBar.className =
            vuPct > 75 ? "h-full rounded-full bg-[#f43f5e]" :
            vuPct > 45 ? "h-full rounded-full bg-[#f59e0b]" : "h-full rounded-full bg-[#10b981]";
        }

        // 2. Draw Real Frequency Spectrum Bars (48 Bins across audible spectrum)
        const numBars = 48;
        const barWidth = Math.floor(width / numBars) - 2;
        for (let i = 0; i < numBars; i++) {
          const binIndex = Math.floor(i * (freqDataArray.length / numBars));
          const val = freqDataArray[binIndex] / 255.0;
          const barHeight = Math.max(2, val * (height - 8));
          const x = i * (barWidth + 2) + 2;
          const y = height - barHeight - 2;

          if (val > 0.72) {
            ctx.fillStyle = "#f43f5e";
          } else if (val > 0.42) {
            ctx.fillStyle = "#f59e0b";
          } else if (isAudioStreaming) {
            ctx.fillStyle = "#10b981";
          } else {
            ctx.fillStyle = "#0d99ff";
          }
          ctx.fillRect(x, y, barWidth, barHeight);
        }

        // 3. Draw Real Time-Domain Waveform Overlay Line
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = isAudioStreaming ? "rgba(16, 185, 129, 0.9)" : "rgba(13, 153, 255, 0.85)";
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

      } else {
        // Standby prompt before mic permission granted
        ctx.fillStyle = "rgba(161, 161, 170, 0.6)";
        ctx.font = "11px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Microphone Standby. Click 'Enable Mic Monitor' or hold 'HOLD TO TALK' to activate live spectrum.", width / 2, height / 2 + 4);
      }
    }

    renderAudioVisualizer();
  }
});
