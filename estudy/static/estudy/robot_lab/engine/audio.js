/* audio.js — Web Audio API procedural sound engine (zero audio files) */
'use strict';

const RRAudio = (() => {
    let _ctx = null;
    let _muted = false;

    function _getCtx() {
        if (_ctx) return _ctx;
        try {
            _ctx = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            _ctx = null;
        }
        return _ctx;
    }

    function _playNotes(freqs, durations, type, gain) {
        const ctx = _getCtx();
        if (!ctx || _muted) return;

        let t = ctx.currentTime + 0.01;
        const vol = ctx.createGain();
        vol.gain.value = gain || 0.12;
        vol.connect(ctx.destination);

        for (let i = 0; i < freqs.length; i++) {
            const osc = ctx.createOscillator();
            osc.type = type || 'sine';
            osc.frequency.value = freqs[i];
            osc.connect(vol);
            osc.start(t);
            const dur = durations[i] || 0.1;
            osc.stop(t + dur);
            t += dur;
        }
    }

    const SOUNDS = {
        move: () => _playNotes([440], [0.04], 'sine', 0.06),
        wall_hit: () => _playNotes([150, 120], [0.08, 0.12], 'sawtooth', 0.1),
        collect: () => _playNotes([880, 1100, 1320], [0.05, 0.05, 0.15], 'triangle', 0.1),
        goal: () => _playNotes([523, 659, 784], [0.1, 0.1, 0.2], 'sine', 0.12),
        error: () => _playNotes([200, 150], [0.15, 0.25], 'sawtooth', 0.08),
        victory: () => _playNotes([523, 659, 784, 1047, 1318], [0.1, 0.1, 0.1, 0.1, 0.4], 'sine', 0.15),
        unlock: () => _playNotes([440, 554, 659, 880], [0.08, 0.08, 0.08, 0.2], 'triangle', 0.12),
        click: () => _playNotes([600], [0.03], 'sine', 0.04),
    };

    function play(name) {
        const fn = SOUNDS[name];
        if (fn) fn();
    }

    function mute() { _muted = true; }
    function unmute() { _muted = false; }
    function toggleMute() { _muted = !_muted; return _muted; }
    function isMuted() { return _muted; }

    function resume() {
        const ctx = _getCtx();
        if (ctx && ctx.state === 'suspended') {
            ctx.resume();
        }
    }

    return { play, mute, unmute, toggleMute, isMuted, resume };
})();

if (typeof window !== 'undefined') window.RRAudio = RRAudio;
