// Upload interactions: drag-and-drop, preview, loading state, CAM tabs.
(function () {
  var dz = document.getElementById("dropzone");
  var input = document.getElementById("file-input");
  var nameEl = document.getElementById("file-name");
  var preview = document.getElementById("preview");
  var form = document.getElementById("upload-form");
  var loading = document.getElementById("loading");

  function showFile(file) {
    if (!file) return;
    if (nameEl) nameEl.textContent = file.name + " (" + Math.round(file.size / 1024) + " KB)";
    if (preview && file.type.startsWith("image/")) {
      preview.src = URL.createObjectURL(file);
      preview.hidden = false;
    }
  }

  if (dz && input) {
    dz.addEventListener("click", function (e) {
      if (e.target.tagName !== "BUTTON" && e.target.tagName !== "LABEL") input.click();
    });
    dz.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") input.click();
    });
    ["dragover", "dragenter"].forEach(function (ev) {
      dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.add("drag"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.remove("drag"); });
    });
    dz.addEventListener("drop", function (e) {
      var f = e.dataTransfer.files && e.dataTransfer.files[0];
      if (f) { input.files = e.dataTransfer.files; showFile(f); }
    });
    input.addEventListener("change", function () { showFile(input.files[0]); });
  }

  if (form) {
    form.addEventListener("submit", function () {
      if (loading) loading.hidden = false;
      var btn = document.getElementById("analyze-btn");
      if (btn) { btn.disabled = true; btn.textContent = "Analyzing…"; }
    });
  }

  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("active"); });
      tab.classList.add("active");
      document.querySelectorAll(".cam-img").forEach(function (img) { img.classList.remove("show"); });
      var target = document.getElementById("cam-" + tab.dataset.cam);
      if (target) target.classList.add("show");
    });
  });
})();
