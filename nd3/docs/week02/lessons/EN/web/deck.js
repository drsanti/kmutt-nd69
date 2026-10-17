const slides = [
  { file: "01-why-ros-and-digital-twin.png", title: "Why Automation Moves to a ROS-Style Architecture and a Digital Twin", act: "Overview" },
  { file: "02-the-graph.png", title: "The Graph — Nodes and Topics", act: "The graph" },
  { file: "03-messages-and-schema.png", title: "Messages and Schema" },
  { file: "04-services-and-actions.png", title: "Services and Actions" },
  { file: "05-parameters-and-lifecycle.png", title: "Parameters and Lifecycle" },
  { file: "06-tf-frames.png", title: "TF — Frames and Transforms" },
  { file: "07-observe-and-debug.png", title: "Observing and Debugging a Distributed System" },
  { file: "08-qos-and-determinism.png", title: "QoS and Determinism" },
  { file: "09-digital-twin.png", title: "What a Digital Twin Is", act: "The twin" },
  { file: "10-twin-meets-middleware.png", title: "The Twin on the Middleware" },
  { file: "11-three-languages.png", title: "The Same Concepts in Three Languages", act: "Three languages" },
];

const frame = document.querySelector("#frame");
const img = document.querySelector("#slide");
const titleEl = document.querySelector("#slide-title");
const countEl = document.querySelector("#slide-count");
const ticksEl = document.querySelector("#ticks");
const live = document.querySelector("#live");
const index = document.querySelector("#index");
const indexBody = document.querySelector("#index-body");
const canvas = document.querySelector("#laser");
const ctx = canvas.getContext("2d");

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const TRAIL_MS = 1100;

let indexAt = slideFromHash();
let trail = [];
let sparks = [];
let pointing = false;
let head = null;

function slideFromHash() {
  const n = Number(location.hash.replace("#", ""));
  if (Number.isInteger(n) && n >= 1 && n <= slides.length) return n - 1;
  return 0;
}

function show(next) {
  indexAt = (next + slides.length) % slides.length;
  const slide = slides[indexAt];
  img.src = `../images/${slide.file}`;
  img.alt = slide.title;
  titleEl.textContent = slide.title;
  countEl.textContent = `${String(indexAt + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`;
  document.title = `${String(indexAt + 1).padStart(2, "0")} · ${slide.title}`;
  live.textContent = `Slide ${indexAt + 1} of ${slides.length}. ${slide.title}`;
  const hash = `#${String(indexAt + 1).padStart(2, "0")}`;
  if (location.hash !== hash) history.replaceState(null, "", hash);
  for (const button of ticksEl.children) {
    button.setAttribute("aria-selected", button.dataset.index === String(indexAt) ? "true" : "false");
  }
  for (const button of indexBody.querySelectorAll(".lesson")) {
    if (button.dataset.index === String(indexAt)) button.setAttribute("aria-current", "true");
    else button.removeAttribute("aria-current");
  }
}

function buildChrome() {
  slides.forEach((slide, i) => {
    const tick = document.createElement("button");
    tick.type = "button";
    tick.dataset.index = String(i);
    tick.setAttribute("role", "tab");
    tick.setAttribute("aria-label", slide.title);
    tick.addEventListener("click", () => show(i));
    ticksEl.append(tick);

    if (slide.act) {
      const label = document.createElement("p");
      label.className = "act";
      label.textContent = slide.act;
      indexBody.append(label);
    }
    const lesson = document.createElement("button");
    lesson.type = "button";
    lesson.className = "lesson";
    lesson.dataset.index = String(i);
    lesson.innerHTML = `<span class="num">${String(i + 1).padStart(2, "0")}</span><span>${slide.title}</span>`;
    lesson.addEventListener("click", () => {
      show(i);
      closeIndex();
    });
    indexBody.append(lesson);
  });
}

function openIndex() {
  index.hidden = false;
  document.querySelector("#index-close").focus();
}

function closeIndex() {
  index.hidden = true;
}

document.querySelector("#prev").addEventListener("click", () => show(indexAt - 1));
document.querySelector("#next").addEventListener("click", () => show(indexAt + 1));
document.querySelector("#index-close").addEventListener("click", closeIndex);
index.addEventListener("click", (event) => {
  if (event.target === index) closeIndex();
});

document.addEventListener("keydown", (event) => {
  const typing = event.target instanceof HTMLInputElement;
  if (typing) return;
  if (event.key === "ArrowRight" || event.key === " " || event.key === "PageDown") {
    event.preventDefault();
    show(indexAt + 1);
  } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
    event.preventDefault();
    show(indexAt - 1);
  } else if (event.key === "Home") {
    show(0);
  } else if (event.key === "End") {
    show(slides.length - 1);
  } else if (event.key === "i" || event.key === "I") {
    if (index.hidden) openIndex();
    else closeIndex();
  } else if (event.key === "Escape") {
    closeIndex();
  } else if (event.key === "f" || event.key === "F") {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }
});

window.addEventListener("hashchange", () => show(slideFromHash()));

let touchX = null;
frame.addEventListener("pointerdown", (event) => {
  if (event.pointerType === "touch") touchX = event.clientX;
});
frame.addEventListener("pointerup", (event) => {
  if (touchX == null || event.pointerType !== "touch") return;
  const delta = event.clientX - touchX;
  touchX = null;
  if (Math.abs(delta) < 48) return;
  show(indexAt + (delta < 0 ? 1 : -1));
});

function resizeLaser() {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(rect.width * dpr));
  canvas.height = Math.max(1, Math.round(rect.height * dpr));
}

function pointerToCanvas(event) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  return {
    x: (event.clientX - rect.left) * dpr,
    y: (event.clientY - rect.top) * dpr,
  };
}

frame.addEventListener("pointermove", (event) => {
  if (event.pointerType === "touch" && event.buttons === 0) return;
  const point = pointerToCanvas(event);
  const now = performance.now();
  pointing = true;
  head = point;
  const last = trail[trail.length - 1];
  const dx = last ? point.x - last.x : 0;
  const dy = last ? point.y - last.y : 0;
  const dist = Math.hypot(dx, dy);
  if (!last || dist > 1.5) {
    trail.push({ x: point.x, y: point.y, t: now });
    if (!reducedMotion && dist > 14) {
      const nx = dx / dist;
      const ny = dy / dist;
      sparks.push({
        x: point.x - nx * dist * 0.35,
        y: point.y - ny * dist * 0.35,
        vx: -nx * dist * 0.04 + (Math.random() - 0.5) * 1.4,
        vy: -ny * dist * 0.04 + (Math.random() - 0.5) * 1.4,
        t: now,
        life: 360 + Math.random() * 180,
      });
      if (sparks.length > 64) sparks.splice(0, sparks.length - 64);
    }
  }
});

frame.addEventListener("pointerleave", () => {
  pointing = false;
  head = null;
});

window.addEventListener("resize", resizeLaser);
if (window.ResizeObserver) new ResizeObserver(resizeLaser).observe(frame);

function drawLaser(now) {
  resizeIfNeeded();
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  trail = trail.filter((point) => now - point.t < TRAIL_MS);
  sparks = sparks.filter((spark) => now - spark.t < spark.life);

  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.globalCompositeOperation = "lighter";

  if (!reducedMotion) {
    for (let i = 1; i < trail.length; i += 1) {
      const a = trail[i - 1];
      const b = trail[i];
      const age = (now - b.t) / TRAIL_MS;
      const fade = (1 - age) ** 1.15;
      ctx.strokeStyle = `rgba(255, 64, 24, ${fade * 0.9})`;
      ctx.lineWidth = 6 + fade * 28;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();

      ctx.strokeStyle = `rgba(255, 236, 200, ${fade})`;
      ctx.lineWidth = 2 + fade * 7;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }

    for (const spark of sparks) {
      const age = (now - spark.t) / spark.life;
      const fade = 1 - age;
      const x = spark.x + spark.vx * age * 18;
      const y = spark.y + spark.vy * age * 18;
      ctx.fillStyle = `rgba(255, 186, 92, ${fade * 0.8})`;
      ctx.beginPath();
      ctx.arc(x, y, fade * 2.4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  if (pointing && head) {
    const radius = reducedMotion ? 8 : 34;
    const glow = ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, radius);
    glow.addColorStop(0, "rgba(255, 255, 245, 1)");
    glow.addColorStop(0.18, "rgba(255, 244, 214, 0.95)");
    glow.addColorStop(0.42, "rgba(255, 92, 36, 0.75)");
    glow.addColorStop(1, "rgba(255, 40, 16, 0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(head.x, head.y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.globalCompositeOperation = "source-over";
  requestAnimationFrame(drawLaser);
}

let sized = false;
function resizeIfNeeded() {
  if (sized) return;
  if (canvas.getBoundingClientRect().width > 0) {
    resizeLaser();
    sized = true;
  }
}

buildChrome();
show(indexAt);
requestAnimationFrame(drawLaser);
