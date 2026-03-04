const MAX_FILES_PER_BATCH = 1000;

function isTouchDevice() {
    return window.matchMedia("(hover: none)").matches || "ontouchstart" in window;
}

function getUploadAreaElement() {
    return document.getElementById("upload-area");
}

function getUploaderData() {
    const uploaderRoot = document.querySelector("[x-data]");
    return uploaderRoot?._x_dataStack?.[0];
}

function applySwatchTextContrast(root = document) {
    const swatches = root.querySelectorAll(".palette-swatch[data-hex]");
    swatches.forEach((swatch) => {
        const label = swatch.querySelector(".palette-label");
        if (!label) return;
        label.style.color = "#E0E0E0";
        label.style.backgroundImage = "none";
        label.style.webkitBackgroundClip = "initial";
        label.style.backgroundClip = "initial";
        label.style.textShadow = "0 1px 0 rgba(41, 41, 41, 0.6), 1px 1px 0 rgba(41, 41, 41, 0.45)";
    });
}

function showTransientNotice(message) {
    const text = String(message || "").trim();
    if (!text) return;

    const existing = document.querySelector(".iris-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "iris-toast";
    toast.textContent = text;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add("show");
    });
    window.setTimeout(() => {
        toast.classList.remove("show");
        window.setTimeout(() => toast.remove(), 220);
    }, 1200);
}

function getDefaultUploadGradient() {
    return "linear-gradient(120deg, var(--primary-color) 30%, var(--mid-band) 30% 70%, var(--primary-color) 70%)";
}

function setUploadAreaBackground(nextBackground) {
    const uploadArea = getUploadAreaElement();
    if (!uploadArea) return;

    const next = String(nextBackground || "").trim();
    const currentInline = String(uploadArea.style.background || "").trim();
    const currentComputed = String(window.getComputedStyle(uploadArea).background || "").trim();
    const previous = currentInline || currentComputed;

    uploadArea.querySelectorAll(".iris-upload-gradient-fade").forEach((node) => node.remove());

    if (!previous || previous === next) {
        uploadArea.style.background = next;
        return;
    }

    const fadeLayer = document.createElement("div");
    fadeLayer.className = "iris-upload-gradient-fade";
    fadeLayer.style.background = previous;
    uploadArea.insertBefore(fadeLayer, uploadArea.firstChild);

    uploadArea.style.background = next;
    requestAnimationFrame(() => {
        fadeLayer.style.opacity = "0";
    });
    window.setTimeout(() => {
        fadeLayer.remove();
    }, 320);
}

function resetUploadAreaBackground() {
    setUploadAreaBackground(getDefaultUploadGradient());
}

function readPaletteDataFromDom(root = document) {
    const node = root.querySelector("#palettes-data");
    if (!node) return null;
    try {
        const parsed = JSON.parse(node.textContent || "[]");
        return Array.isArray(parsed) ? parsed : null;
    } catch {
        return null;
    }
}

function renderPaletteGrid(container, palette, targetCount = 10, options = {}) {
    if (!container) return;
    const commit = Boolean(options.commit);
    const keepAtLeast = Math.max(0, Number(options.keepAtLeast || 0));
    const fadeMs = 300;
    const sourceColors = Array.isArray(palette) ? palette : [];
    const colors = sourceColors.slice(0, targetCount);
    const baseTarget = Math.max(1, targetCount);
    const previewTarget = Math.max(baseTarget, sourceColors.length);
    const keepCount = commit ? Math.max(baseTarget, keepAtLeast) : Math.max(previewTarget, keepAtLeast);
    const finalCount = commit ? baseTarget : previewTarget;

    while (container.children.length < keepCount) {
        const node = document.createElement("div");
        node.className = "h-16 sm:h-22 rounded-xl iris-swatch-empty iris-swatch-fade-in";
        container.appendChild(node);
        window.setTimeout(() => node.classList.remove("iris-swatch-fade-in"), fadeMs);
    }

    for (let i = 0; i < keepCount; i += 1) {
        const node = container.children[i];
        if (!(node instanceof HTMLElement)) continue;

        if (i < baseTarget && i < colors.length) {
            const hex = String(colors[i]?.hex || "");
            const text = hex.replace("#", "").toUpperCase();
            node.className = "palette-swatch flex h-16 sm:h-22 min-w-0 items-center justify-center rounded-xl px-2 text-center text-lg tracking-wide iris-shadow-main";
            node.setAttribute("data-hex", hex);
            node.style.setProperty("--swatch-left", hex);
            node.innerHTML = `<span class="palette-label">${text}</span>`;
            node.classList.remove("iris-swatch-dim", "iris-swatch-fade-out");
        } else if (i < baseTarget) {
            node.className = "h-16 sm:h-22 rounded-xl iris-swatch-empty";
            node.removeAttribute("data-hex");
            node.style.removeProperty("--swatch-left");
            node.innerHTML = "";
            node.classList.remove("iris-swatch-dim", "iris-swatch-fade-out");
        } else if (i < sourceColors.length) {
            const hex = String(sourceColors[i]?.hex || "");
            const text = hex.replace("#", "").toUpperCase();
            node.className = "palette-swatch flex h-16 sm:h-22 min-w-0 items-center justify-center rounded-xl px-2 text-center text-lg tracking-wide iris-shadow-main";
            node.setAttribute("data-hex", hex);
            node.style.setProperty("--swatch-left", hex);
            node.innerHTML = `<span class="palette-label">${text}</span>`;
            node.classList.add("iris-swatch-dim");
            node.classList.remove("iris-swatch-fade-out");
        } else {
            node.classList.remove("iris-swatch-dim");
            node.classList.add("iris-swatch-fade-out");
        }
    }

    if (container.children.length > finalCount) {
        for (let i = finalCount; i < container.children.length; i += 1) {
            const node = container.children[i];
            if (!(node instanceof HTMLElement)) continue;
            node.classList.remove("iris-swatch-dim");
            node.classList.add("iris-swatch-fade-out");
        }
        window.setTimeout(() => {
            while (container.children.length > finalCount) {
                container.removeChild(container.lastElementChild);
            }
            applySwatchTextContrast(container);
        }, fadeMs);
        return;
    }

    applySwatchTextContrast(container);
}

function updateSwatchGridLayout(container, count) {
    if (!container) return;
    container.classList.remove("grid-cols-5", "grid-cols-6");
    container.classList.add(count >= 11 ? "grid-cols-6" : "grid-cols-5");
}

function applyPaletteBackgroundToUploadArea(root = document) {
    const uploadArea = getUploadAreaElement();
    if (!uploadArea) return;

    const uploaderData = getUploaderData();
    const currentPalette = uploaderData?.extractedPalettes?.[uploaderData.currentIndex] || [];
    const colors = currentPalette
        .map((item) => String(item?.hex || "").trim())
        .filter((hex) => /^#?[0-9a-fA-F]{6}$/.test(hex))
        .map((hex) => (hex.startsWith("#") ? hex : `#${hex}`));

    if (!colors.length) {
        resetUploadAreaBackground();
        return;
    }

    const n = colors.length;
    const leftCount = Math.ceil(n / 2);
    const rightCount = n - leftCount;
    const leftColors = colors.slice(0, leftCount);
    const rightColors = colors.slice(leftCount);
    const midStart = 30;
    const midEnd = 70;
    const gradientStops = [];

    if (leftCount > 0) {
        leftColors.forEach((color, index) => {
            const start = (midStart * index) / leftCount;
            const end = (midStart * (index + 1)) / leftCount;
            gradientStops.push(`${color} ${start}% ${end}%`);
        });
    }

    gradientStops.push(`transparent ${midStart}% ${midEnd}%`);

    if (rightCount > 0) {
        rightColors.forEach((color, index) => {
            const start = midEnd + ((100 - midEnd) * index) / rightCount;
            const end = midEnd + ((100 - midEnd) * (index + 1)) / rightCount;
            gradientStops.push(`${color} ${start}% ${end}%`);
        });
    }

    setUploadAreaBackground(`linear-gradient(120deg, ${gradientStops.join(", ")})`);
}
