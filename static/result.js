document.getElementById("copy-link-btn").addEventListener("click", function () {
  navigator.clipboard
    .writeText(window.DOWNLOAD_LINK)
    .then(() => alert("Link copiado!"))
    .catch(() => alert("Falha ao copiar link."));
});
