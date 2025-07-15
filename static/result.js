document.getElementById("copy-link-btn").addEventListener("click", function () {
  // `window.DOWNLOAD_LINK` será definido inline no HTML
  navigator.clipboard
    .writeText(window.DOWNLOAD_LINK)
    .then(() => alert("Link copiado!"))
    .catch(() => alert("Falha ao copiar link."));
});
