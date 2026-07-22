/* FireConverter — client-side batch file conversion.
   Images: Canvas API · PDF: pdf.js · Audio/Video: ffmpeg.wasm (self-hosted). */

"use strict";

// ---------------------------------------------------------------------------
// Format registry
// ---------------------------------------------------------------------------

const KINDS = {
  image: {
    exts: ["png", "jpg", "jpeg", "webp", "gif", "bmp", "svg", "avif", "ico", "tif", "tiff"],
    formats: { png: "PNG", jpg: "JPG", webp: "WEBP", ico: "ICO" },
    default: "png",
  },
  audio: {
    exts: ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma", "aiff", "aif"],
    formats: { mp3: "MP3", wav: "WAV", ogg: "OGG", opus: "OPUS", flac: "FLAC", m4a: "M4A (AAC)" },
    default: "mp3",
  },
  video: {
    exts: ["mp4", "mov", "mkv", "avi", "webm", "m4v", "mpg", "mpeg", "wmv", "flv", "ts"],
    formats: { mp4: "MP4", webm: "WEBM", mov: "MOV", gif: "GIF", mp3: "MP3 (audio only)" },
    default: "mp4",
  },
  pdf: {
    exts: ["pdf"],
    formats: { png: "PNG (per page)", jpg: "JPG (per page)", webp: "WEBP (per page)" },
    default: "png",
  },
};

function detectKind(name) {
  const ext = name.split(".").pop().toLowerCase();
  for (const [kind, def] of Object.entries(KINDS)) {
    if (def.exts.includes(ext)) return kind;
  }
  return null;
}

// ---------------------------------------------------------------------------
// State + DOM
// ---------------------------------------------------------------------------

const state = []; // { id, file, kind, format, status, result: {blob, name} }
let nextId = 1;

const $ = (sel) => document.querySelector(sel);
const dropzone = $("#dropzone");
const fileInput = $("#file-input");
const fileList = $("#file-list");
const toolbar = $("#toolbar");
const masterFormat = $("#master-format");
const convertAllBtn = $("#convert-all");
const downloadAllBtn = $("#download-all");
const clearAllBtn = $("#clear-all");
const ffmpegNote = $("#ffmpeg-note");

pdfjsLib.GlobalWorkerOptions.workerSrc = "vendor/pdfjs/pdf.worker.min.js";

// ---------------------------------------------------------------------------
// File intake
// ---------------------------------------------------------------------------

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") fileInput.click();
});
fileInput.addEventListener("change", () => {
  addFiles(fileInput.files);
  fileInput.value = "";
});
["dragover", "dragenter"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);
dropzone.addEventListener("drop", (e) => addFiles(e.dataTransfer.files));

function addFiles(files) {
  for (const file of files) {
    const kind = detectKind(file.name);
    if (!kind) continue;
    state.push({ id: nextId++, file, kind, format: KINDS[kind].default, status: "ready", result: null });
  }
  render();
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function humanSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function formatOptions(kind, selected) {
  return Object.entries(KINDS[kind].formats)
    .map(([v, label]) => `<option value="${v}" ${v === selected ? "selected" : ""}>${label}</option>`)
    .join("");
}

function render() {
  toolbar.hidden = state.length === 0;
  fileList.innerHTML = "";

  // Master select: union of formats across kinds present
  const kindsPresent = [...new Set(state.map((it) => it.kind))];
  const seen = new Set();
  masterFormat.innerHTML = kindsPresent
    .flatMap((k) => Object.entries(KINDS[k].formats))
    .filter(([v]) => !seen.has(v) && seen.add(v))
    .map(([v, label]) => `<option value="${v}">${label}</option>`)
    .join("");

  for (const item of state) {
    const li = document.createElement("li");
    li.dataset.id = item.id;
    const statusCls = item.status === "done" ? "ok" : item.status === "error" ? "err" : "";
    const statusTxt = { ready: "Ready", converting: "Converting…", done: "Done ✓", error: item.error || "Error" }[item.status];
    li.innerHTML = `
      <div class="f-info">
        <div class="f-name" title="${item.file.name}">${item.file.name}</div>
        <div class="f-meta"><span class="kind-badge">${item.kind}</span>${humanSize(item.file.size)}</div>
      </div>
      <select class="row-format">${formatOptions(item.kind, item.format)}</select>
      <span class="f-status ${statusCls}">${statusTxt}</span>
      ${item.result
        ? `<a class="dl-link" download="${item.result.name}">Download</a>`
        : `<button class="remove-btn" title="Remove">✕</button>`}
      <div class="progress"><div class="progress-bar"></div></div>
    `;
    li.querySelector(".row-format").addEventListener("change", (e) => {
      item.format = e.target.value;
      item.status = "ready";
      item.result = null;
      render();
    });
    const rm = li.querySelector(".remove-btn");
    if (rm) rm.addEventListener("click", () => {
      state.splice(state.indexOf(item), 1);
      render();
    });
    const dl = li.querySelector(".dl-link");
    if (dl) dl.href = URL.createObjectURL(item.result.blob);
    fileList.appendChild(li);
  }

  downloadAllBtn.hidden = !state.some((it) => it.result);
}

function rowEls(item) {
  const li = fileList.querySelector(`li[data-id="${item.id}"]`);
  return { li, status: li?.querySelector(".f-status"), bar: li?.querySelector(".progress-bar"), prog: li?.querySelector(".progress") };
}

function setProgress(item, ratio) {
  const { prog, bar } = rowEls(item);
  if (!prog) return;
  prog.classList.add("active");
  bar.style.width = Math.round(Math.min(1, Math.max(0, ratio)) * 100) + "%";
}

// ---------------------------------------------------------------------------
// Master controls
// ---------------------------------------------------------------------------

masterFormat.addEventListener("change", () => {
  const fmt = masterFormat.value;
  for (const item of state) {
    if (fmt in KINDS[item.kind].formats) {
      item.format = fmt;
      item.status = "ready";
      item.result = null;
    }
  }
  render();
});

clearAllBtn.addEventListener("click", () => {
  state.length = 0;
  render();
});

convertAllBtn.addEventListener("click", async () => {
  convertAllBtn.disabled = true;
  try {
    for (const item of state) {
      if (item.status === "done") continue;
      await convertItem(item);
    }
  } finally {
    convertAllBtn.disabled = false;
    render();
  }
});

downloadAllBtn.addEventListener("click", async () => {
  const zip = new JSZip();
  for (const item of state) {
    if (item.result) zip.file(item.result.name, item.result.blob);
  }
  const blob = await zip.generateAsync({ type: "blob" });
  triggerDownload(blob, "converted.zip");
});

function triggerDownload(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

function baseName(name) {
  return name.replace(/\.[^.]+$/, "");
}

// ---------------------------------------------------------------------------
// Conversion dispatch
// ---------------------------------------------------------------------------

async function convertItem(item) {
  item.status = "converting";
  item.result = null;
  render();
  try {
    let result;
    if (item.kind === "image") result = await convertImage(item);
    else if (item.kind === "pdf") result = await convertPdf(item);
    else result = await convertMedia(item);
    item.result = result;
    item.status = "done";
  } catch (err) {
    console.error("[FireConverter]", item.file.name, err);
    item.status = "error";
    item.error = "Failed: " + (err && err.message ? err.message : "unsupported file");
  }
  render();
}

// ---------------------------------------------------------------------------
// Images (Canvas)
// ---------------------------------------------------------------------------

async function decodeToCanvas(file) {
  let source, w, h;
  const ext = file.name.split(".").pop().toLowerCase();
  if (ext === "svg") {
    source = await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("could not decode SVG"));
      img.src = URL.createObjectURL(file);
    });
    w = source.naturalWidth || 512;
    h = source.naturalHeight || 512;
  } else {
    source = await createImageBitmap(file).catch(() => {
      throw new Error("browser cannot decode this image format");
    });
    w = source.width;
    h = source.height;
  }
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  canvas.getContext("2d").drawImage(source, 0, 0, w, h);
  return canvas;
}

function canvasToBlob(canvas, mime, quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("encoding failed"))), mime, quality);
  });
}

async function convertImage(item) {
  const canvas = await decodeToCanvas(item.file);
  const fmt = item.format;
  const name = baseName(item.file.name) + "." + fmt;

  if (fmt === "ico") return { blob: await canvasToIco(canvas), name };

  if (fmt === "jpg") {
    // Flatten transparency onto white for JPEG.
    const flat = document.createElement("canvas");
    flat.width = canvas.width;
    flat.height = canvas.height;
    const ctx = flat.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, flat.width, flat.height);
    ctx.drawImage(canvas, 0, 0);
    return { blob: await canvasToBlob(flat, "image/jpeg", 0.92), name };
  }

  const mime = { png: "image/png", webp: "image/webp" }[fmt];
  return { blob: await canvasToBlob(canvas, mime, 0.92), name };
}

async function canvasToIco(canvas) {
  // Fit into a 256x256 square (PNG-in-ICO, supported since Vista).
  const size = 256;
  const scale = Math.min(size / canvas.width, size / canvas.height, 1);
  const w = Math.max(1, Math.round(canvas.width * scale));
  const h = Math.max(1, Math.round(canvas.height * scale));
  const sq = document.createElement("canvas");
  sq.width = size;
  sq.height = size;
  sq.getContext("2d").drawImage(canvas, (size - w) / 2, (size - h) / 2, w, h);

  const png = new Uint8Array(await (await canvasToBlob(sq, "image/png")).arrayBuffer());
  const out = new Uint8Array(22 + png.length);
  const dv = new DataView(out.buffer);
  dv.setUint16(0, 0, true);            // reserved
  dv.setUint16(2, 1, true);            // type: icon
  dv.setUint16(4, 1, true);            // count
  out[6] = 0;                          // width  (0 = 256)
  out[7] = 0;                          // height (0 = 256)
  dv.setUint16(10, 1, true);           // color planes
  dv.setUint16(12, 32, true);          // bits per pixel
  dv.setUint32(14, png.length, true);  // data size
  dv.setUint32(18, 22, true);          // data offset
  out.set(png, 22);
  return new Blob([out], { type: "image/x-icon" });
}

// ---------------------------------------------------------------------------
// PDF (pdf.js) — one image per page; multi-page results are zipped
// ---------------------------------------------------------------------------

async function convertPdf(item) {
  const data = await item.file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data }).promise;
  const fmt = item.format;
  const mime = { png: "image/png", jpg: "image/jpeg", webp: "image/webp" }[fmt];
  const base = baseName(item.file.name);
  const pages = [];

  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const viewport = page.getViewport({ scale: 2 });
    const canvas = document.createElement("canvas");
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    const ctx = canvas.getContext("2d");
    if (fmt === "jpg") {
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    // intent "print" avoids requestAnimationFrame, which stalls in background tabs
    await page.render({ canvasContext: ctx, viewport, intent: "print" }).promise;
    pages.push(await canvasToBlob(canvas, mime, 0.92));
    setProgress(item, i / pdf.numPages);
  }

  if (pages.length === 1) return { blob: pages[0], name: `${base}.${fmt}` };

  const zip = new JSZip();
  const pad = String(pages.length).length;
  pages.forEach((blob, i) => zip.file(`${base}_page${String(i + 1).padStart(pad, "0")}.${fmt}`, blob));
  return { blob: await zip.generateAsync({ type: "blob" }), name: `${base}_${fmt}.zip` };
}

// ---------------------------------------------------------------------------
// Audio / Video (ffmpeg.wasm)
// ---------------------------------------------------------------------------

let ffmpegInstance = null;
let ffmpegLoading = null;

async function getFFmpeg() {
  if (ffmpegInstance) return ffmpegInstance;
  if (!ffmpegLoading) {
    ffmpegNote.hidden = false;
    const { FFmpeg } = FFmpegWASM;
    const ffmpeg = new FFmpeg();
    ffmpegLoading = ffmpeg
      .load({
        coreURL: new URL("vendor/ffmpeg/ffmpeg-core.js", location.href).href,
        wasmURL: new URL("vendor/ffmpeg/ffmpeg-core.wasm", location.href).href,
      })
      .then(() => {
        ffmpegNote.hidden = true;
        ffmpegInstance = ffmpeg;
        return ffmpeg;
      })
      .catch((err) => {
        ffmpegNote.hidden = true;
        ffmpegLoading = null;
        throw err;
      });
  }
  return ffmpegLoading;
}

const MEDIA_ARGS = {
  mp3:  ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"],
  wav:  ["-vn", "-c:a", "pcm_s16le"],
  ogg:  ["-vn", "-c:a", "libvorbis", "-q:a", "5"],
  opus: ["-vn", "-c:a", "libopus", "-b:a", "128k"],
  flac: ["-vn", "-c:a", "flac"],
  m4a:  ["-vn", "-c:a", "aac", "-b:a", "192k"],
  mp4:  ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"],
  webm: ["-c:v", "libvpx", "-crf", "10", "-b:v", "1M", "-c:a", "libvorbis"],
  mov:  ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"],
  gif:  ["-vf", "fps=12,scale=480:-1:flags=lanczos", "-loop", "0"],
};

const MEDIA_MIME = {
  mp3: "audio/mpeg", wav: "audio/wav", ogg: "audio/ogg", opus: "audio/ogg",
  flac: "audio/flac", m4a: "audio/mp4", mp4: "video/mp4", webm: "video/webm",
  mov: "video/quicktime", gif: "image/gif",
};

async function convertMedia(item) {
  const ffmpeg = await getFFmpeg();
  const fmt = item.format;
  const inExt = item.file.name.split(".").pop().toLowerCase();
  const inName = "in." + inExt;
  const outName = "out." + fmt;

  const onProgress = ({ progress }) => setProgress(item, progress);
  ffmpeg.on("progress", onProgress);
  try {
    await ffmpeg.writeFile(inName, await FFmpegUtil.fetchFile(item.file));
    const code = await ffmpeg.exec(["-i", inName, ...MEDIA_ARGS[fmt], "-y", outName]);
    if (code !== 0) throw new Error("ffmpeg exited with code " + code);
    const out = await ffmpeg.readFile(outName);
    return {
      blob: new Blob([out.buffer], { type: MEDIA_MIME[fmt] }),
      name: baseName(item.file.name) + "." + fmt,
    };
  } finally {
    ffmpeg.off("progress", onProgress);
    await ffmpeg.deleteFile(inName).catch(() => {});
    await ffmpeg.deleteFile(outName).catch(() => {});
  }
}
