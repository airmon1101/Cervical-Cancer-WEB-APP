(() => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const dropzoneEmpty = document.getElementById("dropzoneEmpty");
  const dropzonePreview = document.getElementById("dropzonePreview");
  const previewImg = document.getElementById("previewImg");
  const scanline = document.getElementById("scanline");
  const fileNameEl = document.getElementById("fileName");
  const clearBtn = document.getElementById("clearBtn");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const analyzeLabel = document.getElementById("analyzeLabel");
  const statusDot = document.getElementById("statusDot");
  const readoutState = document.getElementById("readoutState");
  const readoutEmpty = document.getElementById("readoutEmpty");
  const readoutBody = document.getElementById("readoutBody");
  const readoutError = document.getElementById("readoutError");
  const verdictLabel = document.getElementById("verdictLabel");
  const verdictConf = document.getElementById("verdictConf");
  const verdictNote = document.getElementById("verdictNote");
  const bars = document.getElementById("bars");

  const NOTES = {
    Negative: "No malignant or pre-malignant features detected in this specimen.",
    Suspected: "Some atypical features were detected. Manual review is recommended.",
    Positive: "Features consistent with malignancy were detected. Refer for confirmation.",
  };

  const BAR_CLASS = {
    Negative: "negative",
    Suspected: "suspected",
    Positive: "positive",
  };

  let currentFile = null;

  function resetReadout() {
    readoutBody.hidden = true;
    readoutError.hidden = true;
    readoutEmpty.hidden = false;
    readoutState.textContent = "idle";
    statusDot.classList.remove("active");
  }

  function setFile(file) {
    if (!file) return;
    if (!/\.(png|jpe?g)$/i.test(file.name)) {
      showError("Please choose a PNG or JPG image.");
      return;
    }
    currentFile = file;
    fileNameEl.textContent = file.name;
    clearBtn.hidden = false;
    analyzeBtn.disabled = false;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      dropzoneEmpty.hidden = true;
      dropzonePreview.hidden = false;
    };
    reader.readAsDataURL(file);
    resetReadout();
  }

  function clearFile() {
    currentFile = null;
    fileInput.value = "";
    fileNameEl.textContent = "no file selected";
    clearBtn.hidden = true;
    analyzeBtn.disabled = true;
    dropzoneEmpty.hidden = false;
    dropzonePreview.hidden = true;
    scanline.classList.remove("running");
    resetReadout();
  }

  function showError(message) {
    readoutBody.hidden = true;
    readoutEmpty.hidden = true;
    readoutError.hidden = false;
    readoutError.textContent = message;
    readoutState.textContent = "error";
    statusDot.classList.remove("active");
  }

  function renderBars(probabilities) {
    bars.innerHTML = "";
    const order = ["Negative", "Suspected", "Positive"];
    order.forEach((label) => {
      const pct = (probabilities[label] ?? 0) * 100;
      const row = document.createElement("div");
      row.className = "bar-row";
      row.innerHTML = `
        <span class="bar-name">${label}</span>
        <div class="bar-track"><div class="bar-fill ${BAR_CLASS[label]}" style="width:0%"></div></div>
        <span class="bar-pct mono">${pct.toFixed(1)}%</span>
      `;
      bars.appendChild(row);
      requestAnimationFrame(() => {
        row.querySelector(".bar-fill").style.width = `${pct}%`;
      });
    });
  }

  async function analyze() {
    if (!currentFile) return;

    analyzeBtn.disabled = true;
    analyzeLabel.textContent = "Analyzing...";
    scanline.classList.add("running");
    statusDot.classList.add("active");
    readoutState.textContent = "scanning";
    readoutEmpty.hidden = true;
    readoutError.hidden = true;
    readoutBody.hidden = true;

    const formData = new FormData();
    formData.append("file", currentFile);

    try {
      const res = await fetch("/predict", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Something went wrong analyzing this image.");
      }

      verdictLabel.textContent = data.label;
      verdictLabel.style.color =
        data.label === "Negative" ? "var(--sage)" :
        data.label === "Suspected" ? "var(--amber)" : "var(--brick)";
      verdictConf.textContent = `${(data.confidence * 100).toFixed(1)}% confidence`;
      verdictNote.textContent = NOTES[data.label] || "";
      renderBars(data.probabilities);

      readoutBody.hidden = false;
      readoutState.textContent = "complete";
    } catch (err) {
      showError(err.message || "Could not reach the analysis server.");
    } finally {
      scanline.classList.remove("running");
      statusDot.classList.remove("active");
      analyzeBtn.disabled = false;
      analyzeLabel.textContent = "Analyze specimen";
    }
  }

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => setFile(e.target.files[0]));

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    setFile(file);
  });

  clearBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });

  analyzeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    analyze();
  });
})();
