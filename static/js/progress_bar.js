// Exemplo de progress_bar.js
const form = document.getElementById("upload-form");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

if (form) {
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    form.classList.add("hidden");
    progressContainer.classList.remove("hidden");

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 20;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        progressBar.style.width = "100%";
        progressText.textContent = "100%";
        setTimeout(() => {
          form.submit(); // Agora envia de verdade!
        }, 600);
      } else {
        progressBar.style.width = progress + "%";
        progressText.textContent = Math.floor(progress) + "%";
      }
    }, 200);
  });
}
