"use strict";

const API = {
  async listSlides() {
    const res = await fetch("/api/slides");
    if (!res.ok) throw new Error("Failed to list slides");
    return res.json();
  },

  async metadata(id) {
    const res = await fetch(`/api/slides/${encodeURIComponent(id)}/metadata`);
    if (!res.ok) throw new Error("Failed to load metadata");
    return res.json();
  },

  thumbnailUrl(id) {
    return `/api/slides/${encodeURIComponent(id)}/thumbnail`;
  },

  dziUrl(id) {
    return `/api/slides/${encodeURIComponent(id)}.dzi`;
  },

  // Upload with progress via XHR (fetch lacks upload progress events).
  upload(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/slides/upload");
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          let msg = "Upload failed";
          try { msg = JSON.parse(xhr.responseText).detail || msg; } catch (_) {}
          reject(new Error(msg));
        }
      };
      xhr.onerror = () => reject(new Error("Upload failed"));
      const form = new FormData();
      form.append("file", file);
      xhr.send(form);
    });
  },
};
