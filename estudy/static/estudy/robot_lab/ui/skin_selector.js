/* skin_selector.js — Robot skin picker shown between levels and in settings */
'use strict';

const RRSkinSelector = (() => {
    class SkinSelector {
        constructor(container, { skins, activeSkin, onSelect }) {
            this._container = container;
            this._skins = skins || [];
            this._activeSkin = activeSkin || 'zipp';
            this._onSelect = onSelect || (() => {});
            this._render();
        }

        _render() {
            this._container.innerHTML = '';
            this._container.classList.add('rr-skin-selector');

            const title = document.createElement('h3');
            title.textContent = 'Alege-ti robotul';
            title.style.cssText = 'text-align:center;margin:0 0 16px;font-size:18px;color:#E2E8F0;';
            this._container.appendChild(title);

            const grid = document.createElement('div');
            grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:12px;';

            this._skins.forEach(skin => {
                const card = document.createElement('div');
                card.style.cssText = `
                    display:flex;flex-direction:column;align-items:center;gap:8px;
                    padding:12px;border-radius:12px;border:2px solid ${skin.key === this._activeSkin ? '#22C55E' : '#334155'};
                    background:#1E293B;cursor:${skin.unlocked ? 'pointer' : 'not-allowed'};
                    opacity:${skin.unlocked ? '1' : '0.4'};transition:border-color 0.2s;
                `;

                const preview = document.createElement('div');
                preview.style.cssText = 'width:60px;height:60px;border-radius:50%;background:#0F172A;overflow:hidden;display:flex;align-items:center;justify-content:center;';
                if (skin.unlocked) {
                    preview.innerHTML = `<img src="/static/estudy/robot_lab/svg/${skin.svg_file}" width="48" height="48" alt="${skin.name}" style="filter:${skin.unlocked ? 'none' : 'brightness(0)'}"/>`;
                } else {
                    preview.innerHTML = '<svg width="24" height="24" style="color:#64748B"><use href="#icon-lock"/></svg>';
                }
                card.appendChild(preview);

                const name = document.createElement('div');
                name.style.cssText = 'font-weight:700;font-size:13px;color:#E2E8F0;';
                name.textContent = skin.name;
                card.appendChild(name);

                if (skin.key === this._activeSkin) {
                    const badge = document.createElement('div');
                    badge.style.cssText = 'font-size:10px;color:#22C55E;font-weight:600;';
                    badge.textContent = 'SELECTAT';
                    card.appendChild(badge);
                } else if (!skin.unlocked) {
                    const hint = document.createElement('div');
                    hint.style.cssText = 'font-size:10px;color:#94A3B8;text-align:center;';
                    hint.textContent = skin.unlock_condition ? `Completeaza ${skin.unlock_condition.replace('complete_', '').replace(/_/g, ' ')}` : '';
                    card.appendChild(hint);
                }

                if (skin.unlocked && skin.key !== this._activeSkin) {
                    card.addEventListener('click', () => {
                        this._activeSkin = skin.key;
                        this._onSelect(skin.key);
                        this._render();
                    });
                }

                grid.appendChild(card);
            });

            this._container.appendChild(grid);
        }

        setActive(key) {
            this._activeSkin = key;
            this._render();
        }

        destroy() { this._container.innerHTML = ''; }
    }

    return { SkinSelector };
})();

if (typeof window !== 'undefined') window.RRSkinSelector = RRSkinSelector;
