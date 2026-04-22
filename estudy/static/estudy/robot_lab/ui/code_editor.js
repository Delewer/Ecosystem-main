/* code_editor.js — Senior levels: syntax-highlighted textarea with line numbers */
'use strict';

const RRCodeEditor = (() => {
    class CodeEditor {
        constructor(container, { starterCode, readOnly, onCodeChange }) {
            this._container = container;
            this._onCodeChange = onCodeChange || (() => {});
            this._readOnly = Boolean(readOnly);
            this._render(starterCode || '');
        }

        _render(starterCode) {
            this._container.innerHTML = '';
            this._container.classList.add('rr-code-editor');

            // Line numbers
            this._lineNums = document.createElement('div');
            this._lineNums.className = 'rr-code-editor__lines';
            this._container.appendChild(this._lineNums);

            // Textarea
            this._textarea = document.createElement('textarea');
            this._textarea.className = 'rr-code-editor__input';
            this._textarea.spellcheck = false;
            this._textarea.autocomplete = 'off';
            this._textarea.value = starterCode;
            this._textarea.readOnly = this._readOnly;

            this._textarea.addEventListener('input', () => {
                this._updateLineNumbers();
                this._onCodeChange(this._textarea.value);
            });
            this._textarea.addEventListener('scroll', () => {
                this._lineNums.scrollTop = this._textarea.scrollTop;
            });
            this._textarea.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    const start = this._textarea.selectionStart;
                    const end = this._textarea.selectionEnd;
                    this._textarea.value = this._textarea.value.substring(0, start) + '    ' + this._textarea.value.substring(end);
                    this._textarea.selectionStart = this._textarea.selectionEnd = start + 4;
                    this._updateLineNumbers();
                    this._onCodeChange(this._textarea.value);
                }
            });
            this._container.appendChild(this._textarea);

            // Error highlight area
            this._errorLine = -1;

            this._updateLineNumbers();
        }

        _updateLineNumbers() {
            const lines = this._textarea.value.split('\n');
            const nums = [];
            for (let i = 1; i <= lines.length; i++) {
                const cls = i === this._errorLine ? 'is-error' : '';
                nums.push(`<span class="${cls}">${i}</span>`);
            }
            this._lineNums.innerHTML = nums.join('\n');
        }

        getValue() { return this._textarea.value; }

        setValue(code) {
            this._textarea.value = code;
            this._updateLineNumbers();
        }

        highlightError(lineNumber) {
            this._errorLine = lineNumber;
            this._updateLineNumbers();
        }

        clearError() {
            this._errorLine = -1;
            this._updateLineNumbers();
        }

        focus() { this._textarea.focus(); }

        destroy() { this._container.innerHTML = ''; }
    }

    return { CodeEditor };
})();

if (typeof window !== 'undefined') window.RRCodeEditor = RRCodeEditor;
