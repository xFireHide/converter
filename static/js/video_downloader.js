document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("downloader-form");
  if (!form) return;

  const feedback = document.getElementById("downloader-feedback");
  const resultCard = document.getElementById("downloader-result");
  const resultTitle = document.getElementById("result-title");
  const resultDownload = document.getElementById("result-download");
  const resultPage = document.getElementById("result-page");

  const showMessage = (message, type = "info") => {
    if (!feedback) return;
    feedback.textContent = message;
    feedback.classList.remove("alert-success", "alert-danger", "alert-info");
    feedback.classList.add(`alert-${type}`);
    feedback.hidden = false;
  };

  const hideMessage = () => {
    if (!feedback) return;
    feedback.hidden = true;
  };

  const showResult = ({ title, downloadUrl, pageUrl }) => {
    if (!resultCard || !resultDownload || !resultPage) return;
    if (resultTitle) {
      resultTitle.textContent = title || "";
      resultTitle.hidden = !title;
    }
    resultDownload.href = downloadUrl;
    resultPage.href = pageUrl;
    resultCard.hidden = false;
  };

  const hideResult = () => {
    if (!resultCard) return;
    resultCard.hidden = true;
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage();
    hideResult();

    const submitBtn = form.querySelector("button[type='submit']");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.dataset.originalText = submitBtn.textContent;
      submitBtn.textContent = "…";
    }

    const urlField = form.querySelector("input[name='url']");
    const formatField = form.querySelector("input[name='format']:checked");
    const csrfField = form.querySelector("input[name='csrf_token']");

    const payload = {
      url: urlField ? urlField.value.trim() : "",
      format: formatField ? formatField.value : "mp4",
    };

    try {
      const response = await fetch("/api/video/download", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfField ? { "X-CSRFToken": csrfField.value } : {}),
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (!response.ok || result.status !== "success") {
        throw new Error(result.message || "Não foi possível processar o download.");
      }

      showResult({
        title: result.title || "",
        downloadUrl: result.download_url,
        pageUrl: result.page_url,
      });

      showMessage("Download preparado com sucesso!", "success");

      if (urlField) urlField.value = "";
    } catch (error) {
      console.error(error);
      showMessage(error.message || "Erro inesperado ao baixar o vídeo.", "danger");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = submitBtn.dataset.originalText || "Baixar";
        delete submitBtn.dataset.originalText;
      }
    }
  });
});

