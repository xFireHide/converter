function initProgress() {
  console.log("initProgress function called - ENABLED");
  // Habilitado para o novo design
  
  const form = document.getElementById("upload-form");
  console.log("initProgress: form", form);

  if (!form) {
    console.warn(
      "Upload form not found. Skipping progress bar initialization."
    );
    return;
  }

  form.addEventListener("submit", function (event) {
    console.log("=== FORM SUBMIT EVENT TRIGGERED ===");
    
    // Verifica se há um arquivo selecionado
    const fileInput = form.querySelector('input[type="file"]');
    console.log("File input:", fileInput);
    console.log("Files:", fileInput?.files);
    console.log("Files length:", fileInput?.files?.length);
    
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      console.log("No file selected, allowing normal form submission");
      return; // Deixa o formulário ser submetido normalmente para mostrar erro
    }

    console.log("File selected:", fileInput.files[0].name);
    event.preventDefault();

    // Obter elementos de progresso dinamicamente (caso existam)
    const progressContainer =
      form.closest(".card")?.querySelector(".progress-container") ||
      document.querySelector(".progress-container");
    const progressTextEl =
      progressContainer?.querySelector("#progress-text") ||
      progressContainer?.querySelector("[data-progress-text]");
    const progressFillEl =
      progressContainer?.querySelector(".progress-fill") ||
      progressContainer?.querySelector("[data-progress-fill]");

    if (progressContainer) {
      form.classList.add("hidden");
      progressContainer.classList.remove("hidden");
      progressContainer.classList.add("active");
      if (progressFillEl) {
        progressFillEl.style.width = "0%";
      }
      if (progressTextEl) {
        progressTextEl.textContent = "0%";
      }
    }

    // Simular progresso
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += Math.random() * 20;
      if (progress > 90) progress = 90;
      if (progressFillEl) {
        progressFillEl.style.width = progress + "%";
      }
      if (progressTextEl) {
        progressTextEl.textContent = Math.floor(progress) + "%";
      }
    }, 100);

    // Enviar formulário
    const formData = new FormData(form);
    const action = form.getAttribute("action") || window.location.href;
    
    console.log("Sending form to:", action);
    
    fetch(action, {
      method: "POST",
      body: formData,
      credentials: "include",
    })
      .then(async (response) => {
        console.log("Response received:", response.status, response.url);

        clearInterval(progressInterval);
        if (progressFillEl) {
          progressFillEl.style.width = "100%";
        }
        if (progressTextEl) {
          progressTextEl.textContent = "100%";
        }

        const contentType = response.headers.get("content-type") || "";
        let payload = null;
        if (contentType.includes("application/json")) {
          try {
            payload = await response.json();
          } catch (err) {
            console.warn("Falha ao decodificar JSON da resposta.", err);
          }
        } else {
          try {
            payload = await response.text();
          } catch (err) {
            console.warn("Falha ao ler resposta como texto.", err);
          }
        }

        if (!response.ok) {
          const message =
            payload &&
            typeof payload === "object" &&
            payload !== null &&
            "message" in payload
              ? payload.message
              : `HTTP ${response.status}`;
          throw new Error(message);
        }

        if (payload && typeof payload === "object") {
          const redirectUrl =
            payload.redirect_url ||
            payload.result_url ||
            payload.download_url ||
            payload.url;

          const actionPath = action.toLowerCase();
          if (payload.file && typeof payload.file === "string") {
            if (actionPath.includes("/api/doc/pdf/")) {
              window.location.href = `/pdf_divisor/result/${encodeURIComponent(payload.file)}`;
              return;
            }
            if (actionPath.includes("/api/image/background/")) {
              const params = new URLSearchParams({ target: payload.target_format || "" });
              window.location.href = `/background_remover/result/${encodeURIComponent(payload.file)}?${params}`;
              return;
            }
            if (actionPath.includes("/api/audio/convert")) {
              window.location.href = `/audio_converter/result/${encodeURIComponent(payload.file)}`;
              return;
            }
            if (actionPath.includes("/api/video/convert")) {
              window.location.href = `/video_converter/result/${encodeURIComponent(payload.file)}`;
              return;
            }
          }

          if (!redirectUrl && Array.isArray(payload.converted)) {
            const firstUrl = payload.converted[0] && payload.converted[0].url;
            if (firstUrl) {
              window.location.href = firstUrl;
              return;
            }
          }

          if (redirectUrl) {
            window.location.href = redirectUrl;
            return;
          }

          if (payload.status === "success") {
            window.location.reload();
            return;
          }

          throw new Error(payload.message || "Resposta inesperada do servidor.");
        }

        window.location.reload();
      })
      .catch((error) => {
        console.error("Error:", error);
        clearInterval(progressInterval);
        alert("Erro: " + error.message);
        form.classList.remove("hidden");
        if (progressContainer) {
          progressContainer.classList.add("hidden");
          progressContainer.classList.remove("active");
        }
      });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initProgress);
} else {
  initProgress();
}
