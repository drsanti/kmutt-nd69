// ND02 Voice Dashboard Frontend JavaScript

document.addEventListener("DOMContentLoaded", () => {
  const wsStatusBadge = document.getElementById("wsStatusBadge");
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

  const DEFAULT_LABELS = ["red", "green", "blue", "off", "_silence_", "_unknown_"];
  let knownLabels = [...DEFAULT_LABELS];

  // 1. Initialize Probability Bars
  function initProbBars(labels) {
    probBarsContainer.innerHTML = "";
    labels.forEach((label) => {
      const row = document.createElement("div");
      row.className = "space-y-1";
      row.innerHTML = `
        <div class="flex justify-between text-xs">
          <span class="font-mono font-medium text-slate-300">${label}</span>
          <span id="prob-val-${label}" class="font-mono text-slate-400">0.0%</span>
        </div>
        <div class="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-700/50">
          <div id="prob-bar-${label}" class="h-2.5 rounded-full bg-blue-500 transition-all duration-300" style="width: 0%"></div>
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
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      wsStatusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> Live Stream Active';
      addLogEntry("System", "WebSocket stream connected to server.");
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
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20";
      wsStatusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span> Reconnecting...';
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      socket.close();
    };
  }
  connectWebSocket();

  // 4. Handle Keyword Detections & Reactive State Updates
  function handleKeywordDetected(keyword, confidence, timestamp) {
    const timeStr = new Date().toLocaleTimeString();
    lastTriggerTime.textContent = `Last trigger: ${timeStr} (${timestamp}s)`;

    // Update UI State Machine
    stateBanner.classList.remove("glow-red", "glow-green", "glow-blue", "border-red-500", "border-emerald-500", "border-blue-500", "border-slate-700");

    if (keyword === "red") {
      stateBanner.className = "p-8 rounded-xl border-2 border-red-500 bg-red-950/40 glow-red flex flex-col items-center justify-center text-center transition-all duration-300";
      stateIcon.className = "w-20 h-20 rounded-full flex items-center justify-center text-3xl font-black mb-3 bg-red-600 text-white shadow-lg shadow-red-500/30";
      stateIcon.textContent = "STOP";
      stateTitle.textContent = "EMERGENCY STOP";
      stateTitle.className = "text-3xl font-extrabold tracking-tight text-red-300";
      stateDesc.textContent = "Motors disengaged. Safety interlock triggered.";
    } else if (keyword === "green") {
      stateBanner.className = "p-8 rounded-xl border-2 border-emerald-500 bg-emerald-950/40 glow-green flex flex-col items-center justify-center text-center transition-all duration-300";
      stateIcon.className = "w-20 h-20 rounded-full flex items-center justify-center text-3xl font-black mb-3 bg-emerald-600 text-white shadow-lg shadow-emerald-500/30";
      stateIcon.textContent = "RUN";
      stateTitle.textContent = "DRIVE FORWARD";
      stateTitle.className = "text-3xl font-extrabold tracking-tight text-emerald-300";
      stateDesc.textContent = "Motors driving forward at nominal speed.";
    } else if (keyword === "blue") {
      stateBanner.className = "p-8 rounded-xl border-2 border-blue-500 bg-blue-950/40 glow-blue flex flex-col items-center justify-center text-center transition-all duration-300";
      stateIcon.className = "w-20 h-20 rounded-full flex items-center justify-center text-3xl font-black mb-3 bg-blue-600 text-white shadow-lg shadow-blue-500/30";
      stateIcon.textContent = "NAV";
      stateTitle.textContent = "TURNING LEFT";
      stateTitle.className = "text-3xl font-extrabold tracking-tight text-blue-300";
      stateDesc.textContent = "Differential steering executing 90 degree left turn.";
    } else if (keyword === "off") {
      stateBanner.className = "p-8 rounded-xl border-2 border-slate-700 bg-slate-900/80 flex flex-col items-center justify-center text-center transition-all duration-300";
      stateIcon.className = "w-20 h-20 rounded-full flex items-center justify-center text-3xl font-black mb-3 bg-slate-800 text-slate-400";
      stateIcon.textContent = "PWR";
      stateTitle.textContent = "STANDBY";
      stateTitle.className = "text-3xl font-extrabold tracking-tight text-slate-300";
      stateDesc.textContent = "Robot in low-power idle standby.";
    }

    // Update Probability Bars
    knownLabels.forEach((lb) => {
      const bar = document.getElementById(`prob-bar-${lb}`);
      const val = document.getElementById(`prob-val-${lb}`);
      if (bar && val) {
        if (lb === keyword) {
          const pct = Math.round(confidence * 100);
          bar.style.width = `${pct}%`;
          val.textContent = `${pct}%`;
          bar.className = "h-2.5 rounded-full bg-emerald-500 transition-all duration-300";
        } else {
          bar.style.width = "4%";
          val.textContent = "4%";
          bar.className = "h-2.5 rounded-full bg-slate-700 transition-all duration-300";
        }
      }
    });

    addLogEntry(keyword.toUpperCase(), `Confidence: ${(confidence * 100).toFixed(1)}% | Board Time: ${timestamp}s`);
  }

  // 5. Append Log Entry
  function addLogEntry(tag, msg) {
    if (eventLog.children.length === 1 && eventLog.children[0].classList.contains("italic")) {
      eventLog.innerHTML = "";
    }
    const entry = document.createElement("div");
    entry.className = "p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between";
    const tagColor =
      tag === "RED" ? "text-red-400 font-bold" :
      tag === "GREEN" ? "text-emerald-400 font-bold" :
      tag === "BLUE" ? "text-blue-400 font-bold" :
      tag === "OFF" ? "text-slate-400 font-bold" : "text-slate-300";

    entry.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">${new Date().toLocaleTimeString()}</span>
        <span class="${tagColor}">[${tag}]</span>
        <span class="text-slate-300">${msg}</span>
      </div>
    `;
    eventLog.insertBefore(entry, eventLog.firstChild);
    while (eventLog.children.length > 20) {
      eventLog.removeChild(eventLog.lastChild);
    }
  }

  clearLogBtn.addEventListener("click", () => {
    eventLog.innerHTML = '<div class="text-slate-500 italic p-2">Log cleared. Listening for events...</div>';
  });

  // 6. Test REST API via File Upload
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = audioFileInput.files[0];
    if (!file) {
      alert("Please select a .wav file to classify.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    restResult.classList.remove("hidden");
    restResult.innerHTML = '<span class="text-slate-400">Uploading and running inference...</span>';

    try {
      const resp = await fetch("/api/v1/classify", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      restResult.innerHTML = `<pre class="text-emerald-400">${JSON.stringify(data, null, 2)}</pre>`;

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
    } catch (err) {
      restResult.innerHTML = `<span class="text-red-400">Error: ${err.message}</span>`;
    }
  });
});
