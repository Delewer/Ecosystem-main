/* block_editor.js — Block palette + sequence workspace + repeat wrapper + undo/redo */
'use strict';

const RRBlockEditor = (() => {
    const MAX_SLOTS = 10;

    const BLOCK_DEFS = {
        right:      { label: 'right()',      symbol: '→', category: 'movement' },
        left:       { label: 'left()',       symbol: '←', category: 'movement' },
        up:         { label: 'up()',         symbol: '↑', category: 'movement' },
        down:       { label: 'down()',       symbol: '↓', category: 'movement' },
        turn_left:  { label: 'turn_left()',  symbol: '↺', category: 'movement' },
        turn_right: { label: 'turn_right()', symbol: '↻', category: 'movement' },
        move:       { label: 'move()',       symbol: '▶', category: 'movement' },
        pick:       { label: 'pick()',       symbol: '⚡', category: 'special' },
        activate:   { label: 'activate()',   symbol: '📡', category: 'special' },
    };

    class BlockEditor {
        constructor(container, { allowedApi, onSequenceChange }) {
            this._container = container;
            this._allowedApi = new Set(allowedApi || []);
            this._onSequenceChange = onSequenceChange || (() => {});
            this._sequence = [];
            this._undoStack = [];
            this._redoStack = [];
            this._activeIndex = -1;
            this._render();
        }

        _render() {
            this._container.innerHTML = '';

            // Undo/redo bar
            const undoBar = document.createElement('div');
            undoBar.className = 'rr-undo-bar';
            undoBar.innerHTML = `
                <button data-rr-undo disabled>Undo</button>
                <button data-rr-redo disabled>Redo</button>
                <button data-rr-clear>Sterge tot</button>
            `;
            this._container.appendChild(undoBar);

            undoBar.querySelector('[data-rr-undo]').addEventListener('click', () => this.undo());
            undoBar.querySelector('[data-rr-redo]').addEventListener('click', () => this.redo());
            undoBar.querySelector('[data-rr-clear]').addEventListener('click', () => this.clear());

            // Sequence workspace
            const seqWrap = document.createElement('div');
            seqWrap.className = 'rr-sequence';
            seqWrap.dataset.rrSequence = '';
            for (let i = 0; i < MAX_SLOTS; i++) {
                const slot = document.createElement('div');
                slot.className = 'rr-sequence__slot';
                slot.dataset.slotIndex = i;
                slot.addEventListener('click', () => this._removeAt(i));
                slot.addEventListener('dragover', e => { e.preventDefault(); slot.classList.add('is-drag-over'); });
                slot.addEventListener('dragleave', () => slot.classList.remove('is-drag-over'));
                slot.addEventListener('drop', e => {
                    e.preventDefault();
                    slot.classList.remove('is-drag-over');
                    const cmd = e.dataTransfer.getData('text/plain');
                    if (cmd) this._insertAt(i, cmd);
                });
                seqWrap.appendChild(slot);
            }
            this._container.appendChild(seqWrap);

            // Block palette
            const palette = document.createElement('div');
            palette.className = 'rr-palette';

            const categories = ['movement', 'special'];
            for (const cat of categories) {
                const group = document.createElement('div');
                group.className = 'rr-palette__group';

                for (const [cmd, def] of Object.entries(BLOCK_DEFS)) {
                    if (def.category !== cat) continue;
                    if (!this._allowedApi.has(cmd)) continue;

                    const block = document.createElement('button');
                    block.type = 'button';
                    block.className = `rr-block rr-block--${def.category}`;
                    block.draggable = true;
                    block.innerHTML = `<span class="rr-block__icon">${def.symbol}</span>`;
                    block.title = def.label;
                    block.addEventListener('click', () => this._appendCommand(cmd));
                    block.addEventListener('dragstart', e => {
                        e.dataTransfer.setData('text/plain', cmd);
                        block.classList.add('is-dragging');
                    });
                    block.addEventListener('dragend', () => block.classList.remove('is-dragging'));
                    group.appendChild(block);
                }

                if (group.children.length) palette.appendChild(group);
            }
            this._container.appendChild(palette);

            this._updateSlots();
        }

        _appendCommand(cmd) {
            if (this._sequence.length >= MAX_SLOTS) return;
            this._pushUndo();
            this._sequence.push(cmd);
            this._updateSlots();
            this._notify();
        }

        _insertAt(index, cmd) {
            if (this._sequence.length >= MAX_SLOTS) return;
            this._pushUndo();
            this._sequence.splice(index, 0, cmd);
            if (this._sequence.length > MAX_SLOTS) this._sequence.length = MAX_SLOTS;
            this._updateSlots();
            this._notify();
        }

        _removeAt(index) {
            if (index < 0 || index >= this._sequence.length) return;
            this._pushUndo();
            this._sequence.splice(index, 1);
            this._updateSlots();
            this._notify();
        }

        _updateSlots() {
            const slots = this._container.querySelectorAll('.rr-sequence__slot');
            slots.forEach((slot, i) => {
                const cmd = this._sequence[i];
                if (cmd) {
                    const def = BLOCK_DEFS[cmd];
                    slot.textContent = def ? def.symbol : cmd;
                    slot.classList.add('is-filled');
                    const cat = def ? def.category : 'movement';
                    slot.style.background = '';
                    slot.classList.remove('is-active');
                } else {
                    slot.textContent = '';
                    slot.classList.remove('is-filled');
                    slot.style.background = '';
                    slot.classList.remove('is-active');
                }
                slot.classList.toggle('is-active', i === this._activeIndex);
            });

            // Update undo/redo buttons
            const undoBtn = this._container.querySelector('[data-rr-undo]');
            const redoBtn = this._container.querySelector('[data-rr-redo]');
            if (undoBtn) undoBtn.disabled = !this._undoStack.length;
            if (redoBtn) redoBtn.disabled = !this._redoStack.length;
        }

        _pushUndo() {
            this._undoStack.push([...this._sequence]);
            this._redoStack = [];
            if (this._undoStack.length > 50) this._undoStack.shift();
        }

        _notify() {
            this._onSequenceChange(this.toCode());
        }

        undo() {
            if (!this._undoStack.length) return;
            this._redoStack.push([...this._sequence]);
            this._sequence = this._undoStack.pop();
            this._updateSlots();
            this._notify();
        }

        redo() {
            if (!this._redoStack.length) return;
            this._undoStack.push([...this._sequence]);
            this._sequence = this._redoStack.pop();
            this._updateSlots();
            this._notify();
        }

        clear() {
            if (!this._sequence.length) return;
            this._pushUndo();
            this._sequence = [];
            this._activeIndex = -1;
            this._updateSlots();
            this._notify();
        }

        highlightIndex(index) {
            this._activeIndex = index;
            this._updateSlots();
        }

        getSequence() { return [...this._sequence]; }

        toCode() {
            return this._sequence.map(cmd => `${cmd}()`).join('\n');
        }

        destroy() {
            this._container.innerHTML = '';
        }
    }

    return { BlockEditor, BLOCK_DEFS };
})();

if (typeof window !== 'undefined') window.RRBlockEditor = RRBlockEditor;
