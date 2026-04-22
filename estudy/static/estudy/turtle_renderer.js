/* eslint-env browser */

/**
 * TurtleRenderer — Minimal client-side turtle graphics for Robot Lab.
 *
 * Parses TURTLE:<cmd>:<arg> lines from runner stdout and replays
 * them on a <canvas> element.
 *
 * Usage:
 *   const renderer = new TurtleRenderer(canvasElement);
 *   renderer.execute(stdoutLines);   // array of strings from runner
 *   renderer.reset();
 */
(() => {
    'use strict';

    const TURTLE_PREFIX = 'TURTLE:';
    const DEFAULT_COLOR = '#3B82F6';
    const BG_COLOR = '#0F172A';
    const TURTLE_SIZE = 8;

    class TurtleRenderer {
        constructor(canvas) {
            this._canvas = canvas;
            this._ctx = canvas.getContext('2d');
            this._width = canvas.width;
            this._height = canvas.height;
            this.reset();
        }

        reset() {
            this._x = this._width / 2;
            this._y = this._height / 2;
            this._angle = -90;           // facing up
            this._penDown = true;
            this._color = DEFAULT_COLOR;
            this._commands = [];
            this._clear();
        }

        _clear() {
            const ctx = this._ctx;
            ctx.fillStyle = BG_COLOR;
            ctx.fillRect(0, 0, this._width, this._height);

            // grid lines
            ctx.strokeStyle = 'rgba(148,163,184,0.1)';
            ctx.lineWidth = 0.5;
            for (let x = 0; x < this._width; x += 20) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, this._height);
                ctx.stroke();
            }
            for (let y = 0; y < this._height; y += 20) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(this._width, y);
                ctx.stroke();
            }
        }

        /**
         * Parse stdout lines and replay turtle commands on canvas.
         * @param {string[]} lines - Array of stdout lines from runner.
         */
        execute(lines) {
            this.reset();
            const cmds = [];
            for (const line of lines) {
                const trimmed = (typeof line === 'string' ? line : '').trim();
                if (!trimmed.startsWith(TURTLE_PREFIX)) continue;
                const parts = trimmed.slice(TURTLE_PREFIX.length).split(':');
                const cmd = (parts[0] || '').toLowerCase();
                const arg = parts[1] || '';
                cmds.push({ cmd, arg });
            }
            this._commands = cmds;
            this._replay();
        }

        _replay() {
            for (const { cmd, arg } of this._commands) {
                switch (cmd) {
                    case 'forward': this._forward(parseFloat(arg) || 0); break;
                    case 'backward': this._forward(-(parseFloat(arg) || 0)); break;
                    case 'right': this._angle += (parseFloat(arg) || 0); break;
                    case 'left': this._angle -= (parseFloat(arg) || 0); break;
                    case 'penup': this._penDown = false; break;
                    case 'pendown': this._penDown = true; break;
                    case 'color': this._color = arg || DEFAULT_COLOR; break;
                    case 'goto': {
                        const coords = arg.split(',');
                        const nx = parseFloat(coords[0]);
                        const ny = parseFloat(coords[1]);
                        if (!isNaN(nx) && !isNaN(ny)) {
                            this._moveTo(this._width / 2 + nx, this._height / 2 - ny);
                        }
                        break;
                    }
                    default: break;
                }
            }
            this._drawTurtle();
        }

        _forward(dist) {
            const rad = (this._angle * Math.PI) / 180;
            const nx = this._x + dist * Math.cos(rad);
            const ny = this._y + dist * Math.sin(rad);
            if (this._penDown) {
                const ctx = this._ctx;
                ctx.beginPath();
                ctx.moveTo(this._x, this._y);
                ctx.lineTo(nx, ny);
                ctx.strokeStyle = this._color;
                ctx.lineWidth = 2;
                ctx.lineCap = 'round';
                ctx.stroke();
            }
            this._x = nx;
            this._y = ny;
        }

        _moveTo(nx, ny) {
            if (this._penDown) {
                const ctx = this._ctx;
                ctx.beginPath();
                ctx.moveTo(this._x, this._y);
                ctx.lineTo(nx, ny);
                ctx.strokeStyle = this._color;
                ctx.lineWidth = 2;
                ctx.lineCap = 'round';
                ctx.stroke();
            }
            this._x = nx;
            this._y = ny;
        }

        _drawTurtle() {
            const ctx = this._ctx;
            const rad = (this._angle * Math.PI) / 180;
            ctx.save();
            ctx.translate(this._x, this._y);
            ctx.rotate(rad);
            ctx.beginPath();
            ctx.moveTo(TURTLE_SIZE, 0);
            ctx.lineTo(-TURTLE_SIZE / 2, -TURTLE_SIZE / 2);
            ctx.lineTo(-TURTLE_SIZE / 2, TURTLE_SIZE / 2);
            ctx.closePath();
            ctx.fillStyle = '#22C55E';
            ctx.fill();
            ctx.restore();
        }
    }

    window.TurtleRenderer = TurtleRenderer;
})();
