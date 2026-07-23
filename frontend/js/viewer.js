"use strict";

let viewer = null;
let activeId = null;

function initViewer() {
  viewer = OpenSeadragon({
    id: "viewer",
    prefixUrl: "https://cdn.jsdelivr.net/npm/openseadragon@5.0.1/build/openseadragon/images/",
    showNavigator: true,
    navigatorPosition: "TOP_RIGHT",
    showRotationControl: true,
    showFlipControl: true,
    gestureSettingsMouse: { clickToZoom: false, dblClickToZoom: true },
    gestureSettingsTouch: { pinchRotate: false },
    minZoomImageRatio: 0.8,
    maxZoomPixelRatio: 2,
    animationTime: 0.4,
    zoomPerScroll: 1.4,
    crossOriginPolicy: "Anonymous",
    imageLoaderLimit: 6,
  });
}

function setScalebar(mpp) {
  if (!viewer.scalebar) return;
  if (mpp && mpp > 0) {
    viewer.scalebar({
      type: OpenSeadragon.ScalebarType.MICROSCOPY,
      pixelsPerMeter: 1e6 / mpp, // mpp is microns/pixel -> pixels per meter
      location: OpenSeadragon.ScalebarLocation.BOTTOM_LEFT,
      xOffset: 12,
      yOffset: 12,
      stayInsideImage: false,
      color: "#ffffff",
      fontColor: "#ffffff",
      backgroundColor: "rgba(0,0,0,0.55)",
      barThickness: 3,
    });
  } else {
    // No MPP (e.g. plain JPEG): disable the scale bar.
    viewer.scalebar({ pixelsPerMeter: 0 });
  }
}

function renderMetadata(meta) {
  const section = document.getElementById("metadataSection");
  const dl = document.getElementById("metadata");
  section.hidden = false;
  const rows = [
    ["Name", meta.name],
    ["Format", (meta.format || "").toUpperCase()],
    ["Dimensions", `${meta.width.toLocaleString()} x ${meta.height.toLocaleString()} px`],
    ["MPP", meta.mpp ? `${meta.mpp.toFixed(4)} um/px` : "n/a"],
    ["Objective", meta.objective_power ? `${meta.objective_power}x` : "n/a"],
    ["Vendor", meta.vendor || "n/a"],
    ["Pyramid levels", meta.level_count],
  ];
  dl.innerHTML = rows
    .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`)
    .join("");
}

async function openSlide(id) {
  if (!viewer) initViewer();
  activeId = id;
  document.getElementById("placeholder").hidden = true;

  markActive(id);
  try {
    const meta = await API.metadata(id);
    renderMetadata(meta);
    viewer.open(API.dziUrl(id));
    viewer.addOnceHandler("open", () => setScalebar(meta.mpp));
  } catch (err) {
    alert(`Failed to open slide: ${err.message}`);
  }
}

function markActive(id) {
  document.querySelectorAll(".slide-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === id);
  });
}

async function refreshSlideList() {
  const list = document.getElementById("slideList");
  let slides = [];
  try {
    slides = await API.listSlides();
  } catch (_) {
    list.innerHTML = '<li class="empty">Could not load slides.</li>';
    return;
  }
  if (!slides.length) {
    list.innerHTML = '<li class="empty">No slides yet. Upload one above.</li>';
    return;
  }
  list.innerHTML = "";
  for (const s of slides) {
    const li = document.createElement("li");
    li.className = "slide-item";
    li.dataset.id = s.id;
    li.innerHTML = `
      <img src="${API.thumbnailUrl(s.id)}" alt="" loading="lazy" />
      <div class="meta">
        <div class="name" title="${s.name}">${s.name}</div>
        <div class="fmt">${s.format}</div>
      </div>`;
    li.addEventListener("click", () => openSlide(s.id));
    list.appendChild(li);
  }
  if (activeId) markActive(activeId);
}

function setupUpload() {
  const area = document.getElementById("uploadArea");
  const input = document.getElementById("fileInput");
  const progress = document.getElementById("uploadProgress");
  const bar = document.getElementById("uploadProgressBar");

  async function handleFile(file) {
    if (!file) return;
    progress.hidden = false;
    bar.style.width = "0%";
    try {
      const result = await API.upload(file, (frac) => {
        bar.style.width = `${Math.round(frac * 100)}%`;
      });
      await refreshSlideList();
      await openSlide(result.id);
    } catch (err) {
      alert(err.message);
    } finally {
      setTimeout(() => { progress.hidden = true; }, 600);
    }
  }

  area.addEventListener("click", () => input.click());
  input.addEventListener("change", () => handleFile(input.files[0]));

  ["dragenter", "dragover"].forEach((ev) =>
    area.addEventListener(ev, (e) => {
      e.preventDefault();
      area.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    area.addEventListener(ev, (e) => {
      e.preventDefault();
      area.classList.remove("dragover");
    })
  );
  area.addEventListener("drop", (e) => {
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
}

window.addEventListener("DOMContentLoaded", () => {
  initViewer();
  setupUpload();
  refreshSlideList();
});
