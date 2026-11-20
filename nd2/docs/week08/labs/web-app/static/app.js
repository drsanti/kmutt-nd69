// RobotOS Edge AI Studio - Industrial SCADA Dashboard Frontend

document.addEventListener("DOMContentLoaded", () => {
  const wsStatusBadge = document.getElementById("wsStatusBadge");
  const footerWsStatus = document.getElementById("footerWsStatus");
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

  const tabBtnWs = document.getElementById("tabBtnWs");
  const tabBtnRest = document.getElementById("tabBtnRest");
  const tabBtnModel = document.getElementById("tabBtnModel");

  const DEFAULT_LABELS = ["red", "green", "blue", "off", "_silence_", "_unknown_"];
  let knownLabels = [...DEFAULT_LABELS];
  let modelMetaData = null;
  let lastRestPayload = null;

  // 1. Initialize Probability Meters with Industrial Styling
  function initProbBars(labels) {
    probBarsContainer.innerHTML = "";
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
      row.className = "space-y-1 font-mono";
      row.innerHTML = `
        <div class="flex justify-between text-[11px] items-center">
          <span class="font-bold tracking-wider ${badgeColor}">${label}</span>
          <span id="prob-val-${label}" class="text-slate-400 font-bold">0.0%</span>
        </div>
        <div class="w-full bg-[#0a0e14] rounded h-2 overflow-hidden border border-[#212b3d] p-[1px]">
          <div id="prob-bar-${label}" class="h-full rounded-sm ${colorClass} transition-all duration-200" style="width: 0%"></div>
        </div>
      `;
      probBarsContainer.appendChild(row);
    });
  }
  initProbBars(knownLabels);

  // 2. Fetch Model Metadata via REST API
  fetch("/api/v1/model/info")
    .then((res) => res.json())
    .then((data) => {
      if (data && data.labels) {
        knownLabels = data.labels;
        modelMetaData = data;
        initProbBars(knownLabels);
      }
    })
    .catch((err) => console.log("Model info not ready yet:", err));

  // 3. Connect to WebSocket Stream
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/kws`;
  let socket = null;

  function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      wsStatusBadge.className =
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      wsStatusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> LIVE MIC (16kHz)';
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
          handleKeywordDetected(data.keyword, data.confidence, data.timestamp);
        }
      } catch (err) {
        console.error("Failed to parse WS message:", err);
      }
    };

    socket.onclose = () => {
      wsStatusBadge.className =
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20";
      wsStatusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span> Reconnecting...';
      if (footerWsStatus) footerWsStatus.textContent = "WS: Disconnected";
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      socket.close();
    };
  }
  connectWebSocket();

  // 4. Handle Keyword Detections & Reactive Industrial State Updates
  function handleKeywordDetected(keyword, confidence, timestamp) {
    const timeStr = new Date().toLocaleTimeString();
    lastTriggerTime.textContent = `Last trigger: ${timeStr} (${timestamp}s)`;

    // Reset glows and hazard styling
    stateBanner.className = "p-7 rounded-xl border-2 bg-[#0e141f]/90 flex flex-col items-center justify-center text-center transition-all duration-300 relative overflow-hidden shadow-2xl";

    const kw = keyword.toLowerCase();
    if (kw === "red") {
      stateBanner.classList.add("glow-red", "hazard-stripes");
      stateIcon.className = "w-20 h-20 rounded-2xl flex items-center justify-center text-4xl font-black mb-3 bg-red-600 text-white shadow-xl scale-105 transition-all";
      stateIcon.textContent = "🛑";
      stateTitle.textContent = "EMERGENCY STOP";
      stateTitle.className = "text-3xl font-black tracking-tight text-red-400 font-mono";
      stateDesc.textContent = "Safety Interlock Tripped! All motor outputs disabled (0.0 m/s). Active electromagnetic brake locked.";
    } else if (kw === "green") {
      stateBanner.classList.add("glow-green");
      stateIcon.className = "w-20 h-20 rounded-2xl flex items-center justify-center text-4xl font-black mb-3 bg-emerald-600 text-white shadow-xl scale-105 transition-all";
      stateIcon.textContent = "🚀";
      stateTitle.textContent = "DRIVE FORWARD";
      stateTitle.className = "text-3xl font-black tracking-tight text-emerald-400 font-mono";
      stateDesc.textContent = "Patrol Navigation Active. Linear velocity nominal: 0.50 m/s. Obstacle avoidance LiDAR engaged.";
    } else if (kw === "blue") {
      stateBanner.classList.add("glow-blue");
      stateIcon.className = "w-20 h-20 rounded-2xl flex items-center justify-center text-4xl font-black mb-3 bg-sky-600 text-white shadow-xl scale-105 transition-all";
      stateIcon.textContent = "🧭";
      stateTitle.textContent = "MANUAL NAVIGATION";
      stateTitle.className = "text-3xl font-black tracking-tight text-sky-400 font-mono";
      stateDesc.textContent = "Waypoint Heading Adjust. Angular velocity: +0.35 rad/s. Operator manual steering active.";
    } else if (kw === "off") {
      stateBanner.classList.add("glow-amber");
      stateIcon.className = "w-20 h-20 rounded-2xl flex items-center justify-center text-4xl font-black mb-3 bg-slate-800 text-slate-300 shadow-xl transition-all";
      stateIcon.textContent = "💤";
      stateTitle.textContent = "SYSTEM STANDBY";
      stateTitle.className = "text-3xl font-black tracking-tight text-slate-300 font-mono";
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

    addLogEntry(keyword.toUpperCase(), `Confidence: ${(confidence * 100).toFixed(1)}% | T: ${timestamp}s -> FSM State Transition`);
  }

  // 5. Append Log Entry to Terminal
  function addLogEntry(tag, msg) {
    if (eventLog.children.length === 1 && eventLog.children[0].classList.contains("italic")) {
      eventLog.innerHTML = "";
    }
    const entry = document.createElement("div");
    entry.className = "p-1.5 rounded bg-[#0e141f] border border-[#1a2333] flex items-center justify-between font-mono text-[11px]";

    const tagBadge =
      tag === "RED" ? "bg-red-500/20 text-red-400 border border-red-500/30" :
      tag === "GREEN" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" :
      tag === "BLUE" ? "bg-sky-500/20 text-sky-400 border border-sky-500/30" :
      tag === "OFF" ? "bg-slate-700/30 text-slate-300 border border-slate-600/30" :
      tag === "REST" ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" :
      "bg-slate-800 text-slate-400 border border-slate-700";

    entry.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-[10px] text-slate-500">${new Date().toLocaleTimeString()}</span>
        <span class="px-1.5 py-0.2 rounded text-[10px] font-bold ${tagBadge}">[${tag}]</span>
        <span class="text-slate-300">${msg}</span>
      </div>
      <span class="text-[9px] text-slate-600">ID:0x${Math.floor(Math.random() * 0xffff).toString(16)}</span>
    `;
    eventLog.insertBefore(entry, eventLog.firstChild);
    while (eventLog.children.length > 50) {
      eventLog.removeChild(eventLog.lastChild);
    }
  }

  clearLogBtn.addEventListener("click", () => {
    eventLog.innerHTML = '<div class="text-slate-500 italic p-1">[system] Telemetry log cleared. Stream listening...</div>';
  });

  // 6. Terminal Panel Tab Switching
  if (tabBtnWs && tabBtnRest && tabBtnModel) {
    tabBtnWs.addEventListener("click", () => {
      tabBtnWs.className = "term-tab active flex items-center gap-1.5";
      tabBtnRest.className = "term-tab";
      tabBtnModel.className = "term-tab";
    });

    tabBtnRest.addEventListener("click", () => {
      tabBtnWs.className = "term-tab";
      tabBtnRest.className = "term-tab active";
      tabBtnModel.className = "term-tab";
      if (lastRestPayload) {
        addLogEntry("REST", `Cached REST Response: Top=${lastRestPayload.top_class} (${(lastRestPayload.confidence * 100).toFixed(1)}%)`);
      }
    });

    tabBtnModel.addEventListener("click", () => {
      tabBtnWs.className = "term-tab";
      tabBtnRest.className = "term-tab";
      tabBtnModel.className = "term-tab active";
      if (modelMetaData) {
        addLogEntry("MODEL", `Meta: Arch=DS-CNN int8, Labels=[${modelMetaData.labels.join(", ")}], Threshold=${modelMetaData.threshold}`);
      }
    });
  }

  // 7. REST API Shared Dispatcher
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
      restResult.innerHTML = `<pre class="text-emerald-400 font-mono text-[10px]">${JSON.stringify(data, null, 2)}</pre>`;

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

      if (data.top_class && data.confidence > 0.5) {
        handleKeywordDetected(data.top_class, data.confidence, 0.0);
      }
    } catch (err) {
      restResult.innerHTML = `<span class="text-red-400 font-mono text-[10px]">Error: ${err.message}</span>`;
      addLogEntry("ERROR", `REST error: ${err.message}`);
    }
  }

  // 7.1 Use Built-in Sample Audio Button
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
        restResult.innerHTML = `<span class="text-red-400 font-mono text-[10px]">Error: ${err.message}</span>`;
      }
    });
  }

  // 7.2 Browser Microphone Audio Recorder & WAV Encoder
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
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true); // 16-bit
    writeString(36, "data");
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
  }

  async function recordBrowserWav(durationMs = 1000) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    const pcmChunks = [];

    return new Promise((resolve) => {
      processor.onaudioprocess = (e) => {
        pcmChunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
      };
      source.connect(processor);
      processor.connect(audioContext.destination);

      setTimeout(() => {
        processor.disconnect();
        source.disconnect();
        stream.getTracks().forEach((t) => t.stop());
        audioContext.close();

        const totalLen = pcmChunks.reduce((acc, c) => acc + c.length, 0);
        const full = new Float32Array(totalLen);
        let offset = 0;
        pcmChunks.forEach((c) => {
          full.set(c, offset);
          offset += c.length;
        });
        const samples = full.subarray(0, 16000);
        const wavBuffer = encodeWav(samples, 16000);
        resolve(new Blob([wavBuffer], { type: "audio/wav" }));
      }, durationMs);
    });
  }

  if (recordBrowserMicBtn) {
    recordBrowserMicBtn.addEventListener("click", async () => {
      const icon = document.getElementById("recordMicIcon");
      const txt = document.getElementById("recordMicText");
      try {
        icon.textContent = "🔴";
        txt.textContent = "Recording...";
        recordBrowserMicBtn.classList.add("animate-pulse", "bg-red-950/60", "border-red-500/50");
        const blob = await recordBrowserWav(1000);
        icon.textContent = "🎙️";
        txt.textContent = "Record Mic (1s)";
        recordBrowserMicBtn.classList.remove("animate-pulse", "bg-red-950/60", "border-red-500/50");
        await sendAudioBlobForClassification(blob, "browser_mic.wav");
      } catch (err) {
        icon.textContent = "🎙️";
        txt.textContent = "Record Mic (1s)";
        recordBrowserMicBtn.classList.remove("animate-pulse", "bg-red-950/60", "border-red-500/50");
        alert("Microphone permission denied or not supported in this browser: " + err.message);
      }
    });
  }

  // 7.3 Custom File Upload
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = audioFileInput.files[0];
    if (!file) {
      alert("Please select a .wav file or click 'Use Built-in Sample'.");
      return;
    }
    await sendAudioBlobForClassification(file, file.name);
  });
});
