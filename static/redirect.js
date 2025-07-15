const form = document.getElementById("upload-form");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  form.classList.add("hidden");
  progressContainer.classList.remove("hidden");

  // Cria FormData e envia via fetch
  const formData = new FormData(form);
  const response = await fetch("/", {
    method: "POST",
    body: formData,
  });

  if (response.redirected) {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 10;
      if (progress >= 100) {
        clearInterval(interval);
        progressBar.style.width = "100%";
        progressText.textContent = "100%";
        setTimeout(() => {
          window.location.href = response.url;
        }, 500);
      } else {
        progressBar.style.width = progress + "%";
        progressText.textContent = Math.floor(progress) + "%";
      }
    }, 300);
  } else {
    alert("Erro ao enviar o arquivo.");
    form.classList.remove("hidden");
    progressContainer.classList.add("hidden");
  }
});
