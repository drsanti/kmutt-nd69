// RobotOS Edge AI Studio - Industrial SCADA Dashboard Frontend

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const wsStatusBadge = document.getElementById("wsStatusBadge");
  const footerWsStatus = document.getElementById("footerWsStatus");
  const headerThresholdBadge = document.getElementById("headerThresholdBadge");
  const threshDisplay = document.getElementById("threshDisplay");
  const thresholdSlider = document.getElementById("thresholdSlider");
  const presetRelaxed = document.getElementById("presetRelaxed");
  const presetBalanced = document.getElementById("presetBalanced");
  const presetStrict = document.getElementById("presetStrict");

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
          <div id="prob-bar-${label}" class="h-full rounded-sm ${colorClass} transition-all duration-200" style="width: 0%"></div>
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
    if (presetRelaxed && presetBalanced && presetStrict) {
      presetRelaxed.className = Math.abs(currentThreshold - 0.60) < 0.02
        ? "flex-1 py-1 px-1.5 rounded bg-sky-950/50 border border-sky-500/40 text-[10px] font-mono text-sky-300 font-bold text-center"
        : "flex-1 py-1 px-1.5 rounded bg-[#182335] hover:bg-[#22314a] border border-[#273852] text-[10px] font-mono text-slate-300 text-center";
      presetBalanced.className = Math.abs(currentThreshold - 0.80) < 0.02
        ? "flex-1 py-1 px-1.5 rounded bg-sky-950/50 border border-sky-500/40 text-[10px] font-mono text-sky-300 font-bold text-center"
        : "flex-1 py-1 px-1.5 rounded bg-[#182335] hover:bg-[#22314a] border border-[#273852] text-[10px] font-mono text-slate-300 text-center";
      presetStrict.className = Math.abs(currentThreshold - 0.95) < 0.02
        ? "flex-1 py-1 px-1.5 rounded bg-sky-950/50 border border-sky-500/40 text-[10px] font-mono text-sky-300 font-bold text-center"
        : "flex-1 py-1 px-1.5 rounded bg-[#182335] hover:bg-[#22314a] border border-[#273852] text-[10px] font-mono text-slate-300 text-center";
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

  if (presetRelaxed) {
    presetRelaxed.addEventListener("click", () => {
      updateThresholdUI(0.60);
      pushThresholdToServer(0.60);
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

  // 3. Fetch Model Metadata via REST API
  fetch("/api/v1/model/info")
    .then((res) => res.json())
    .then((data) => {
      if (data) {
        if (data.labels) {
          knownLabels = data.labels;
        }
        if (data.threshold) {
          updateThresholdUI(data.threshold);
        }
        modelMetaData = data;
        initProbBars(knownLabels);
      }
    })
    .catch((err) => console.log("Model info not ready yet:", err));

  // 4. Connect to WebSocket Stream
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/kws`;
  let socket = null;

  function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      wsStatusBadge.className =
        "inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25";
      wsStatusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> LIVE MIC (16kHz)';
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

  // 5. Handle Keyword Detections & Reactive Industrial State Updates
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

    // Update Softmax Meters
    knownLabels.forEach((lb) => {
      const bar = document.getElementById(`prob-bar-${lb}`);
      const val = document.getElementById(`prob-val-${lb}`);
      if (bar && val) {
        if (lb.toLowerCase() === kw) {
          const pct = Math.round(confidence * 100);
          bar.style.width = `${pct}%`;
          val.textContent = `${pct}%`;
        } else {
          bar.style.width = "2%";
          val.textContent = "< 2%";
        }
      }
    });

    const srcTag = source === "simulated" ? "SIM" : "MIC";
    addLogEntry(keyword.toUpperCase(), `[${srcTag}] Conf: ${(confidence * 100).toFixed(1)}% | T: ${timestamp}s -> FSM State Triggered`);
  }

  // 6. Append Log Entry to Terminal
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

  // 7. Global Interactive Keyword Simulation Dispatcher
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
      // Fallback local UI trigger
      handleKeywordDetected(keyword, 0.95, 0.0, "simulated");
    }
  };

  // 8. Terminal Panel Tab Switching
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

  // 9. REST API Shared Audio Dispatcher
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

  // 9.1 Use Built-in Sample Audio Button
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

  // 9.2 Browser Microphone Audio Recorder & WAV Encoder (Web Audio API)
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

        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        const recordedSamples = [];
        const targetDurationSec = 1.0;
        const totalSamplesNeeded = Math.floor(audioCtx.sampleRate * targetDurationSec);

        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          for (let i = 0; i < inputData.length; i++) {
            recordedSamples.push(inputData[i]);
            if (recordedSamples.length >= totalSamplesNeeded) break;
          }
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);

        setTimeout(async () => {
          processor.disconnect();
          source.disconnect();
          stream.getTracks().forEach((track) => track.stop());

          recordMicIcon.textContent = "🎙️";
          recordMicText.textContent = "Record Browser Mic (1s)";
          recordBrowserMicBtn.classList.remove("bg-red-950/60", "border-red-500/60");

          // Downsample to 16 kHz
          const rawFloat32 = new Float32Array(recordedSamples);
          const ratio = 16000 / audioCtx.sampleRate;
          const newLength = Math.round(rawFloat32.length * ratio);
          const resampled = new Float32Array(newLength);
          for (let i = 0; i < newLength; i++) {
            const origIndex = i / ratio;
            const i1 = Math.floor(origIndex);
            const i2 = Math.min(i1 + 1, rawFloat32.length - 1);
            const frac = origIndex - i1;
            resampled[i] = rawFloat32[i1] * (1 - frac) + rawFloat32[i2] * frac;
          }

          const wavBlob = encodeWav(resampled, 16000);
          await sendAudioBlobForClassification(wavBlob, "browser_mic.wav");
        }, 1100);
      } catch (err) {
        alert("Microphone permission denied or device not found: " + err.message);
      }
    });
  }

  // 9.3 Custom File Upload Form
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

  // 10. Live Oscilloscope Audio Waveform Animation
  if (audioCanvas) {
    const ctx = audioCanvas.getContext("2d");
    let phase = 0;

    function drawVisualizer() {
      const width = audioCanvas.width = audioCanvas.offsetWidth || 500;
      const height = audioCanvas.height = 52;

      ctx.clearRect(0, 0, width, height);

      // Draw subtle grid lines
      ctx.strokeStyle = "rgba(56, 189, 248, 0.08)";
      ctx.lineWidth = 1;
      for (let x = 0; x < width; x += 30) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 15) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Draw active sine-pulse waveform
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#38bdf8";
      ctx.shadowColor = "#38bdf8";
      ctx.shadowBlur = 8;
      ctx.beginPath();

      const centerY = height / 2;
      const points = 60;
      const step = width / points;

      for (let i = 0; i <= points; i++) {
        const x = i * step;
        const normX = i / points;
        const amp = Math.sin(normX * Math.PI) * 14;
        const y = centerY + Math.sin(normX * 8 + phase) * amp * 0.7 + Math.sin(normX * 16 - phase * 1.5) * (amp * 0.3);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.shadowBlur = 0;

      phase += 0.04;
      requestAnimationFrame(drawVisualizer);
    }
    requestAnimationFrame(drawVisualizer);
  }
});
