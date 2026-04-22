/* robot.js — Robot state machine: position, direction, inventory, skin, animations */
'use strict';

const RRRobot = (() => {
    const DIRS = ['N', 'E', 'S', 'W'];
    const DELTAS = { N: [-1, 0], E: [0, 1], S: [1, 0], W: [0, -1] };

    class Robot {
        constructor({ row, col, dir, skin }) {
            this.row = row || 0;
            this.col = col || 0;
            this.dir = DIRS.includes(dir) ? dir : 'E';
            this.skin = skin || 'zipp';
            this.inventory = [];
            this.state = 'idle'; // idle, walking, turning, collecting, success, error, thinking, sliding, burning
            this._stateTimeout = null;
        }

        get position() { return { r: this.row, c: this.col }; }

        get delta() { return DELTAS[this.dir] || [0, 1]; }

        frontPos() {
            const [dr, dc] = this.delta;
            return { r: this.row + dr, c: this.col + dc };
        }

        moveTo(r, c) {
            this.row = r;
            this.col = c;
        }

        turnLeft() {
            const idx = DIRS.indexOf(this.dir);
            this.dir = DIRS[(idx + 3) % 4];
        }

        turnRight() {
            const idx = DIRS.indexOf(this.dir);
            this.dir = DIRS[(idx + 1) % 4];
        }

        faceDirection(dir) {
            if (DIRS.includes(dir)) this.dir = dir;
        }

        addItem(item) {
            if (!this.inventory.includes(item)) {
                this.inventory.push(item);
            }
        }

        hasItem(item) {
            return this.inventory.includes(item);
        }

        setState(newState, durationMs) {
            if (this._stateTimeout) {
                clearTimeout(this._stateTimeout);
                this._stateTimeout = null;
            }
            this.state = newState;
            if (durationMs && durationMs > 0) {
                this._stateTimeout = setTimeout(() => {
                    this.state = 'idle';
                    this._stateTimeout = null;
                }, durationMs);
            }
        }

        reset(row, col, dir) {
            this.row = row || 0;
            this.col = col || 0;
            this.dir = dir || 'E';
            this.inventory = [];
            this.state = 'idle';
            if (this._stateTimeout) {
                clearTimeout(this._stateTimeout);
                this._stateTimeout = null;
            }
        }

        toJSON() {
            return {
                row: this.row,
                col: this.col,
                dir: this.dir,
                skin: this.skin,
                inventory: [...this.inventory],
                state: this.state,
            };
        }
    }

    return { Robot, DIRS, DELTAS };
})();

if (typeof window !== 'undefined') window.RRRobot = RRRobot;
