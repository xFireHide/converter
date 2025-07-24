document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".drop-area").forEach((dropArea) => {
    const fileElem = dropArea.querySelector("input[type='file']");
    const fileList = dropArea.querySelector(".file-list");
    const button = dropArea.querySelector("button");

    if (!fileElem) return;

    if (button) {
      button.addEventListener("click", (e) => {
        e.preventDefault();
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
});

function handleFiles(files, fileInput, fileList) {
  const accept = fileInput.getAttribute("accept") || "";
  const allowed = accept
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
  const dt = new DataTransfer();
  fileList.innerHTML = "";
  Array.from(files).forEach((file) => {
    if (fileAccepted(file, allowed)) {
      dt.items.add(file);
      fileList.innerHTML += `<p>📄 ${file.name} (${(file.size / 1024).toFixed(
        2
      )} KB)</p>`;
    }
  });
  fileInput.files = dt.files;
}

function fileAccepted(file, allowed) {
  if (!allowed.length) return true;
  return allowed.some((type) => {
    if (type === "image/*") {
      return file.type.startsWith("image/");
    }
    if (type.startsWith(".")) {
      return file.name.toLowerCase().endsWith(type.toLowerCase());
    }
    return file.type === type;
  });
}
