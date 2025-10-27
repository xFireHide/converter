function initShortenerResult() {
  const shortCode = window.SHORT_CODE || "";
  const shortUrl = window.SHORT_URL || window.location.href;
  const statsEndpoint =
    window.URL_STATS_ENDPOINT || (shortCode ? `/api/url/stats/${shortCode}` : "");

  const inputEl = document.getElementById("short-url-input");
  const copyBtn = document.getElementById("copy-short-url");
  const countEl = document.getElementById("click-count");
  const refreshBtn = document.getElementById("refresh-count");
  const updatedAtEl = document.querySelector("[data-updated-at]");
  const historyRows = Array.from(document.querySelectorAll("[data-short-code]"));
  const rowConfigs = historyRows.map((row) => ({
    code: row.dataset.shortCode,
    statsUrl: row.dataset.statsUrl || `/api/url/stats/${row.dataset.shortCode}`,
    countEl: row.querySelector("[data-count]"),
  }));
  const hasCurrentRow = rowConfigs.some((config) => config.code === shortCode);

  document.querySelectorAll("[data-copy-btn]").forEach((btn) => {
    const value = btn.getAttribute("data-copy-value") || "";
    btn.addEventListener("click", () => {
      if (!value) return;
      navigator.clipboard
        .writeText(value)
        .then(() => {
          const original = btn.textContent;
          btn.textContent = "Copiado!";
          setTimeout(() => {
            btn.textContent = original;
          }, 1500);
        })
        .catch(() => {
          alert("Não foi possível copiar o link.");
        });
    });
  });

  if (copyBtn && inputEl) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard
        .writeText(inputEl.value || shortUrl)
        .then(() => {
          copyBtn.textContent = "Copiado!";
          setTimeout(() => {
            copyBtn.textContent = "Copiar";
          }, 1500);
        })
        .catch(() => {
          alert("Não foi possível copiar o link.");
        });
    });
  }

  let pollingHandle = null;

  async function fetchStats(showError = false) {
    const tasks = [];

    if (statsEndpoint && !hasCurrentRow) {
      tasks.push(
        fetch(statsEndpoint, { cache: "no-store" })
          .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
          })
          .then((data) => {
            if (countEl && typeof data.click_count === "number") {
              countEl.textContent = data.click_count;
            }
            return data.click_count;
          })
      );
    }

    rowConfigs.forEach((config) => {
      tasks.push(
        fetch(config.statsUrl, { cache: "no-store" })
          .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
          })
          .then((data) => {
            if (config.countEl && typeof data.click_count === "number") {
              config.countEl.textContent = data.click_count;
              if (config.code === shortCode && countEl) {
                countEl.textContent = data.click_count;
              }
            }
          })
      );
    });

    if (!tasks.length) return;

    return Promise.all(tasks)
      .then(() => {
        if (updatedAtEl) {
          const now = new Date();
          updatedAtEl.textContent = now.toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
        }
      })
      .catch((error) => {
        if (showError) {
          console.error("Erro ao buscar estatísticas:", error);
          alert("Não foi possível atualizar o contador agora.");
        }
      });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      fetchStats(true);
    });
  }

  if (statsEndpoint || rowConfigs.length) {
    pollingHandle = setInterval(fetchStats, 5000);
    fetchStats();
  }

  window.addEventListener("beforeunload", () => {
    if (pollingHandle) {
      clearInterval(pollingHandle);
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initShortenerResult);
} else {
  initShortenerResult();
}
