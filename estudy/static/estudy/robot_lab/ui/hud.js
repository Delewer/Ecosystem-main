/* hud.js — Heads-up display: star counter, step counter, timer, world/level info */
'use strict';

const RRHUD = (() => {
    let _el = null;
    let _timerInterval = null;
    let _seconds = 0;
    let _steps = 0;
    let _stars = [false, false, false];

    function mount(container, { worldName, levelTitle, onMenuClick, onSoundToggle }) {
        _el = document.createElement('div');
        _el.className = 'rr-hud';
        _el.innerHTML = `
            <button class="rr-hud__menu" data-rr-menu aria-label="Meniu">
                <svg class="rr-btn__icon"><use href="#icon-menu"/></svg>
            </button>
            <span class="rr-hud__title">ROBO RESCUE</span>
            <span class="rr-hud__level" data-rr-level></span>
            <div class="rr-hud__stars" data-rr-stars>
                <svg class="rr-hud__star"><use href="#icon-star-empty"/></svg>
                <svg class="rr-hud__star"><use href="#icon-star-empty"/></svg>
                <svg class="rr-hud__star"><use href="#icon-star-empty"/></svg>
            </div>
            <div class="rr-hud__separator"></div>
            <div class="rr-hud__stat">Pasi: <span class="rr-hud__stat-value" data-rr-steps>0</span></div>
            <div class="rr-hud__stat rr-hud__timer" data-rr-timer>
                <svg class="rr-btn__icon" style="width:14px;height:14px"><use href="#icon-settings"/></svg>
                <span class="rr-hud__stat-value" data-rr-time>0:00</span>
            </div>
            <div class="rr-hud__spacer"></div>
            <button class="rr-hud__sound" data-rr-sound aria-label="Sunet">
                <svg class="rr-btn__icon"><use href="#icon-sound-on"/></svg>
            </button>
        `;
        container.prepend(_el);

        const levelEl = _el.querySelector('[data-rr-level]');
        if (levelEl) levelEl.textContent = `${worldName || ''} — ${levelTitle || ''}`;

        _el.querySelector('[data-rr-menu]')?.addEventListener('click', () => {
            if (onMenuClick) onMenuClick();
        });

        _el.querySelector('[data-rr-sound]')?.addEventListener('click', () => {
            if (onSoundToggle) onSoundToggle();
        });
    }

    function startTimer() {
        _seconds = 0;
        _updateTimerDisplay();
        _timerInterval = setInterval(() => {
            _seconds++;
            _updateTimerDisplay();
        }, 1000);
    }

    function stopTimer() {
        if (_timerInterval) {
            clearInterval(_timerInterval);
            _timerInterval = null;
        }
    }

    function resetTimer() {
        stopTimer();
        _seconds = 0;
        _updateTimerDisplay();
    }

    function _updateTimerDisplay() {
        if (!_el) return;
        const min = Math.floor(_seconds / 60);
        const sec = _seconds % 60;
        const timeEl = _el.querySelector('[data-rr-time]');
        if (timeEl) timeEl.textContent = `${min}:${String(sec).padStart(2, '0')}`;

        const timerEl = _el.querySelector('[data-rr-timer]');
        if (timerEl) {
            timerEl.classList.toggle('is-warning', _seconds > 120);
        }
    }

    function setSteps(count) {
        _steps = count;
        if (!_el) return;
        const stepsEl = _el.querySelector('[data-rr-steps]');
        if (stepsEl) stepsEl.textContent = String(count);
    }

    function setStars(earned) {
        _stars = [earned >= 1, earned >= 2, earned >= 3];
        if (!_el) return;
        const starsContainer = _el.querySelector('[data-rr-stars]');
        if (!starsContainer) return;
        const starEls = starsContainer.querySelectorAll('.rr-hud__star');
        starEls.forEach((el, i) => {
            el.innerHTML = _stars[i]
                ? '<use href="#icon-star"/>'
                : '<use href="#icon-star-empty"/>';
            el.classList.toggle('is-earned', _stars[i]);
        });
    }

    function setSoundIcon(muted) {
        if (!_el) return;
        const btn = _el.querySelector('[data-rr-sound]');
        if (!btn) return;
        btn.innerHTML = muted
            ? '<svg class="rr-btn__icon"><use href="#icon-sound-off"/></svg>'
            : '<svg class="rr-btn__icon"><use href="#icon-sound-on"/></svg>';
    }

    function destroy() {
        stopTimer();
        if (_el && _el.parentNode) _el.parentNode.removeChild(_el);
        _el = null;
    }

    return { mount, startTimer, stopTimer, resetTimer, setSteps, setStars, setSoundIcon, destroy };
})();

if (typeof window !== 'undefined') window.RRHUD = RRHUD;
