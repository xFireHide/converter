document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("upload-form");
  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");

  if (!form) return;

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    form.classList.add("hidden");
    progressContainer.classList.remove("hidden");

    // Começa a animar já!
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 8;
      if (progress >= 95) progress = 95; // Fica em 95% até resposta
      progressBar.style.width = progress + "%";
      progressText.textContent = Math.floor(progress) + "%";
    }, 200);

    const formData = new FormData(form);
    fetch(form.action, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        clearInterval(interval);
        progressBar.style.width = "100%";
        progressText.textContent = "100%";
        setTimeout(() => {
          if (response.redirected) {
            window.location.href = response.url;
          } else {
            location.reload();
          }
        }, 400);
      })
      .catch(() => {
        clearInterval(interval);
        alert("Erro ao enviar o arquivo.");
        form.classList.remove("hidden");
        progressContainer.classList.add("hidden");
      });
  });
});
