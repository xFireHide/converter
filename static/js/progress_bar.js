function initProgress() {
  const form = document.getElementById("upload-form");
  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");

  if (!form) return;

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    form.classList.add("hidden");
    progressContainer.classList.remove("hidden");
    progressContainer.classList.add("active");
    progressBar.style.width = "0%";
    progressText.textContent = "0%";

    const action = form.getAttribute("action") || window.location.href;
    const method = form.getAttribute("method") || "POST";

    const xhr = new XMLHttpRequest();
    xhr.open(method, action);
    xhr.withCredentials = true;

    xhr.upload.addEventListener("progress", function (e) {
      if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        progressBar.style.width = percent + "%";
        progressText.textContent = Math.floor(percent) + "%";
      }
    });

    xhr.addEventListener("load", function () {
      progressBar.style.width = "100%";
      progressText.textContent = "100%";

      if (xhr.status >= 200 && xhr.status < 400) {
        setTimeout(() => {
          window.location.href = xhr.responseURL;
        }, 300);
      } else {
        alert("Erro ao enviar o arquivo.");
        form.classList.remove("hidden");
        progressContainer.classList.add("hidden");
        progressContainer.classList.remove("active");
      }
    });

    xhr.addEventListener("error", function () {
      alert("Erro ao enviar o arquivo.");
      form.classList.remove("hidden");
      progressContainer.classList.add("hidden");
      progressContainer.classList.remove("active");
    });

    xhr.send(new FormData(form));
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initProgress);
