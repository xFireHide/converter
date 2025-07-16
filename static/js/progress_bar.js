// static/js/progress_bar.js
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("upload-form");
  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");

  if (!form) return; // Segurança

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    form.classList.add("hidden");
    progressContainer.classList.remove("hidden");

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 18;
          if (progress >= 100) {
            clearInterval(interval);
            progressBar.style.width = "100%";
            progressText.textContent = "100%";
            setTimeout(() => {
              // Redireciona se for redirect
              if (response.redirected) {
                window.location.href = response.url;
              } else {
                location.reload();
              }
            }, 400);
          } else {
            progressBar.style.width = progress + "%";
            progressText.textContent = Math.floor(progress) + "%";
          }
        }, 220);
      })
      .catch(() => {
        alert("Erro ao enviar o arquivo.");
        form.classList.remove("hidden");
        progressContainer.classList.add("hidden");
      });
  });
});
