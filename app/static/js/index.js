
function isTouchDevice() {
    return window.matchMedia("(hover: none)").matches || "ontouchstart" in window;
}

const MAX_FILES_PER_BATCH = 1000;

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

let lastPointerClientX = -1;
let lastPointerClientY = -1;

function parseHexColor(value) {
    const hex = String(value || "").trim().replace("#", "");
    if (!/^[0-9a-fA-F]{6}$/.test(hex)) return null;
    return {
        hex,
        r: parseInt(hex.slice(0, 2), 16),
        g: parseInt(hex.slice(2, 4), 16),
        b: parseInt(hex.slice(4, 6), 16),
    };
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

function getUploadAreaElement() {
    return document.getElementById("upload-area");
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
        } else {
            if (i < sourceColors.length) {
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
    }

    if (container.children.length > finalCount) {
        for (let i = finalCount; i < container.children.length; i += 1) {
            const node = container.children[i];
            if (!(node instanceof HTMLElement)) continue;
            // Commit mode: overflow swatches should directly fade out.
            // Preview mode already handles "colored -> dim", "empty -> fade out".
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

function getUploaderData() {
    const uploaderRoot = document.querySelector("[x-data]");
    return uploaderRoot?._x_dataStack?.[0];
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

    // split colors to left/right sides
    const leftCount = Math.ceil(n / 2);
    const rightCount = n - leftCount;

    const leftColors = colors.slice(0, leftCount);
    const rightColors = colors.slice(leftCount);

    // keep center white band from 30%–70% (same as CSS)
    const midStart = 30;
    const midEnd = 70;

    const gradientStops = [];

    // left side: 0%–30%
    if (leftCount > 0) {
        leftColors.forEach((color, index) => {
            const start = (midStart * index) / leftCount;
            const end = (midStart * (index + 1)) / leftCount;
            gradientStops.push(`${color} ${start}% ${end}%`);
        });
    }

    // middle transparent band; center color handled by .iris-upload-mid-band
    gradientStops.push(`transparent ${midStart}% ${midEnd}%`);

    // right side: 70%–100%
    if (rightCount > 0) {
        rightColors.forEach((color, index) => {
            const start = midEnd + ((100 - midEnd) * index) / rightCount;
            const end = midEnd + ((100 - midEnd) * (index + 1)) / rightCount;
            gradientStops.push(`${color} ${start}% ${end}%`);
        });
    }

    setUploadAreaBackground(`linear-gradient(120deg, ${gradientStops.join(", ")})`);
}

function uploader() {
    return {
        isDark: getStoredTheme() === "dark",
        themeTransitioning: false,
        nColors: "10",
        previewUrl: "",
        previewUrls: [],
        files: [],
        totalFiles: 0,
        currentIndex: 0,
        extractedPalettes: [],
        paletteRenderTimer: null,
        previewAnimating: false,
        previewSlideClass: "",
        isWorking: false,
        dropActive: false,
        showExport: false,
        holdDelayTimer: null,
        holdRepeatTimer: null,
        navHoldDelayTimer: null,
        navHoldRepeatTimer: null,
        lastNavTapAt: 0,
        lastNavDirection: 0,
        previewDragging: false,
        previewDragStartX: 0,
        previewDragDeltaX: 0,
        keyboardHoldDirection: 0,
        keyboardHoldDelayTimer: null,
        keyboardHoldRepeatTimer: null,
        navPaletteRenderTimer: null,
        preSubmitDesktopCount: 0,
        preSubmitMobileCount: 0,
        lastKeyTapAt: 0,
        onUploadAreaClick(e) {
            const target = e?.target;
            if (target?.closest(".iris-nav-btn")) return;
            this.$refs.fileInput.click();
        },
        clearLoadedFiles() {
            this.revokePreviews();
            this.files = [];
            this.totalFiles = 0;
            this.currentIndex = 0;
            this.previewUrl = "";
            this.previewAnimating = false;
            this.previewSlideClass = "";
            this.extractedPalettes = [];
            if (this.navPaletteRenderTimer) {
                window.clearTimeout(this.navPaletteRenderTimer);
                this.navPaletteRenderTimer = null;
            }
            this.stopNavHold(true);
            this.onKeyboardUp(true);
            if (this.$refs?.fileInput) {
                this.$refs.fileInput.value = "";
                const dt = new DataTransfer();
                this.$refs.fileInput.files = dt.files;
            }
            resetUploadAreaBackground();
            this.renderCurrentPalette(true);
        },
        toggleTheme() {
            if (this.themeTransitioning) return;
            this.themeTransitioning = true;
            this.isDark = !this.isDark;
            applyTheme(this.isDark ? "dark" : "light");
            window.setTimeout(() => {
                this.themeTransitioning = false;
            }, 700);
        },
        previewAt(offset) {
            if (!this.totalFiles || !this.previewUrls.length) return "";
            const idx = this.currentIndex + offset;
            if (idx < 0 || idx >= this.totalFiles) return "";
            return this.previewUrls[idx];
        },
        sanitizeNColors() {
            const digits = String(this.nColors ?? "").replace(/[^\d]/g, "");
            let value = parseInt(digits || "10", 10);
            if (Number.isNaN(value)) value = 10;
            this.nColors = String(Math.min(12, Math.max(1, value)));
        },
        stepNColors(delta) {
            const current = parseInt(this.nColors, 10);
            const base = Number.isNaN(current) ? 10 : current;
            this.nColors = String(Math.min(12, Math.max(1, base + delta)));
            this.schedulePaletteRender();
        },
        startAdjust(delta) {
            this.stopAdjust();
            this.stepNColors(delta);
            this.holdDelayTimer = window.setTimeout(() => {
                this.holdRepeatTimer = window.setInterval(() => this.stepNColors(delta), 90);
            }, 500);
        },
        stopAdjust() {
            if (this.holdDelayTimer) window.clearTimeout(this.holdDelayTimer);
            if (this.holdRepeatTimer) window.clearInterval(this.holdRepeatTimer);
            this.holdDelayTimer = null;
            this.holdRepeatTimer = null;
        },
        revokePreviews() {
            this.previewUrls.forEach((url) => URL.revokeObjectURL(url));
            this.previewUrls = [];
        },
        setPreviewIndex(nextIndex) {
            if (!this.totalFiles) return;
            const prevIndex = this.currentIndex;
            const clamped = Math.max(0, Math.min(this.totalFiles - 1, nextIndex));
            if (clamped === this.currentIndex) return false;
            this.currentIndex = clamped;
            this.previewUrl = this.previewUrls[clamped] || "";
            this.previewSlideClass = clamped > prevIndex ? "iris-slide-in-right" : "iris-slide-in-left";
            this.previewAnimating = true;
            window.setTimeout(() => {
                this.previewAnimating = false;
                this.previewSlideClass = "";
            }, 260);
            this.scheduleNavPaletteRender();
            return true;
        },
        shiftPreview(step) {
            if (!this.totalFiles) return;
            return this.setPreviewIndex(this.currentIndex + step);
        },
        setFiles(filesLike) {
            const files = Array.from(filesLike || []).filter((file) => file && file.type.startsWith("image/"));
            if (!files.length) return;
            let accepted = files;
            if (files.length > MAX_FILES_PER_BATCH) {
                accepted = files.slice(0, MAX_FILES_PER_BATCH);
                showTransientNotice(`Limit is ${MAX_FILES_PER_BATCH} images. Using the first ${MAX_FILES_PER_BATCH}.`);
            }
            this.revokePreviews();
            const dt = new DataTransfer();
            accepted.forEach((file) => dt.items.add(file));
            this.$refs.fileInput.files = dt.files;
            this.files = accepted;
            this.previewUrls = accepted.map((file) => URL.createObjectURL(file));
            this.totalFiles = accepted.length;
            this.currentIndex = 0;
            this.previewUrl = this.previewUrls[0] || "";
            this.previewAnimating = false;
            this.previewSlideClass = "";
            this.extractedPalettes = [];
            if (this.navPaletteRenderTimer) {
                window.clearTimeout(this.navPaletteRenderTimer);
                this.navPaletteRenderTimer = null;
            }
            this.stopNavHold(true);
            this.onKeyboardUp(true);
            resetUploadAreaBackground();
            this.renderCurrentPalette(true);
        },
        scheduleNavPaletteRender() {
            if (this.navPaletteRenderTimer) window.clearTimeout(this.navPaletteRenderTimer);
            this.navPaletteRenderTimer = window.setTimeout(() => {
                this.navPaletteRenderTimer = null;
                this.renderCurrentPalette();
            }, 180);
        },
        flushNavPaletteRender() {
            if (this.navPaletteRenderTimer) {
                window.clearTimeout(this.navPaletteRenderTimer);
                this.navPaletteRenderTimer = null;
            }
            this.renderCurrentPalette();
        },
        onPick(e) {
            const files = e?.target?.files;
            if (!files?.length) {
                if (this.files?.length && this.$refs?.fileInput) {
                    const dt = new DataTransfer();
                    this.files.forEach((file) => dt.items.add(file));
                    this.$refs.fileInput.files = dt.files;
                }
                return;
            }
            this.setFiles(files);
        },
        onDrop(e) {
            this.dropActive = false;
            const files = e?.dataTransfer?.files;
            if (!files?.length) return;
            this.setFiles(files);
        },
        schedulePaletteRender() {
            if (this.paletteRenderTimer) window.clearTimeout(this.paletteRenderTimer);
            this.paletteRenderTimer = window.setTimeout(() => this.renderCurrentPalette(), 120);
        },
        renderCurrentPalette(commit = false, options = {}) {
            const n = Math.max(1, parseInt(this.nColors, 10) || 10);
            const palette = this.extractedPalettes?.[this.currentIndex] || [];
            const desktop = document.getElementById("desktop-swatches");
            const mobile = document.getElementById("mobile-swatches");
            const keepDesktop = Math.max(0, Number(options.keepDesktop || 0));
            const keepMobile = Math.max(0, Number(options.keepMobile || 0));
            const paletteCount = Array.isArray(palette) ? palette.length : 0;
            const previewLayoutCount = Math.max(n, paletteCount);
            updateSwatchGridLayout(desktop, commit ? n : previewLayoutCount);
            renderPaletteGrid(desktop, palette, n, { commit, keepAtLeast: keepDesktop });
            renderPaletteGrid(mobile, palette, n, { commit, keepAtLeast: keepMobile });
            applyPaletteBackgroundToUploadArea(document);
        },
        startPreviewDrag(e) {
            if (!this.totalFiles) return;
            this.previewDragging = true;
            this.previewDragStartX = e.clientX;
            this.previewDragDeltaX = 0;
        },
        movePreviewDrag(e) {
            if (!this.previewDragging) return;
            this.previewDragDeltaX = e.clientX - this.previewDragStartX;
        },
        endPreviewDrag() {
            if (!this.previewDragging) return;
            this.previewDragging = false;
            if (Math.abs(this.previewDragDeltaX) > 36) {
                this.shiftPreview(this.previewDragDeltaX < 0 ? 1 : -1);
            }
            this.previewDragDeltaX = 0;
        },
        startNavHold(direction) {
            this.stopNavHold(true);
            const now = Date.now();
            const turbo = this.lastNavDirection === direction && now - this.lastNavTapAt < 260;
            this.lastNavDirection = direction;
            this.lastNavTapAt = now;
            const moved = this.shiftPreview(direction);
            if (!moved) return;
            this.navHoldDelayTimer = window.setTimeout(() => {
                this.navHoldRepeatTimer = window.setInterval(() => {
                    const stepMoved = this.shiftPreview(direction);
                    if (!stepMoved) this.stopNavHold();
                }, turbo ? 20 : 100);
            }, 260);
        },
        stopNavHold(suppressFlush = false) {
            if (this.navHoldDelayTimer) window.clearTimeout(this.navHoldDelayTimer);
            if (this.navHoldRepeatTimer) window.clearInterval(this.navHoldRepeatTimer);
            this.navHoldDelayTimer = null;
            this.navHoldRepeatTimer = null;
            if (!suppressFlush) this.flushNavPaletteRender();
        },
        onKeyboardDown(direction) {
            if (!this.totalFiles) return;
            if (this.keyboardHoldDirection === direction) return;
            this.onKeyboardUp(true);
            const now = Date.now();
            const turbo = now - this.lastKeyTapAt < 260;
            this.lastKeyTapAt = now;
            this.keyboardHoldDirection = direction;
            const moved = this.shiftPreview(direction);
            if (!moved) {
                this.onKeyboardUp();
                return;
            }
            this.keyboardHoldDelayTimer = window.setTimeout(() => {
                this.keyboardHoldRepeatTimer = window.setInterval(() => {
                    const stepMoved = this.shiftPreview(direction);
                    if (!stepMoved) this.onKeyboardUp();
                }, turbo ? 20 : 100);
            }, 260);
        },
        onKeyboardUp(suppressFlush = false) {
            this.keyboardHoldDirection = 0;
            if (this.keyboardHoldDelayTimer) window.clearTimeout(this.keyboardHoldDelayTimer);
            if (this.keyboardHoldRepeatTimer) window.clearInterval(this.keyboardHoldRepeatTimer);
            this.keyboardHoldDelayTimer = null;
            this.keyboardHoldRepeatTimer = null;
            if (!suppressFlush) this.flushNavPaletteRender();
        },
    };
}

function copyPaletteJson(button) {
    if (isTouchDevice()) {
        const dock = button?.closest(".iris-export-dock");
        if (dock && !dock.classList.contains("open")) {
            dock.classList.add("open");
            return;
        }
    }
    const node = document.getElementById("palette-json");
    if (!node) return;
    navigator.clipboard.writeText(node.innerText || node.textContent || "");
    if (!button) return;
    const originalHtml = button.innerHTML;
    const originalClass = button.className;
    const label = button.querySelector("span");
    if (label) {
        label.textContent = "COPIED";
    } else {
        button.textContent = "COPIED";
    }
    button.classList.add("opacity-50");
    button.disabled = true;
    window.setTimeout(() => {
        button.innerHTML = originalHtml;
        button.className = originalClass;
        button.disabled = false;
    }, 900);
    closeAllExportDock();
}

function shortUniqueId() {
    const t = Date.now().toString(36);
    const p = Math.floor(performance.now()).toString(36);
    const r = Math.floor(Math.random() * 1679616).toString(36);
    return `${t}${p}${r}`;
}

function exportPaletteTxt(button) {
    const jsonNode = document.getElementById("palette-json");
    if (!jsonNode) return;
    const content = jsonNode.innerText || jsonNode.textContent || "";
    const uploaderData = getUploaderData();
    const count = uploaderData?.extractedPalettes?.length || uploaderData?.totalFiles || 1;
    const filename = `Iris_OKLCH_${count}_${shortUniqueId()}.txt`;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    if (button) {
        button.classList.add("opacity-50");
        window.setTimeout(() => button.classList.remove("opacity-50"), 500);
    }
    closeAllExportDock();
}

function toggleExportDock(triggerButton) {
    const dock = triggerButton?.closest(".iris-export-dock");
    if (!dock) return;
    dock.classList.toggle("open");
}

function closeAllExportDock() {
    document.querySelectorAll(".iris-export-dock.open").forEach((dock) => dock.classList.remove("open"));
}

function initExportDockHover(root = document) {
    const docks = root.querySelectorAll(".iris-export-dock");
    docks.forEach((dock) => {
        if (dock.dataset.hoverBound === "1") return;
        dock.dataset.hoverBound = "1";
        dock.addEventListener("mouseenter", () => {
            if (isTouchDevice()) return;
            dock.classList.add("open");
        });
        dock.addEventListener("mouseleave", (event) => {
            if (isTouchDevice()) return;
            const next = event.relatedTarget;
            if (next && dock.contains(next)) return;
            dock.classList.remove("open");
        });
    });
}

function keepDockOpenIfPointerInside(root = document) {
    if (lastPointerClientX < 0 || lastPointerClientY < 0) return;
    const docks = root.querySelectorAll(".iris-export-dock");
    docks.forEach((dock) => {
        const rect = dock.getBoundingClientRect();
        const inside = lastPointerClientX >= rect.left
            && lastPointerClientX <= rect.right
            && lastPointerClientY >= rect.top
            && lastPointerClientY <= rect.bottom;
        if (inside) dock.classList.add("open");
    });
}

function toggleMobileSheet() {
    const sheet = document.getElementById("mobile-sheet");
    if (!sheet) return;
    setMobileSheetOpen(sheet, !sheet.classList.contains("open"));
}

function setMobileSheetOpen(sheet, shouldOpen) {
    if (!sheet) return;
    sheet.classList.remove("anim-open", "anim-close");
    if (shouldOpen) {
        sheet.classList.add("open", "anim-open");
    } else {
        sheet.classList.add("anim-close");
        window.setTimeout(() => {
            sheet.classList.remove("open");
            sheet.classList.remove("anim-close");
        }, 260);
    }
}

function initMobileSheetGesture() {
    const sheet = document.getElementById("mobile-sheet");
    if (!sheet) return;
    let startY = 0;
    let active = false;

    sheet.addEventListener("touchstart", (e) => {
        if (!e.touches?.length) return;
        active = true;
        startY = e.touches[0].clientY;
    }, { passive: true });

    sheet.addEventListener("touchend", (e) => {
        if (!active || !e.changedTouches?.length) return;
        const delta = e.changedTouches[0].clientY - startY;
        if (delta < -24) {
            setMobileSheetOpen(sheet, true);
        } else if (delta > 24) {
            setMobileSheetOpen(sheet, false);
        }
        active = false;
    }, { passive: true });
}

document.addEventListener("DOMContentLoaded", () => applySwatchTextContrast());
document.addEventListener("DOMContentLoaded", () => {
    applyTheme(getStoredTheme());
    const alpineData = getUploaderData();
    if (alpineData) alpineData.schedulePaletteRender();
    initExportDockHover(document);
});
document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event?.target?.id === "result") {
        const alpineData = getUploaderData();
        const palettes = readPaletteDataFromDom(event.target);
        if (alpineData && Array.isArray(palettes) && palettes.length > 0) {
            const n = Math.max(1, parseInt(alpineData.nColors, 10) || 10);
            const previousPalette = alpineData.extractedPalettes?.[alpineData.currentIndex] || [];
            const desktop = document.getElementById("desktop-swatches");
            const mobile = document.getElementById("mobile-swatches");
            const keepDesktop = alpineData.preSubmitDesktopCount || 0;
            const keepMobile = alpineData.preSubmitMobileCount || 0;

            // Seed the swapped DOM with previous colors, then transition to new result.
            if (desktop) {
                updateSwatchGridLayout(desktop, n);
                renderPaletteGrid(desktop, previousPalette, n, { keepAtLeast: keepDesktop });
            }
            if (mobile) {
                renderPaletteGrid(mobile, previousPalette, n, { keepAtLeast: keepMobile });
            }

            alpineData.extractedPalettes = palettes;
            requestAnimationFrame(() => {
                alpineData.renderCurrentPalette(true, { keepDesktop, keepMobile });
                alpineData.preSubmitDesktopCount = 0;
                alpineData.preSubmitMobileCount = 0;
            });
        }
        applySwatchTextContrast(event.target);
        initMobileSheetGesture();
        initExportDockHover(event.target);
        keepDockOpenIfPointerInside(event.target);
    }
});
document.body.addEventListener("htmx:beforeRequest", (event) => {
    if (event?.detail?.requestConfig?.path !== "/api/extract") return;
    const alpineData = getUploaderData();
    if (alpineData) {
        const inputEl = alpineData.$refs?.fileInput;
        const inputCount = inputEl?.files?.length || 0;
        const memoryCount = alpineData.files?.length || 0;

        // Some browsers clear <input type=file> when the picker is canceled.
        // Restore from in-memory files so the form field "images" is always present.
        if (inputEl && inputCount === 0 && memoryCount > 0) {
            const dt = new DataTransfer();
            alpineData.files.forEach((file) => dt.items.add(file));
            inputEl.files = dt.files;
        }

        if ((inputEl?.files?.length || 0) === 0) {
            event.preventDefault();
            alpineData.$refs?.fileInput?.click?.();
            return;
        }
        if ((inputEl?.files?.length || 0) > MAX_FILES_PER_BATCH) {
            event.preventDefault();
            showTransientNotice(`Limit is ${MAX_FILES_PER_BATCH} images per run.`);
            const accepted = Array.from(inputEl.files).slice(0, MAX_FILES_PER_BATCH);
            alpineData.setFiles(accepted);
            return;
        }
        alpineData.preSubmitDesktopCount = document.getElementById("desktop-swatches")?.children?.length || 0;
        alpineData.preSubmitMobileCount = document.getElementById("mobile-swatches")?.children?.length || 0;
        alpineData.isWorking = true;
    }
});
document.body.addEventListener("htmx:afterRequest", (event) => {
    if (event?.detail?.requestConfig?.path !== "/api/extract") return;
    const alpineData = getUploaderData();
    if (alpineData) alpineData.isWorking = false;
});
["htmx:responseError", "htmx:sendError", "htmx:timeout"].forEach((evt) => {
    document.body.addEventListener(evt, (event) => {
        if (event?.detail?.requestConfig?.path !== "/api/extract") return;
        const alpineData = getUploaderData();
        if (alpineData) alpineData.isWorking = false;
    });
});
document.addEventListener("keydown", (event) => {
    const alpineData = getUploaderData();
    if (!alpineData) return;
    const activeTag = String(document.activeElement?.tagName || "").toLowerCase();
    if (activeTag === "textarea") return;
    if (event.key === "Enter" && activeTag !== "input") {
        event.preventDefault();
        const form = document.getElementById("extract-form");
        if (form instanceof HTMLFormElement && alpineData.totalFiles > 0 && !alpineData.isWorking) {
            form.requestSubmit();
        }
        return;
    }
    if (activeTag === "input") return;
    if (event.key === "ArrowLeft") {
        event.preventDefault();
        alpineData.onKeyboardDown(-1);
    } else if (event.key === "ArrowRight") {
        event.preventDefault();
        alpineData.onKeyboardDown(1);
    } else if (event.key === "ArrowUp") {
        event.preventDefault();
        alpineData.stepNColors(1);
    } else if (event.key === "ArrowDown") {
        event.preventDefault();
        alpineData.stepNColors(-1);
    }
});
document.addEventListener("keyup", (event) => {
    const alpineData = getUploaderData();
    if (!alpineData) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        alpineData.onKeyboardUp();
    }
});
document.addEventListener("DOMContentLoaded", () => {
    initMobileSheetGesture();
});
document.addEventListener("click", (event) => {
    if (!isTouchDevice()) return;
    const target = event.target;
    if (target?.closest(".iris-export-dock")) return;
    closeAllExportDock();
});
document.addEventListener("pointermove", (event) => {
    lastPointerClientX = event.clientX;
    lastPointerClientY = event.clientY;
}, { passive: true });
