/* eslint-env browser */

/**
 * RoboMentor — Animated SVG robot character for Robot Lab.
 *
 * States: idle, thinking, success, error, hint
 * Usage:
 *   RoboMentor.mount(containerElement)
 *   RoboMentor.setState('thinking')
 *   RoboMentor.setState('success', 'Bravo! Robotul a ajuns!')
 *   RoboMentor.setState('error', 'Aproape! Verifica pasul 3.')
 *   RoboMentor.setState('hint', 'Incearca sa...')
 */
(() => {
    'use strict';

    const SVG_NS = 'http://www.w3.org/2000/svg';
    const STATES = ['idle', 'thinking', 'success', 'error', 'hint'];
    const BLINK_INTERVAL_MS = 3200;
    const BLINK_DURATION_MS = 180;

    let _container = null;
    let _root = null;
    let _bubble = null;
    let _bubbleText = null;
    let _blinkTimer = null;
    let _currentState = 'idle';

    /* ── SVG construction ───────────────────────────────────── */

    const _buildSVG = () => {
        const svg = document.createElementNS(SVG_NS, 'svg');
        svg.setAttribute('viewBox', '0 0 120 140');
        svg.setAttribute('width', '120');
        svg.setAttribute('height', '140');
        svg.setAttribute('aria-hidden', 'true');
        svg.classList.add('robo-mentor__svg');

        svg.innerHTML = [
            /* antenna */
            '<g class="robo-mentor__antenna" data-robo-antenna>',
            '  <line x1="60" y1="10" x2="60" y2="30" stroke="#64748B" stroke-width="3" stroke-linecap="round"/>',
            '  <circle cx="60" cy="8" r="5" fill="#3B82F6" class="robo-mentor__antenna-tip"/>',
            '</g>',
            /* head */
            '<rect class="robo-mentor__head" x="25" y="30" width="70" height="55" rx="14" fill="#1E293B" stroke="#3B82F6" stroke-width="2"/>',
            /* eyes */
            '<g class="robo-mentor__eyes" data-robo-eyes>',
            '  <ellipse cx="44" cy="55" rx="8" ry="9" fill="#3B82F6" class="robo-mentor__eye robo-mentor__eye--left"/>',
            '  <ellipse cx="76" cy="55" rx="8" ry="9" fill="#3B82F6" class="robo-mentor__eye robo-mentor__eye--right"/>',
            '  <circle cx="46" cy="53" r="2.5" fill="#fff" opacity="0.8"/>',
            '  <circle cx="78" cy="53" r="2.5" fill="#fff" opacity="0.8"/>',
            '</g>',
            /* mouth */
            '<rect class="robo-mentor__mouth" x="42" y="72" width="36" height="4" rx="2" fill="#64748B"/>',
            /* body */
            '<rect class="robo-mentor__body" x="30" y="90" width="60" height="40" rx="10" fill="#1E293B" stroke="#3B82F6" stroke-width="2"/>',
            /* body light */
            '<circle cx="60" cy="110" r="5" fill="#3B82F6" opacity="0.6" class="robo-mentor__core"/>',
        ].join('\n');

        return svg;
    };

    const _buildBubble = () => {
        const wrap = document.createElement('div');
        wrap.className = 'robo-mentor__bubble';
        wrap.hidden = true;
        const text = document.createElement('p');
        text.className = 'robo-mentor__bubble-text';
        wrap.appendChild(text);
        return { wrap, text };
    };

    /* ── Blink logic (idle) ─────────────────────────────────── */

    const _startBlink = () => {
        _stopBlink();
        _blinkTimer = window.setInterval(() => {
            if (_currentState !== 'idle') return;
            _root?.classList.add('robo-mentor--blink');
            setTimeout(() => _root?.classList.remove('robo-mentor--blink'), BLINK_DURATION_MS);
        }, BLINK_INTERVAL_MS);
    };

    const _stopBlink = () => {
        if (_blinkTimer) {
            clearInterval(_blinkTimer);
            _blinkTimer = null;
        }
    };

    /* ── State management ───────────────────────────────────── */

    const _applyState = (state, message) => {
        if (!_root) return;

        STATES.forEach((s) => _root.classList.remove(`robo-mentor--${s}`));
        _root.classList.add(`robo-mentor--${state}`);
        _currentState = state;

        if (state === 'idle') {
            _startBlink();
        } else {
            _stopBlink();
        }

        if (message && _bubble && _bubbleText) {
            _bubbleText.textContent = message;
            _bubble.hidden = false;
        } else if (_bubble) {
            _bubble.hidden = true;
        }
    };

    /* ── Public API ─────────────────────────────────────────── */

    const mount = (container) => {
        if (!container) return;
        _container = container;

        _root = document.createElement('div');
        _root.className = 'robo-mentor robo-mentor--idle';
        _root.setAttribute('role', 'img');
        _root.setAttribute('aria-label', 'RoboMentor');

        _root.appendChild(_buildSVG());

        const bubbleParts = _buildBubble();
        _bubble = bubbleParts.wrap;
        _bubbleText = bubbleParts.text;
        _root.appendChild(_bubble);

        _container.appendChild(_root);
        _startBlink();
    };

    const setState = (state, message) => {
        if (!STATES.includes(state)) return;
        _applyState(state, message || '');
    };

    const getState = () => _currentState;

    const destroy = () => {
        _stopBlink();
        if (_root && _root.parentNode) {
            _root.parentNode.removeChild(_root);
        }
        _root = null;
        _bubble = null;
        _bubbleText = null;
        _container = null;
        _currentState = 'idle';
    };

    window.RoboMentor = { mount, setState, getState, destroy };
})();
