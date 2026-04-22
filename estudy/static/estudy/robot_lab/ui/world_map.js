/* world_map.js — Animated world selection screen with immersive space effects */
'use strict';

const RRWorldMap = (() => {
    class WorldMap {
        constructor(container, { worlds, onWorldSelect, onLevelSelect }) {
            this._container = container;
            this._worlds = worlds || [];
            this._onWorldSelect = onWorldSelect || (() => {});
            this._onLevelSelect = onLevelSelect || (() => {});
            this._levelSelectEl = null;
            this._render();
        }

        _render() {
            const totals = this._worlds.reduce((acc, w) => {
                acc.stars += (w.stars || 0);
                acc.max += (w.max_stars || 0);
                if (w.completed) acc.done += 1;
                if (w.unlocked) acc.unlocked += 1;
                return acc;
            }, { stars: 0, max: 0, done: 0, unlocked: 0 });
            const totalPct = totals.max ? Math.round((totals.stars / totals.max) * 100) : 0;
            const worldsTotal = this._worlds.length;

            this._container.innerHTML = `
                <div class="rr-world-map">
                    <div class="rr-shooting-star"></div>
                    <div class="rr-shooting-star"></div>
                    <div class="rr-shooting-star"></div>
                    <div class="rr-world-map__header">
                        <div class="rr-world-map__title">ROBO RESCUE</div>
                        <div class="rr-world-map__subtitle">Planeta Zeta-9 are nevoie de tine!</div>
                        <div class="rr-world-map__summary">
                            <div class="rr-wm-chip">
                                <svg class="rr-wm-chip__icon"><use href="#icon-star"/></svg>
                                <span>${totals.stars}/${totals.max}</span>
                            </div>
                            <div class="rr-wm-chip">&#127758; ${totals.done}/${worldsTotal} lumi</div>
                            <div class="rr-wm-chip rr-wm-chip--bar">
                                <div class="rr-wm-chip__bar"><div class="rr-wm-chip__bar-fill" style="width:${totalPct}%"></div></div>
                                <span>${totalPct}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="rr-world-map__planet">
                        <div class="rr-world-map__planet-bg"></div>
                        <div class="rr-world-map__worlds" data-rr-worlds></div>
                    </div>
                </div>
            `;

            const worldsContainer = this._container.querySelector('[data-rr-worlds]');
            this._worlds.forEach(world => {
                const bubble = document.createElement('div');
                bubble.className = 'rr-world-bubble';
                bubble.dataset.world = world.world_id;
                if (!world.unlocked) bubble.classList.add('is-locked');

                const themeMap = { 1: 'garden', 2: 'ice', 3: 'volcano', 4: 'space', 5: 'core' };
                const theme = themeMap[world.world_id] || 'garden';

                const starPct = world.max_stars
                    ? Math.round((world.stars / world.max_stars) * 100)
                    : 0;
                const unlockHint = world.unlock_hint || '';

                bubble.innerHTML = `
                    <div class="rr-world-bubble__icon">
                        <svg><use href="#world-${theme}"/></svg>
                    </div>
                    <div class="rr-world-bubble__name">${world.name}</div>
                    <div class="rr-world-bubble__stars">
                        <svg><use href="#icon-star"/></svg>
                        ${world.stars}/${world.max_stars}
                    </div>
                    ${world.unlocked ? `
                    <div class="rr-world-bubble__progress">
                        <div class="rr-world-bubble__progress-fill" style="width:${starPct}%"></div>
                    </div>` : ''}
                    ${!world.unlocked ? `
                    <svg class="rr-world-bubble__lock"><use href="#icon-lock"/></svg>
                    ${unlockHint ? `<div class="rr-world-bubble__hint">${unlockHint}</div>` : ''}
                    ` : ''}
                `;

                if (world.unlocked) {
                    bubble.addEventListener('click', () => {
                        this._onWorldSelect(world);
                        this._showLevelSelect(world);
                    });
                }

                worldsContainer.appendChild(bubble);
            });
        }

        _showLevelSelect(world) {
            if (this._levelSelectEl) this._levelSelectEl.remove();

            this._levelSelectEl = document.createElement('div');
            this._levelSelectEl.className = 'rr-level-select rr-theme--' + (world.theme || 'garden');

            const title = document.createElement('div');
            title.className = 'rr-level-select__title';
            title.textContent = world.name;
            this._levelSelectEl.appendChild(title);

            const grid = document.createElement('div');
            grid.className = 'rr-level-select__grid';

            const levelIds = world.level_ids || [];
            const completedLevels = world.completed_levels || [];
            const starData = world.level_stars || {};
            const titleData = world.level_titles || {};
            const xpData = world.level_xp || {};

            levelIds.forEach((levelId, i) => {
                if (i > 0) {
                    const path = document.createElement('div');
                    path.className = 'rr-level-path';
                    if (i <= completedLevels.length) path.classList.add('is-unlocked');
                    grid.appendChild(path);
                }

                const isComplete = completedLevels.indexOf(levelId) !== -1;
                const isLocked = i > completedLevels.length;
                const stars = starData[levelId] || 0;
                const title = titleData[levelId] || '';
                const xp = xpData[levelId] || 0;

                const node = document.createElement('div');
                node.className = 'rr-level-node';
                if (isComplete) node.classList.add('is-complete');
                if (isLocked) node.classList.add('is-locked');

                const starIcons = [1, 2, 3].map(s =>
                    `<svg class="rr-level-node__star${s <= stars ? ' is-earned' : ''}"><use href="#icon-star${s <= stars ? '' : '-empty'}"/></svg>`
                ).join('');

                node.innerHTML = `
                    <div class="rr-level-node__circle">${isComplete ? '&#10003;' : i + 1}</div>
                    ${title ? `<div class="rr-level-node__name">${title}</div>` : ''}
                    ${xp && !isLocked ? `<div class="rr-level-node__xp">&#9889; ${xp}</div>` : ''}
                    <div class="rr-level-node__stars">${starIcons}</div>
                `;

                if (!isLocked) {
                    node.addEventListener('click', () => {
                        if (window.RRAudio) RRAudio.play('click');
                        this._onLevelSelect(levelId);
                    });
                }

                grid.appendChild(node);
            });

            this._levelSelectEl.appendChild(grid);

            const backBtn = document.createElement('button');
            backBtn.className = 'rr-level-select__back';
            backBtn.textContent = '\u2190 Inapoi la harta';
            backBtn.addEventListener('click', () => {
                this._levelSelectEl.remove();
                this._levelSelectEl = null;
            });
            this._levelSelectEl.appendChild(backBtn);

            document.body.appendChild(this._levelSelectEl);
        }

        destroy() {
            if (this._levelSelectEl) this._levelSelectEl.remove();
            this._container.innerHTML = '';
        }
    }

    return { WorldMap };
})();

if (typeof window !== 'undefined') window.RRWorldMap = RRWorldMap;
