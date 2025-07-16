const form = document.getElementById("upload-form");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  form.classList.add("hidden");
  progressContainer.classList.remove("hidden");

  const formData = new FormData(form);
  const response = await fetch(form.action, {
    method: form.method,
    body: formData,
  });

  if (response.redirected) {
    let progress = 0;
    const interval = setInterval(() => {
      progress = Math.min(progress + Math.random() * 10, 100);
      progressBar.style.width = progress + "%";
      progressText.textContent = Math.floor(progress) + "%";
      if (progress === 100) {
        clearInterval(interval);
        setTimeout(() => (window.location.href = response.url), 300);
      }
    }, 200);
  } else {
    alert("Erro ao enviar o arquivo.");
    form.classList.remove("hidden");
    progressContainer.classList.add("hidden");
  }
});
