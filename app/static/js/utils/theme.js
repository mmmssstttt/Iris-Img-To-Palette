function getStoredTheme() {
    try {
        const theme = localStorage.getItem("iris-theme");
        return theme === "light" ? "light" : "dark";
    } catch {
        return "dark";
    }
}

function applyTheme(theme) {
    const safeTheme = theme === "dark" ? "dark" : "light";
    const uploadArea = getUploadAreaElement();
    const previousUploadBackground = uploadArea ? String(window.getComputedStyle(uploadArea).background || "").trim() : "";

    document.documentElement.setAttribute("data-theme", safeTheme);
    try {
        localStorage.setItem("iris-theme", safeTheme);
    } catch {
        // ignore storage failures
    }

    if (uploadArea && previousUploadBackground) {
        const fadeLayer = document.createElement("div");
        fadeLayer.className = "iris-upload-theme-fade";
        fadeLayer.style.background = previousUploadBackground;
        uploadArea.insertBefore(fadeLayer, uploadArea.firstChild);
        requestAnimationFrame(() => {
            fadeLayer.style.opacity = "0";
        });
        window.setTimeout(() => {
            fadeLayer.remove();
        }, 720);
    }

    const uploaderData = getUploaderData();
    if (uploaderData) uploaderData.isDark = safeTheme === "dark";
}
