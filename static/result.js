// static/result.js

// Copia o link de download do PDF para a área de transferência
// Busca diretamente o href do botão de download para garantir que é a URL correta
const copyBtn = document.getElementById("copy-link-btn");
copyBtn.addEventListener("click", function () {
  // Seleciona o link de download (elemento <a> com atributo download)
  const downloadLinkEl = document.querySelector("a[download]");
  const link = downloadLinkEl
    ? downloadLinkEl.href
    : window.DOWNLOAD_LINK || window.location.href;

  navigator.clipboard
    .writeText(link)
    .then(() => alert("Link copiado!"))
    .catch(() => alert("Falha ao copiar link."));
});
