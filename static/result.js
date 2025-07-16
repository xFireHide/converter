const copyBtn = document.getElementById("copy-link-btn");
copyBtn.addEventListener("click", function () {
  const downloadLinkEl = document.querySelector("a[download]");
  const link = downloadLinkEl
    ? downloadLinkEl.href
    : window.DOWNLOAD_LINK || window.location.href;

  navigator.clipboard
    .writeText(link)
    .then(() => alert("Link copiado!"))
    .catch(() => alert("Falha ao copiar link."));
});
