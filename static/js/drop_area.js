const dropArea = document.getElementById("drop-area");
const fileElem = document.getElementById("fileElem");
const fileList = document.getElementById("fileList");

// Destaque visual ao arrastar
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

// Drop de arquivos
dropArea.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  handleFiles(files);
});

// Seleção manual
fileElem.addEventListener("change", (e) => {
  handleFiles(fileElem.files);
});

function handleFiles(files) {
  fileList.innerHTML = "";
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    fileList.innerHTML += `<p>📄 ${file.name} (${(file.size / 1024).toFixed(
      2
    )} KB)</p>`;
    // Aqui você pode enviar os arquivos via fetch ou AJAX
    // ex: uploadFile(file);
  }
}
