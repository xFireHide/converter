const REDIRECT_URL = "/download/sucesso";

const form = document.getElementById("upload-form");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");

form.addEventListener("submit", function (event) {
  event.preventDefault();
  form.classList.add("hidden");
  progressContainer.classList.remove("hidden");

  let progress = 0;
  const interval = setInterval(() => {
    progress += Math.random() * 10;
    if (progress >= 100) {
      progress = 100;
      clearInterval(interval);
      progressBar.style.width = "100%";
      progressText.textContent = "100%";
      setTimeout(() => {
        window.location.href = REDIRECT_URL;
      }, 500);
    } else {
      progressBar.style.width = progress + "%";
      progressText.textContent = Math.floor(progress) + "%";
    }
  }, 300);
});
