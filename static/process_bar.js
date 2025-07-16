const form = document.getElementById("upload-form");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

form.addEventListener("submit", function (event) {
  event.preventDefault();

  const formData = new FormData(form);

  form.classList.add("hidden");
  progressContainer.classList.remove("hidden");

  fetch(form.action, {
    // Usa a action definida no form HTML
    method: "POST",
    body: formData,
  })
    .then((response) => {
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
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${Math.floor(progress)}%`;
          }
        }, 300);
      } else {
        response.text().then((text) => {
          alert(`Erro ao enviar o arquivo: ${text}`);
        });
        form.classList.remove("hidden");
        progressContainer.classList.add("hidden");
      }
    })
    .catch((err) => {
      alert(`Erro ao enviar o arquivo: ${err}`);
      form.classList.remove("hidden");
      progressContainer.classList.add("hidden");
    });
});
