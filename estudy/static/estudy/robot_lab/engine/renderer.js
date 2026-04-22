/* renderer.js — CSS Grid maze renderer, handles all tile types, robot overlay */
'use strict';

const RRRenderer = (() => {
    const TILE_CLASS_MAP = {
        wall: 'rr-tile--wall', floor: 'rr-tile--floor', start: 'rr-tile--start',
        goal: 'rr-tile--goal', terminal: 'rr-tile--terminal',
        battery: 'rr-tile--battery', key: 'rr-tile--key', door: 'rr-tile--door',
        hazard: 'rr-tile--hazard', ice: 'rr-tile--ice', heater: 'rr-tile--heater',
        lava: 'rr-tile--lava', coolant: 'rr-tile--coolant', portal: 'rr-tile--portal',
    };

    class Renderer {
        constructor(container) {
            this._container = container;
            this._gridEl = null;
            this._robotEl = null;
            this._world = null;
        }

        mount(world) {
            this._world = world;
            this._container.innerHTML = '';

            // Grid
            this._gridEl = document.createElement('div');
            this._gridEl.className = 'rr-grid';
            this._gridEl.style.gridTemplateColumns = `repeat(${world.cols}, var(--rr-tile-size, 60px))`;
            this._gridEl.style.position = 'relative';

            for (let r = 0; r < world.rows; r++) {
                for (let c = 0; c < world.cols; c++) {
                    const tile = document.createElement('div');
                    tile.className = 'rr-tile';
                    tile.dataset.row = r;
                    tile.dataset.col = c;
                    const type = world.tileType(r, c);
                    const cls = TILE_CLASS_MAP[type] || 'rr-tile--floor';
                    tile.classList.add(cls);
                    this._gridEl.appendChild(tile);
                }
            }

            // Robot overlay
            this._robotEl = document.createElement('div');
            this._robotEl.className = 'rr-robot rr-robot--idle';
            this._robotEl.innerHTML = '<div class="rr-robot__sprite"></div>';
            this._gridEl.appendChild(this._robotEl);

            this._container.appendChild(this._gridEl);
        }

        updateRobot(robot) {
            if (!this._robotEl || !this._world) return;

            var tileSize = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--rr-tile-size')) || 60;
            var gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--rr-tile-gap')) || 1;
            var x = robot.col * (tileSize + gap);
            var y = robot.row * (tileSize + gap);

            // Use left/top for positioning so CSS animations on transform don't conflict
            this._robotEl.style.left = x + 'px';
            this._robotEl.style.top = y + 'px';
            this._robotEl.dataset.dir = robot.dir;

            // Update state class
            this._robotEl.className = 'rr-robot rr-robot--' + robot.skin + ' rr-robot--' + robot.state;
        }

        updateTile(r, c, type) {
            if (!this._gridEl || !this._world) return;
            const idx = r * this._world.cols + c;
            const tile = this._gridEl.children[idx];
            if (!tile || tile === this._robotEl) return;

            // Remove old type classes
            Object.values(TILE_CLASS_MAP).forEach(cls => tile.classList.remove(cls));
            const cls = TILE_CLASS_MAP[type] || 'rr-tile--floor';
            tile.classList.add(cls);
        }

        updateLavaPhase(safe) {
            if (!this._gridEl) return;
            const lavaTiles = this._gridEl.querySelectorAll('.rr-tile--lava');
            lavaTiles.forEach(tile => {
                tile.classList.toggle('is-safe', safe);
            });
        }

        highlightTile(r, c, className) {
            if (!this._gridEl || !this._world) return;
            const idx = r * this._world.cols + c;
            const tile = this._gridEl.children[idx];
            if (tile) tile.classList.add(className);
        }

        clearHighlights(className) {
            if (!this._gridEl) return;
            this._gridEl.querySelectorAll(`.${className}`).forEach(el => el.classList.remove(className));
        }

        destroy() {
            this._container.innerHTML = '';
            this._gridEl = null;
            this._robotEl = null;
            this._world = null;
        }
    }

    return { Renderer };
})();

if (typeof window !== 'undefined') window.RRRenderer = RRRenderer;
