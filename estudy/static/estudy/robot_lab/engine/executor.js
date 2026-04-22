/* executor.js — Runs block commands or server-side Python execution step by step */
'use strict';

const RRExecutor = (() => {
    const SPEEDS = { '0.5x': 700, '1x': 350, '2x': 175, '3x': 90 };

    class Executor {
        constructor({ world, robot, renderer, audio, particles, onStep, onComplete }) {
            this._world = world;
            this._robot = robot;
            this._renderer = renderer;
            this._audio = audio || null;
            this._particles = particles || null;
            this._onStep = onStep || (() => {});
            this._onComplete = onComplete || (() => {});
            this._speed = '1x';
            this._trace = [];
            this._index = -1;
            this._timer = null;
            this._running = false;
        }

        setSpeed(speed) {
            if (SPEEDS[speed]) this._speed = speed;
        }

        loadTrace(trace, opts) {
            this._trace = Array.isArray(trace) ? trace : [];
            this._index = -1;
            this._running = false;
            this._solved = !!(opts && opts.solved);
        }

        runAll() {
            if (!this._trace.length || this._running) return;
            this._running = true;
            this._index = -1;
            this._stepLoop();
        }

        _stepLoop() {
            if (!this._running) return;
            this._index++;
            if (this._index >= this._trace.length) {
                this._running = false;
                this._onComplete({ solved: this._solved });
                return;
            }

            this._applyTraceEntry(this._trace[this._index]);
            this._onStep(this._index, this._trace[this._index]);

            this._timer = setTimeout(() => this._stepLoop(), SPEEDS[this._speed] || 350);
        }

        stepOnce() {
            if (this._running) return;
            this._index++;
            if (this._index >= this._trace.length) {
                this._index = this._trace.length - 1;
                return;
            }
            this._applyTraceEntry(this._trace[this._index]);
            this._onStep(this._index, this._trace[this._index]);

            if (this._index >= this._trace.length - 1) {
                this._onComplete({ solved: this._solved });
            }
        }

        pause() {
            this._running = false;
            if (this._timer) {
                clearTimeout(this._timer);
                this._timer = null;
            }
        }

        reset() {
            this.pause();
            this._index = -1;
            const startPos = this._world.startPos;
            this._robot.reset(startPos.r, startPos.c, this._world.startDir);
            this._renderer.updateRobot(this._robot);
        }

        _applyTraceEntry(entry) {
            if (!entry) return;

            const pos = Array.isArray(entry.position) ? entry.position : [this._robot.row, this._robot.col];
            const dir = entry.dir || this._robot.dir;
            const action = entry.action || '';
            const error = entry.error || '';

            // Apply position
            this._robot.moveTo(pos[0], pos[1]);
            this._robot.faceDirection(dir);

            // Advance world step (for lava timer)
            this._world.advanceStep();

            // Set animation state
            if (error) {
                this._robot.setState('error', 400);
                if (this._audio) this._audio.play('error');
                if (this._particles) this._particles.emit('sparks', pos[0], pos[1]);
            } else if (action === 'pick' || action === 'activate') {
                this._robot.setState('collecting', 400);
                if (this._audio) this._audio.play('collect');
                if (this._particles) this._particles.emit('stars', pos[0], pos[1]);
            } else if (action === 'turn_left' || action === 'turn_right') {
                this._robot.setState('turning', 250);
                if (this._audio) this._audio.play('move');
            } else {
                this._robot.setState('walking', 300);
                if (this._audio) this._audio.play('move');
            }

            // Update renderer
            this._renderer.updateRobot(this._robot);
            this._renderer.updateLavaPhase(this._world.lavaPhase);
        }

        get isRunning() { return this._running; }
        get currentIndex() { return this._index; }
        get traceLength() { return this._trace.length; }
    }

    return { Executor, SPEEDS };
})();

if (typeof window !== 'undefined') window.RRExecutor = RRExecutor;
