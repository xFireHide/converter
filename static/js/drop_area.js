function initDropAreas() {
  document.querySelectorAll(".drop-area").forEach((dropArea) => {
    const fileElem = dropArea.querySelector("input[type='file']");
    const fileList = dropArea.querySelector(".file-list");
    const button = dropArea.querySelector("button");

    if (!fileElem) return;

    if (button) {
      button.addEventListener("click", (e) => {
        e.preventDefault();
        fileElem.value = "";
        fileElem.click();
      });
    }

    ["dragenter", "dragover"].forEach((eventName) => {
      dropArea.addEventListener(
        eventName,
        (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropArea.classList.add("hover");
        },
        false
      );
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropArea.addEventListener(
        eventName,
        (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropArea.classList.remove("hover");
        },
        false
      );
    });

    dropArea.addEventListener("drop", (e) => {
      handleFiles(e.dataTransfer.files, fileElem, fileList);
    });

    fileElem.addEventListener("change", () => {
      handleFiles(fileElem.files, fileElem, fileList);
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initDropAreas);
} else {
  initDropAreas();
}

function handleFiles(files, fileInput, fileList) {
  const accept = (fileInput.getAttribute("accept") || "").toLowerCase();
  const allowed = accept
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const dt = typeof DataTransfer === "undefined" ? null : new DataTransfer();
  const accepted = [];
  const rejected = [];

  fileList.innerHTML = "";

  Array.from(files).forEach((file) => {
    if (fileAccepted(file, allowed)) {
      accepted.push(file);
      if (dt) dt.items.add(file);
      fileList.innerHTML += `<p>📄 ${file.name} (${(file.size / 1024).toFixed(2)} KB)</p>`;
    } else {
      rejected.push(file.name);
    }
  });

  if (dt) {
    fileInput.files = dt.files;
  } else if (rejected.length) {
    // Fallback: limpa a seleção caso o navegador não suporte DataTransfer
    fileInput.value = "";
  }

  if (!accepted.length) {
    fileList.innerHTML = "<p class=\"file-warning\">Nenhum arquivo compatível selecionado.</p>";
  } else if (rejected.length) {
    fileList.innerHTML += `<p class="file-warning">Arquivos ignorados: ${rejected.join(", ")}</p>`;
  }
}

function fileAccepted(file, allowed) {
  if (!allowed.length) return true;
  const fileType = (file.type || "").toLowerCase();
  const fileName = (file.name || "").toLowerCase();

  return allowed.some((type) => {
    const rule = type.toLowerCase();
    if (rule.endsWith("/*")) {
      const base = rule.slice(0, rule.indexOf("/"));
      return fileType.startsWith(`${base}/`);
    }
    if (rule.startsWith(".")) {
      return fileName.endsWith(rule);
    }
    return fileType === rule;
  });
}
