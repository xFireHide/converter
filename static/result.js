const copyBtn = document.getElementById("copy-link-btn");
copyBtn.addEventListener("click", () => {
  const downloadEl = document.querySelector("a[download]");
  const link = downloadEl.href;
  navigator.clipboard
    .writeText(link)
    .then(() => alert("Link copiado!"))
    .catch(() => alert("Falha ao copiar link."));
});
