document.addEventListener("DOMContentLoaded", function () {
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("xray_image");
    const previewImg = document.getElementById("previewImg");

    if (!dropZone || !fileInput) return;

    function showPreview(file) {
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            previewImg.classList.remove("d-none");
        };
        reader.readAsDataURL(file);
    }

    fileInput.addEventListener("change", function () {
        showPreview(fileInput.files[0]);
    });

    ["dragenter", "dragover"].forEach((evt) => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((evt) => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", function (e) {
        const files = e.dataTransfer.files;
        if (files && files.length) {
            fileInput.files = files;
            showPreview(files[0]);
        }
    });

    const form = document.getElementById("uploadForm");
    if (form) {
        form.addEventListener("submit", function () {
            const btn = form.querySelector("button[type=submit]");
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing...';
        });
    }
});
