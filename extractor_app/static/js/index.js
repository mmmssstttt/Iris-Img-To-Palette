function paletteApp() {
    return {
        file: null,
        fileName: '',
        preview: null,
        dragover: false,
        loading: false,

        selectedColors: [],
        extractedColors: [],
        maxColors: 10,
        dragIndex: null,

        handleFile(e) {
            const file = e.target.files[0];
            if (!file) return;

            this.file = file;
            this.fileName = file.name;

            const r = new FileReader();
            r.onload = e => this.preview = e.target.result;
            r.readAsDataURL(file);
        },

        handleDrop(e) {
            const file = e.dataTransfer.files[0];
            if (!file) return;

            this.file = file;
            this.fileName = file.name;

            const r = new FileReader();
            r.onload = e => this.preview = e.target.result;
            r.readAsDataURL(file);
        },

        setExtracted(colors) {
            this.extractedColors = colors;
        },

        addColor(c) {
            if (this.selectedColors.length < this.maxColors) {
                this.selectedColors.push(c);
            }
        },

        removeColor(i) {
            this.selectedColors.splice(i,1);
        },

        moveColor(from, to) {
            if (from === to) return;
            if (from < 0 || to < 0) return;
            if (from >= this.selectedColors.length || to >= this.selectedColors.length) return;

            const [moved] = this.selectedColors.splice(from, 1);
            this.selectedColors.splice(to, 0, moved);
        },

        startDrag(i) {
            this.dragIndex = i;
        },

        dropOn(i) {
            if (this.dragIndex === null) return;
            this.moveColor(this.dragIndex, i);
            this.dragIndex = null;
        },

        clearDrag() {
            this.dragIndex = null;
        },

        async recordData() {
            if (!this.file) {
                alert('upload first');
                return;
            }

            const fd = new FormData();
            fd.append('image', this.file);
            fd.append('selected_colors', JSON.stringify(this.selectedColors));

            await fetch('/api/record', {
                method:'POST',
                body:fd
            });

            alert('saved');
        }
    }
}
