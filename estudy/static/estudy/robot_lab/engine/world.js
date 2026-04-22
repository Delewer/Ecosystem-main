/* world.js — Parses level JSON, manages tile state, handles special tile logic */
'use strict';

const RRWorld = (() => {
    const TILE_TYPES = {
        '#': 'wall', '.': 'floor', 'S': 'start', 'G': 'goal', 'T': 'terminal',
        'B': 'battery', 'K': 'key', 'D': 'door', 'H': 'hazard',
        '~': 'ice', '=': 'heater', '^': 'lava', 'C': 'coolant',
        'P': 'portal',
    };

    class World {
        constructor(levelSpec) {
            this.spec = levelSpec;
            this.grid = (levelSpec.grid || []).map(row => [...String(row)]);
            this.rows = this.grid.length;
            this.cols = this.rows ? Math.max(...this.grid.map(r => r.length)) : 0;
            this.theme = String(levelSpec.world_theme || levelSpec.background_theme || 'garden');
            this.startPos = this._findTile('S');
            this.startDir = String(levelSpec.start_dir || 'E').toUpperCase();
            this.stepCount = 0;
            this.lavaTimer = 0;
            this.lavaPhase = true; // true = safe
        }

        tileAt(r, c) {
            if (r < 0 || c < 0 || r >= this.rows) return '#';
            const row = this.grid[r];
            if (!row || c >= row.length) return '#';
            return row[c];
        }

        tileType(r, c) {
            return TILE_TYPES[this.tileAt(r, c)] || 'floor';
        }

        _findTile(ch) {
            for (let r = 0; r < this.rows; r++) {
                for (let c = 0; c < this.grid[r].length; c++) {
                    if (this.grid[r][c] === ch) return { r, c };
                }
            }
            return { r: 0, c: 0 };
        }

        findAllTiles(ch) {
            const result = [];
            for (let r = 0; r < this.rows; r++) {
                for (let c = 0; c < this.grid[r].length; c++) {
                    if (this.grid[r][c] === ch) result.push({ r, c });
                }
            }
            return result;
        }

        isWalkable(r, c, inventory) {
            const tile = this.tileAt(r, c);
            if (tile === '#') return false;
            if (tile === 'D') return (inventory || []).includes('key');
            return true;
        }

        isIce(r, c) { return this.tileAt(r, c) === '~'; }
        isHeater(r, c) { return this.tileAt(r, c) === '='; }

        isLavaSafe(r, c) {
            if (this.tileAt(r, c) !== '^') return true;
            return this.lavaPhase;
        }

        advanceStep() {
            this.stepCount++;
            if (this.stepCount % 3 === 0) {
                this.lavaPhase = !this.lavaPhase;
            }
            this.lavaTimer = this.stepCount;
        }

        removeTile(r, c) {
            if (r >= 0 && r < this.rows && c >= 0 && c < this.grid[r].length) {
                this.grid[r][c] = '.';
            }
        }

        slideOnIce(r, c, dr, dc) {
            let nr = r + dr;
            let nc = c + dc;
            while (this.isWalkable(nr, nc, []) && this.isIce(nr, nc)) {
                nr += dr;
                nc += dc;
            }
            if (!this.isWalkable(nr, nc, [])) {
                nr -= dr;
                nc -= dc;
            }
            if (this.isHeater(nr, nc)) {
                // Stop at heater
            }
            return { r: nr, c: nc };
        }

        portalPair(r, c) {
            const portals = this.findAllTiles('P');
            const other = portals.find(p => !(p.r === r && p.c === c));
            return other || null;
        }
    }

    return { World };
})();

if (typeof window !== 'undefined') window.RRWorld = RRWorld;
