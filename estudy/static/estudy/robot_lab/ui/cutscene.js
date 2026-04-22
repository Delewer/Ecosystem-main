/* cutscene.js — Simple story panels shown before World 1 and between worlds */
'use strict';

const RRCutscene = (() => {
    const SCENES = {
        intro: [
            { text: 'Planeta Zeta-9 e in pericol! Robotii rebeli au stricat reteaua de energie.', bg: '#064E3B' },
            { text: 'Tu il controlezi pe ZIPP — un mic robot de reparatii trimis sa salveze planeta.', bg: '#0F172A' },
            { text: 'Traverseaza sectoare periculoase, rezolva puzzle-uri si restaureaza energia!', bg: '#1E293B' },
        ],
        world_2_unlock: [
            { text: 'ZIPP: Gradina e restaurata! Dar urmatorul sector e inghetat complet.', bg: '#0C2D48' },
            { text: 'ZIPP: Pestera de Gheata ma asteapta. Pardoseala e alunecoasa — am nevoie de bucle!', bg: '#1E3A5F' },
        ],
        world_3_unlock: [
            { text: 'ZIPP: Gheata s-a topit! Dar detectez temperaturi extreme in sectorul urmator.', bg: '#451A03' },
            { text: 'ZIPP: Vulcanul! Lava se activeaza si dezactiveaza — trebuie sa gandesc cu conditii.', bg: '#78350F' },
        ],
        world_4_unlock: [
            { text: 'ZIPP: Vulcanul e stabil! Semnalul vine din spatiu acum.', bg: '#0F0A2A' },
            { text: 'ZIPP: Statia Spatiala! Portaluri si gravitatie zero — am nevoie de functii!', bg: '#1E1B4B' },
        ],
        world_5_unlock: [
            { text: 'ZIPP: Statia e online! Dar nucleul central e inca corupt.', bg: '#1C1917' },
            { text: 'ZIPP: Nucleul Final! Tot ce am invatat va fi pus la incercare!', bg: '#292524' },
        ],
    };

    let _overlay = null;
    let _panelIndex = 0;
    let _panels = [];
    let _resolve = null;
    let _typeTimer = null;
    let _isTyping = false;

    function _clearTypewriter() {
        if (_typeTimer) {
            clearInterval(_typeTimer);
            _typeTimer = null;
        }
        _isTyping = false;
    }

    function _finishCurrentPanel() {
        const content = _overlay ? _overlay.querySelector('[data-rr-cutscene-text]') : null;
        const panel = _panels[_panelIndex];
        _clearTypewriter();
        if (content && panel) content.textContent = panel.text;
    }

    function _typeWriter(el, text, speed) {
        _clearTypewriter();
        el.textContent = '';
        let i = 0;
        _isTyping = true;
        _typeTimer = setInterval(() => {
            if (!_overlay || !_overlay.parentNode) {
                _clearTypewriter();
                return;
            }
            if (i < text.length) {
                i++;
                el.textContent = text.slice(0, i);
                if (i >= text.length) _clearTypewriter();
                return;
            }
            _clearTypewriter();
        }, speed || 30);
    }

    function _showPanel(index) {
        if (index >= _panels.length) {
            _close();
            return;
        }
        _panelIndex = index;
        const panel = _panels[index];

        const content = _overlay.querySelector('[data-rr-cutscene-text]');
        const bg = _overlay.querySelector('[data-rr-cutscene-bg]');
        const counter = _overlay.querySelector('[data-rr-cutscene-counter]');

        if (bg) bg.style.background = panel.bg || '#0F172A';
        if (counter) counter.textContent = `${index + 1} / ${_panels.length}`;
        if (content) _typeWriter(content, panel.text, 25);
    }

    function _close() {
        _clearTypewriter();
        if (_overlay && _overlay.parentNode) _overlay.parentNode.removeChild(_overlay);
        _overlay = null;
        if (_resolve) { _resolve(); _resolve = null; }
    }

    function _handleNext() {
        if (_isTyping) {
            _finishCurrentPanel();
            return;
        }
        _showPanel(_panelIndex + 1);
    }

    function play(sceneKey) {
        _panels = SCENES[sceneKey] || [];
        if (!_panels.length) return Promise.resolve();
        if (_overlay) _close();

        return new Promise(resolve => {
            _resolve = resolve;
            _panelIndex = 0;

            _overlay = document.createElement('div');
            _overlay.style.cssText = `
                position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;
                align-items:center;justify-content:center;gap:24px;
            `;
            _overlay.innerHTML = `
                <div data-rr-cutscene-bg style="position:absolute;inset:0;transition:background 0.5s;"></div>
                <div style="position:relative;max-width:600px;padding:32px;text-align:center;z-index:1;">
                    <p data-rr-cutscene-text style="font-size:20px;line-height:1.6;color:#E2E8F0;min-height:80px;"></p>
                    <div style="margin-top:16px;font-size:12px;color:#94A3B8;" data-rr-cutscene-counter></div>
                    <div style="margin-top:24px;display:flex;gap:12px;justify-content:center;">
                        <button data-rr-cutscene-next class="rr-btn rr-btn--primary">Continua →</button>
                        <button data-rr-cutscene-skip class="rr-btn">Sari peste</button>
                    </div>
                </div>
            `;

            _overlay.querySelector('[data-rr-cutscene-next]').addEventListener('click', _handleNext);
            _overlay.querySelector('[data-rr-cutscene-skip]').addEventListener('click', _close);

            document.body.appendChild(_overlay);
            _showPanel(0);
        });
    }

    return { play, SCENES };
})();

if (typeof window !== 'undefined') window.RRCutscene = RRCutscene;
