/* particles.js — CSS particle system: confetti, sparks, stars burst */
'use strict';

const RRParticles = (() => {
    let _container = null;

    function mount(container) {
        _container = container;
    }

    function _createParticle(x, y, color, size, dx, dy, duration) {
        if (!_container) return;
        const el = document.createElement('div');
        el.style.cssText = `
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            pointer-events: none;
            z-index: 100;
            will-change: transform, opacity;
        `;
        _container.appendChild(el);

        const anim = el.animate([
            { transform: 'translate(0, 0) scale(1)', opacity: 1 },
            { transform: `translate(${dx}px, ${dy}px) scale(0.2)`, opacity: 0 },
        ], { duration, easing: 'ease-out', fill: 'forwards' });

        anim.onfinish = () => el.remove();
    }

    function _rand(min, max) {
        return Math.random() * (max - min) + min;
    }

    const EFFECTS = {
        confetti(x, y) {
            const colors = ['#EF4444', '#3B82F6', '#22C55E', '#FBBF24', '#EC4899', '#8B5CF6'];
            for (let i = 0; i < 30; i++) {
                const angle = _rand(0, Math.PI * 2);
                const dist = _rand(40, 120);
                const dx = Math.cos(angle) * dist;
                const dy = Math.sin(angle) * dist;
                _createParticle(x, y, colors[i % colors.length], _rand(4, 8), dx, dy, 1200);
            }
        },

        sparks(x, y) {
            for (let i = 0; i < 6; i++) {
                const angle = _rand(0, Math.PI * 2);
                const dist = _rand(15, 40);
                const dx = Math.cos(angle) * dist;
                const dy = Math.sin(angle) * dist;
                _createParticle(x, y, '#9CA3AF', _rand(2, 5), dx, dy, 400);
            }
        },

        stars(x, y) {
            for (let i = 0; i < 8; i++) {
                const angle = _rand(-Math.PI, 0);
                const dist = _rand(20, 60);
                const dx = Math.cos(angle) * dist;
                const dy = Math.sin(angle) * dist - 30;
                _createParticle(x, y, '#FBBF24', _rand(3, 6), dx, dy, 600);
            }
        },

        fullscreen_confetti() {
            if (!_container) return;
            const rect = _container.getBoundingClientRect();
            const colors = ['#EF4444', '#3B82F6', '#22C55E', '#FBBF24', '#EC4899', '#8B5CF6', '#F97316'];
            for (let i = 0; i < 50; i++) {
                const x = _rand(0, rect.width);
                const dy = _rand(rect.height * 0.6, rect.height);
                const dx = _rand(-80, 80);
                _createParticle(x, -10, colors[i % colors.length], _rand(4, 10), dx, dy, _rand(1500, 3000));
            }
        },
    };

    function emit(effectName, tileRow, tileCol) {
        const fn = EFFECTS[effectName];
        if (!fn) return;

        if (effectName === 'fullscreen_confetti') {
            fn();
            return;
        }

        // Convert tile coords to pixel position relative to container
        const tileSize = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--rr-tile-size')) || 60;
        const gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--rr-tile-gap')) || 1;
        const x = tileCol * (tileSize + gap) + tileSize / 2;
        const y = tileRow * (tileSize + gap) + tileSize / 2;

        fn(x, y);
    }

    return { mount, emit };
})();

if (typeof window !== 'undefined') window.RRParticles = RRParticles;
