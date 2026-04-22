/* lesson.js — Interactive step-based lesson engine (bright & playful) */
'use strict';
(() => {
    const root = document.querySelector('[data-lesson]');
    if (!root) return;

    const slug = root.dataset.lessonSlug || '';
    const steps = Array.from(root.querySelectorAll('.lesson-step'));
    const dots = Array.from(root.querySelectorAll('.lesson-hud__dot'));
    const xpEl = root.querySelector('[data-ls-xp-val]');
    const totalXp = parseInt(root.dataset.xpReward || '50', 10);

    let currentStep = 0;
    let earnedXp = 0;
    let completedSteps = new Set();

    const cheerMessages = [
        'Super! 🎉', 'Excelent! 🌟', 'Bravo! 💪', 'Minunat! ✨',
        'Continuă tot așa! 🚀', 'Ești grozav! 🏆', 'Fantastic! 🎯',
    ];

    // --- Sound Effects (Web Audio API) ---
    const LessonAudio = (() => {
        let ctx = null;
        function getCtx() {
            if (!ctx) {
                try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e) {}
            }
            return ctx;
        }
        function play(freq, duration, type, vol) {
            const c = getCtx(); if (!c) return;
            if (c.state === 'suspended') c.resume();
            const osc = c.createOscillator();
            const gain = c.createGain();
            osc.type = type || 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(vol || 0.12, c.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + duration);
            osc.connect(gain); gain.connect(c.destination);
            osc.start(); osc.stop(c.currentTime + duration);
        }
        return {
            click: () => play(800, 0.06, 'sine', 0.08),
            stepNext: () => { play(523, 0.08, 'sine', 0.1); setTimeout(() => play(659, 0.08, 'sine', 0.1), 60); },
            stepPrev: () => { play(659, 0.08, 'sine', 0.1); setTimeout(() => play(523, 0.08, 'sine', 0.1), 60); },
            correct: () => { play(523, 0.12, 'sine', 0.12); setTimeout(() => play(659, 0.12, 'sine', 0.12), 100); setTimeout(() => play(784, 0.15, 'sine', 0.12), 200); },
            wrong: () => { play(300, 0.15, 'sawtooth', 0.08); setTimeout(() => play(250, 0.2, 'sawtooth', 0.06), 120); },
            xp: () => play(1047, 0.1, 'sine', 0.08),
            achievement: () => { [523,659,784,1047].forEach((f,i) => setTimeout(() => play(f, 0.15, 'sine', 0.1), i*100)); },
            complete: () => { [523,659,784,1047,1319].forEach((f,i) => setTimeout(() => play(f, 0.2, 'triangle', 0.1), i*120)); },
            combo: () => { play(880, 0.08, 'square', 0.06); setTimeout(() => play(1100, 0.1, 'square', 0.06), 70); },
        };
    })();

    // --- State persistence ---
    const stateKey = 'ls-state-' + slug;
    function loadState() {
        try {
            const raw = localStorage.getItem(stateKey);
            if (!raw) return;
            const s = JSON.parse(raw);
            if (s.completedSteps) completedSteps = new Set(s.completedSteps);
            if (typeof s.earnedXp === 'number') earnedXp = s.earnedXp;
            if (typeof s.currentStep === 'number') currentStep = Math.min(s.currentStep, steps.length - 1);
        } catch (e) {}
    }
    function saveState() {
        try {
            localStorage.setItem(stateKey, JSON.stringify({
                completedSteps: [...completedSteps],
                earnedXp: earnedXp,
                currentStep: currentStep,
            }));
        } catch (e) {}
    }

    // --- Navigation ---
    function goToStep(idx) {
        if (idx < 0 || idx >= steps.length) return;
        const direction = idx >= currentStep ? 1 : -1;
        if (direction > 0) LessonAudio.stepNext(); else LessonAudio.stepPrev();
        steps.forEach(s => {
            s.classList.remove('is-active');
            s.style.animation = '';
        });
        const target = steps[idx];
        target.classList.add('is-active');
        target.style.animation = 'none';
        void target.offsetWidth;
        target.style.animation = direction > 0
            ? 'lk-slidein 0.5s cubic-bezier(0.22,1,0.36,1)'
            : 'lk-slideBack 0.5s cubic-bezier(0.22,1,0.36,1)';
        currentStep = idx;
        updateDots();
        saveState();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function updateDots() {
        dots.forEach((dot, i) => {
            dot.classList.toggle('is-active', i === currentStep);
            dot.classList.toggle('is-done', completedSteps.has(i));
        });
    }

    function completeStep(idx) {
        if (completedSteps.has(idx)) return;
        completedSteps.add(idx);
        const xpPerStep = Math.floor(totalXp / Math.max(steps.length - 1, 1));
        const award = idx === steps.length - 1 ? (totalXp - earnedXp) : xpPerStep;
        addXp(award);
        updateDots();
        saveState();

        // Celebrate dot
        if (dots[idx]) {
            dots[idx].style.animation = 'none';
            void dots[idx].offsetWidth;
            dots[idx].style.animation = 'lk-pop 0.5s cubic-bezier(0.22,1,0.36,1)';
        }

        // Show a cheer toast
        showCheerToast();
    }

    function addXp(amount) {
        if (amount <= 0) return;
        LessonAudio.xp();
        const from = earnedXp;
        earnedXp = Math.min(earnedXp + amount, totalXp);
        if (xpEl) animateCounter(xpEl, from, earnedXp, 600);
        // Floating +XP indicator
        showFloatingXp(amount);
    }

    function animateCounter(el, from, to, duration) {
        const start = performance.now();
        function tick(now) {
            const t = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - t, 3);
            el.textContent = Math.round(from + (to - from) * ease);
            if (t < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    function showFloatingXp(amount) {
        if (!xpEl) return;
        const rect = xpEl.getBoundingClientRect();
        const floater = document.createElement('div');
        floater.textContent = '+' + amount + ' XP';
        floater.style.cssText =
            'position:fixed;z-index:9999;pointer-events:none;font-family:Nunito,sans-serif;' +
            'font-weight:900;font-size:20px;color:#F59E0B;text-shadow:0 2px 4px rgba(0,0,0,0.15);' +
            'left:' + rect.left + 'px;top:' + rect.top + 'px;';
        document.body.appendChild(floater);
        floater.animate([
            { transform: 'translateY(0) scale(1)', opacity: 1 },
            { transform: 'translateY(-60px) scale(1.3)', opacity: 0 },
        ], { duration: 900, easing: 'cubic-bezier(0.22,1,0.36,1)' }).onfinish = () => floater.remove();
    }

    function showCheerToast() {
        const msg = cheerMessages[Math.floor(Math.random() * cheerMessages.length)];
        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.style.cssText =
            'position:fixed;bottom:30px;left:50%;transform:translateX(-50%);z-index:9999;' +
            'padding:14px 28px;border-radius:16px;font-family:Nunito,sans-serif;' +
            'font-weight:800;font-size:18px;color:#FFF;pointer-events:none;' +
            'background:linear-gradient(135deg,#7C3AED,#EC4899);' +
            'box-shadow:0 8px 24px rgba(124,58,237,0.35);';
        document.body.appendChild(toast);
        toast.animate([
            { transform: 'translateX(-50%) translateY(20px) scale(0.8)', opacity: 0 },
            { transform: 'translateX(-50%) translateY(0) scale(1)', opacity: 1 },
            { transform: 'translateX(-50%) translateY(0) scale(1)', opacity: 1 },
            { transform: 'translateX(-50%) translateY(-20px) scale(0.8)', opacity: 0 },
        ], { duration: 1800, easing: 'ease-out' }).onfinish = () => toast.remove();
    }

    function nextStep() {
        completeStep(currentStep);
        goToStep(currentStep + 1);
    }
    function prevStep() {
        goToStep(currentStep - 1);
    }

    // --- Event delegation ---
    root.addEventListener('click', function(e) {
        const btn = e.target.closest('[data-ls-action]');
        if (!btn) return;
        const action = btn.dataset.lsAction;
        if (action === 'next') nextStep();
        else if (action === 'prev') prevStep();
        else if (action === 'start') { completeStep(0); goToStep(1); }
        else if (action === 'goto' && btn.dataset.lsStep) goToStep(parseInt(btn.dataset.lsStep, 10));
    });

    // Dot clicks
    dots.forEach((dot, i) => {
        dot.addEventListener('click', () => goToStep(i));
    });

    // --- Quiz logic ---
    const quizForm = root.querySelector('[data-ls-quiz]');
    if (quizForm) {
        const opts = quizForm.querySelectorAll('.ls-quiz-opt');
        const fbEl = quizForm.querySelector('[data-ls-quiz-fb]');
        const correctAnswer = quizForm.dataset.lsCorrect || '';
        const explanation = quizForm.dataset.lsExplanation || '';
        const submitBtn = quizForm.querySelector('[data-ls-quiz-submit]');
        let quizAnswered = false;
        let selectedOpt = null;

        opts.forEach(opt => {
            opt.addEventListener('click', () => {
                if (quizAnswered) return;
                opts.forEach(o => o.classList.remove('is-selected'));
                opt.classList.add('is-selected');
                selectedOpt = opt;
                if (submitBtn) submitBtn.disabled = false;
            });
        });

        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                if (!selectedOpt || quizAnswered) return;
                quizAnswered = true;
                const answer = selectedOpt.dataset.lsAnswer || '';
                const isCorrect = answer === correctAnswer;

                opts.forEach(o => {
                    if (o.dataset.lsAnswer === correctAnswer) o.classList.add('is-correct');
                    else if (o === selectedOpt && !isCorrect) o.classList.add('is-wrong');
                });

                if (fbEl) {
                    fbEl.style.display = 'block';
                    if (isCorrect) {
                        fbEl.className = 'ls-quiz-fb ls-quiz-fb--ok';
                        fbEl.innerHTML = '<strong>Corect!</strong> ' + explanation;
                        completeStep(currentStep);
                        emitConfetti(submitBtn);
                        LessonAudio.correct();
                    } else {
                        fbEl.className = 'ls-quiz-fb ls-quiz-fb--no';
                        fbEl.innerHTML = '<strong>Nu chiar.</strong> Raspunsul corect e evidentiat. ' + explanation;
                        shakeElement(selectedOpt);
                        LessonAudio.wrong();
                    }
                }

                const testId = quizForm.dataset.lsTestId;
                const csrfToken = getCsrf();
                if (testId && csrfToken) {
                    fetch('/estudy/tests/' + testId + '/submit/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
                        body: 'answer=' + encodeURIComponent(answer) + '&time_taken_ms=0',
                    }).catch(() => {});
                }
            });
        }
    }

    // --- Practice drag-and-drop ---
    const practiceEl = root.querySelector('[data-ls-practice]');
    if (practiceEl) {
        const tokens = practiceEl.querySelectorAll('.ls-match-token');
        const slots = practiceEl.querySelectorAll('.ls-match-slot');
        const verifyBtn = practiceEl.querySelector('[data-ls-verify]');
        const resetBtn = practiceEl.querySelector('[data-ls-reset-practice]');

        tokens.forEach(token => {
            token.draggable = true;
            token.addEventListener('dragstart', e => {
                e.dataTransfer.setData('text/plain', token.dataset.lsToken);
                token.style.opacity = '0.5';
                token.classList.add('is-dragging');
            });
            token.addEventListener('dragend', () => {
                token.style.opacity = '';
                token.classList.remove('is-dragging');
            });

            // Click-to-place
            token.addEventListener('click', () => {
                if (token.classList.contains('is-placed')) return;
                const emptySlot = Array.from(slots).find(s => !s.dataset.lsFilled);
                if (emptySlot) {
                    emptySlot.textContent = token.textContent;
                    emptySlot.dataset.lsFilled = token.dataset.lsToken;
                    emptySlot.classList.add('is-filled');
                    token.classList.add('is-placed');
                    // Brief scale bounce on the slot
                    pulseElement(emptySlot);
                }
            });
        });

        slots.forEach(slot => {
            slot.addEventListener('dragover', e => { e.preventDefault(); slot.classList.add('is-over'); });
            slot.addEventListener('dragleave', () => slot.classList.remove('is-over'));
            slot.addEventListener('drop', e => {
                e.preventDefault();
                slot.classList.remove('is-over');
                const val = e.dataTransfer.getData('text/plain');
                if (!val) return;
                if (slot.dataset.lsFilled) {
                    const oldToken = practiceEl.querySelector('[data-ls-token="' + slot.dataset.lsFilled + '"]');
                    if (oldToken) oldToken.classList.remove('is-placed');
                }
                slot.textContent = '';
                const tokenEl = practiceEl.querySelector('[data-ls-token="' + val + '"]');
                if (tokenEl) {
                    slot.textContent = tokenEl.textContent;
                    tokenEl.classList.add('is-placed');
                }
                slot.dataset.lsFilled = val;
                slot.classList.add('is-filled');
                pulseElement(slot);
            });
            slot.addEventListener('click', () => {
                if (!slot.dataset.lsFilled) return;
                const tokenEl = practiceEl.querySelector('[data-ls-token="' + slot.dataset.lsFilled + '"]');
                if (tokenEl) tokenEl.classList.remove('is-placed');
                slot.dataset.lsFilled = '';
                slot.textContent = slot.dataset.lsPlaceholder || '';
                slot.classList.remove('is-filled', 'is-correct', 'is-wrong');
            });
        });

        if (verifyBtn) {
            verifyBtn.addEventListener('click', () => {
                let allCorrect = true;
                slots.forEach(slot => {
                    const filled = slot.dataset.lsFilled || '';
                    const expected = slot.dataset.lsExpect || '';
                    slot.classList.remove('is-correct', 'is-wrong');
                    if (filled === expected) {
                        slot.classList.add('is-correct');
                    } else {
                        slot.classList.add('is-wrong');
                        shakeElement(slot);
                        allCorrect = false;
                    }
                });
                if (allCorrect) {
                    completeStep(currentStep);
                    emitConfetti(verifyBtn);
                    LessonAudio.correct();
                } else {
                    LessonAudio.wrong();
                }
            });
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                tokens.forEach(t => t.classList.remove('is-placed'));
                slots.forEach(s => {
                    s.dataset.lsFilled = '';
                    s.textContent = s.dataset.lsPlaceholder || '';
                    s.classList.remove('is-filled', 'is-correct', 'is-wrong');
                });
            });
        }
    }

    // --- Code copy ---
    root.addEventListener('click', function(e) {
        const copyBtn = e.target.closest('.ls-code__copy');
        if (!copyBtn) return;
        const codeBlock = copyBtn.closest('.ls-code');
        if (!codeBlock) return;
        const text = codeBlock.textContent.replace(/Copiaza|Copiat!/, '').trim();
        navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = 'Copiat!';
            pulseElement(copyBtn);
            setTimeout(() => { copyBtn.textContent = 'Copiaza'; }, 1500);
        }).catch(() => {});
    });

    // --- Toggle completion ---
    root.addEventListener('click', function(e) {
        const completeBtn = e.target.closest('[data-ls-complete]');
        if (!completeBtn) return;
        completeStep(currentStep);
        emitConfetti(completeBtn);
        emitEmojiRain();
        LessonAudio.complete();

        const csrfToken = getCsrf();
        if (csrfToken) {
            fetch('/estudy/lessons/' + slug + '/toggle/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
                body: 'seconds=0',
            }).catch(() => {});
        }
    });

    // --- Confetti burst ---
    function emitConfetti(anchor) {
        const rect = anchor ? anchor.getBoundingClientRect()
            : { left: window.innerWidth / 2, top: window.innerHeight / 2 };
        const cx = rect.left + (rect.width || 0) / 2;
        const cy = rect.top + (rect.height || 0) / 2;
        const colors = ['#7C3AED', '#EC4899', '#10B981', '#F59E0B', '#3B82F6', '#EF4444'];
        const shapes = ['circle', 'square', 'star'];
        for (let i = 0; i < 36; i++) {
            const el = document.createElement('div');
            const shape = shapes[i % 3];
            const size = 6 + Math.random() * 6;
            const color = colors[i % colors.length];
            let css = 'position:fixed;pointer-events:none;z-index:9999;';
            css += 'left:' + cx + 'px;top:' + cy + 'px;';
            if (shape === 'circle') {
                css += 'width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:' + color + ';';
            } else if (shape === 'square') {
                css += 'width:' + size + 'px;height:' + size + 'px;border-radius:2px;background:' + color + ';';
            } else {
                css += 'width:0;height:0;background:none;font-size:' + (size + 4) + 'px;line-height:1;';
                el.textContent = '★';
                el.style.color = color;
            }
            el.style.cssText = css;
            document.body.appendChild(el);
            const angle = (Math.PI * 2 / 36) * i + (Math.random() - 0.5) * 0.5;
            const vel = 100 + Math.random() * 160;
            const dx = Math.cos(angle) * vel;
            const dy = Math.sin(angle) * vel - 80;
            const spin = (Math.random() - 0.5) * 720;
            el.animate([
                { transform: 'translate(0,0) rotate(0deg) scale(1)', opacity: 1 },
                { transform: 'translate(' + dx + 'px,' + dy + 'px) rotate(' + spin + 'deg) scale(0)', opacity: 0 },
            ], { duration: 800 + Math.random() * 500, easing: 'cubic-bezier(0.22,1,0.36,1)' })
            .onfinish = () => el.remove();
        }
    }

    // --- Emoji rain for lesson completion ---
    function emitEmojiRain() {
        const emojis = ['🎉', '🌟', '🏆', '💎', '🎊', '✨', '🚀', '🎯', '💪', '🥇'];
        for (let i = 0; i < 20; i++) {
            const el = document.createElement('div');
            el.textContent = emojis[i % emojis.length];
            el.style.cssText =
                'position:fixed;top:-40px;z-index:9998;pointer-events:none;font-size:28px;' +
                'left:' + (Math.random() * 100) + 'vw;';
            document.body.appendChild(el);
            const delay = Math.random() * 600;
            const duration = 2000 + Math.random() * 1500;
            const drift = (Math.random() - 0.5) * 100;
            el.animate([
                { transform: 'translateY(0) translateX(0) rotate(0deg)', opacity: 1 },
                { transform: 'translateY(110vh) translateX(' + drift + 'px) rotate(' + (360 + Math.random() * 360) + 'deg)', opacity: 0.3 },
            ], { duration: duration, delay: delay, easing: 'ease-in' })
            .onfinish = () => el.remove();
        }
    }

    // --- Micro-animations ---
    function shakeElement(el) {
        el.animate([
            { transform: 'translateX(0)' },
            { transform: 'translateX(-6px)' },
            { transform: 'translateX(6px)' },
            { transform: 'translateX(-4px)' },
            { transform: 'translateX(4px)' },
            { transform: 'translateX(0)' },
        ], { duration: 400, easing: 'ease-out' });
    }

    function pulseElement(el) {
        el.animate([
            { transform: 'scale(1)' },
            { transform: 'scale(1.08)' },
            { transform: 'scale(1)' },
        ], { duration: 300, easing: 'ease-out' });
    }

    // --- CSRF helper ---
    function getCsrf() {
        const raw = document.cookie || '';
        const parts = raw.split(';');
        for (let i = 0; i < parts.length; i++) {
            const item = parts[i].trim();
            if (item.startsWith('csrftoken=')) return decodeURIComponent(item.slice(10));
        }
        return '';
    }

    // --- Feature 10: Text-to-Speech ---
    const ttsBtn = root.querySelector('[data-ls-tts]');
    const ttsTextEl = root.querySelector('.ls-tts-text');
    if (ttsBtn && ttsTextEl && 'speechSynthesis' in window) {
        let speaking = false;
        ttsBtn.addEventListener('click', () => {
            if (speaking) {
                speechSynthesis.cancel();
                speaking = false;
                ttsBtn.innerHTML = '&#128264; Citeste';
                return;
            }
            const text = ttsTextEl.textContent || '';
            if (!text) return;
            const utter = new SpeechSynthesisUtterance(text);
            utter.lang = 'ro-RO';
            utter.rate = 0.9;
            utter.onend = () => { speaking = false; ttsBtn.innerHTML = '&#128264; Citeste'; };
            speechSynthesis.speak(utter);
            speaking = true;
            ttsBtn.innerHTML = '&#9724; Stop';
        });
    }

    // --- Feature 3: Smart Hints panel ---
    const hintsToggle = root.querySelector('[data-ls-hints-toggle]');
    const hintsDrawer = root.querySelector('[data-ls-hints-drawer]');
    const hintsMoreBtn = root.querySelector('[data-ls-hints-more]');
    if (hintsToggle && hintsDrawer) {
        hintsToggle.addEventListener('click', () => {
            const isOpen = !hintsDrawer.hidden;
            hintsDrawer.hidden = isOpen;
            hintsToggle.innerHTML = isOpen ? '&#128161; Ai nevoie de ajutor?' : '&#10006; Inchide';
        });
    }
    if (hintsMoreBtn) {
        let hintLevel = 1;
        hintsMoreBtn.addEventListener('click', () => {
            hintLevel++;
            const allHints = root.querySelectorAll('[data-ls-hint]');
            let revealed = 0;
            allHints.forEach(h => {
                if (parseInt(h.dataset.hintLevel, 10) <= hintLevel) {
                    h.hidden = false;
                    revealed++;
                }
            });
            if (revealed >= allHints.length) hintsMoreBtn.hidden = true;
        });
    }

    // --- Feature 6: Easter Eggs ---
    const eggContainer = root.querySelector('[data-ls-easter-eggs]');
    if (eggContainer) {
        const eggs = Array.from(eggContainer.querySelectorAll('[data-egg-trigger]'));
        const triggeredEggs = new Set();
        function checkEasterEggs(condition) {
            eggs.forEach(egg => {
                const trigger = egg.dataset.eggTrigger;
                if (triggeredEggs.has(trigger)) return;
                if (trigger === condition) {
                    triggeredEggs.add(trigger);
                    const msg = egg.dataset.eggMessage || 'Ai gasit un secret!';
                    const val = parseInt(egg.dataset.eggValue || '0', 10);
                    // Show easter egg toast
                    const toast = document.createElement('div');
                    toast.innerHTML = '&#127873; ' + msg + (val > 0 ? ' (+' + val + ' XP)' : '');
                    toast.style.cssText =
                        'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);z-index:9999;' +
                        'padding:16px 32px;border-radius:16px;font-family:Nunito,sans-serif;' +
                        'font-weight:800;font-size:16px;color:#FFF;pointer-events:none;' +
                        'background:linear-gradient(135deg,#F59E0B,#EF4444);' +
                        'box-shadow:0 8px 24px rgba(245,158,11,0.4);';
                    document.body.appendChild(toast);
                    toast.animate([
                        { transform: 'translateX(-50%) scale(0)', opacity: 0 },
                        { transform: 'translateX(-50%) scale(1.05)', opacity: 1 },
                        { transform: 'translateX(-50%) scale(1)', opacity: 1 },
                        { transform: 'translateX(-50%) scale(1)', opacity: 1 },
                        { transform: 'translateX(-50%) scale(0.9)', opacity: 0 },
                    ], { duration: 3000, easing: 'ease-out' }).onfinish = () => toast.remove();
                    if (val > 0) addXp(val);
                    emitConfetti(toast);
                }
            });
        }
        // Expose for triggering from other features
        root._checkEasterEggs = checkEasterEggs;
        // Auto-check common triggers
        const observer = new MutationObserver(() => {
            if (completedSteps.size >= steps.length - 1) checkEasterEggs('all_steps_completed');
        });
        observer.observe(root, { attributes: true, subtree: true });
        // Check on quiz correct
        root.addEventListener('click', e => {
            if (e.target.closest('[data-ls-quiz-submit]')) {
                setTimeout(() => {
                    if (root.querySelector('.ls-quiz-opt.is-correct.is-selected')) {
                        checkEasterEggs('quiz_first_try');
                    }
                }, 100);
            }
        });
    }

    // --- Feature 8: Quiz retry on wrong answer ---
    const retryPanel = root.querySelector('[data-ls-quiz-retry]');
    const retryBtn = root.querySelector('[data-ls-quiz-retry-btn]');
    if (retryPanel && retryBtn && quizForm) {
        // Show retry after wrong answer
        const origSubmit = quizForm.querySelector('[data-ls-quiz-submit]');
        if (origSubmit) {
            origSubmit.addEventListener('click', () => {
                setTimeout(() => {
                    if (root.querySelector('.ls-quiz-opt.is-wrong')) {
                        retryPanel.hidden = false;
                        retryPanel.style.animation = 'lk-slidein 0.5s ease-out';
                    }
                }, 300);
            });
        }
        retryBtn.addEventListener('click', () => {
            // Reset quiz state for retry
            const opts = quizForm.querySelectorAll('.ls-quiz-opt');
            const fb = quizForm.querySelector('[data-ls-quiz-fb]');
            const sub = quizForm.querySelector('[data-ls-quiz-submit]');
            opts.forEach(o => o.classList.remove('is-selected', 'is-correct', 'is-wrong'));
            if (fb) { fb.style.display = 'none'; fb.className = 'ls-quiz-fb'; }
            if (sub) sub.disabled = true;
            retryPanel.hidden = true;
            // Reset quizAnswered flag — we need to re-enable clicking
            // The quizAnswered flag is in closure scope, so we dispatch a custom event
            quizForm.dispatchEvent(new CustomEvent('ls:quiz-reset'));
        });
    }

    // Extend quiz to support reset
    if (quizForm) {
        quizForm.addEventListener('ls:quiz-reset', () => {
            // Re-run click handlers by patching quizAnswered
            // We accomplish this by replacing the quiz click handlers
            const opts = quizForm.querySelectorAll('.ls-quiz-opt');
            const submitBtn = quizForm.querySelector('[data-ls-quiz-submit]');
            const correctAnswer = quizForm.dataset.lsCorrect || '';
            const explanation = quizForm.dataset.lsExplanation || '';
            const fbEl = quizForm.querySelector('[data-ls-quiz-fb]');
            let selectedOpt = null;

            const newClickHandler = (opt) => () => {
                opts.forEach(o => o.classList.remove('is-selected'));
                opt.classList.add('is-selected');
                selectedOpt = opt;
                if (submitBtn) submitBtn.disabled = false;
            };

            opts.forEach(opt => {
                const clone = opt.cloneNode(true);
                opt.parentNode.replaceChild(clone, opt);
                clone.addEventListener('click', newClickHandler(clone));
            });

            if (submitBtn) {
                const newSubmit = submitBtn.cloneNode(true);
                submitBtn.parentNode.replaceChild(newSubmit, submitBtn);
                newSubmit.addEventListener('click', () => {
                    const sel = quizForm.querySelector('.ls-quiz-opt.is-selected');
                    if (!sel) return;
                    const answer = sel.dataset.lsAnswer || '';
                    const isCorrect = answer === correctAnswer;
                    quizForm.querySelectorAll('.ls-quiz-opt').forEach(o => {
                        if (o.dataset.lsAnswer === correctAnswer) o.classList.add('is-correct');
                        else if (o === sel && !isCorrect) o.classList.add('is-wrong');
                    });
                    if (fbEl) {
                        fbEl.style.display = 'block';
                        if (isCorrect) {
                            fbEl.className = 'ls-quiz-fb ls-quiz-fb--ok';
                            fbEl.innerHTML = '<strong>Corect!</strong> ' + explanation;
                            completeStep(currentStep);
                            emitConfetti(newSubmit);
                        } else {
                            fbEl.className = 'ls-quiz-fb ls-quiz-fb--no';
                            fbEl.innerHTML = '<strong>Nu chiar.</strong> Raspunsul corect e evidentiat. ' + explanation;
                            shakeElement(sel);
                            if (retryPanel) {
                                setTimeout(() => { retryPanel.hidden = false; }, 300);
                            }
                        }
                    }
                });
            }
        });
    }

    // --- Feature 2: Inline Code Playground ---
    root.querySelectorAll('[data-ls-code-exercise]').forEach(block => {
        const exId = block.dataset.exerciseId;
        const input = block.querySelector('[data-ls-code-input]');
        const runBtn = block.querySelector('[data-ls-code-run]');
        const output = block.querySelector('[data-ls-code-output]');
        const hintBtn = block.querySelector('[data-ls-code-hint]');
        const hintTexts = block.querySelectorAll('[data-code-hint]');
        const testIcons = block.querySelectorAll('[data-test-icon]');
        let hintIndex = 0;

        if (runBtn && input && output) {
            runBtn.addEventListener('click', async () => {
                output.textContent = 'Se ruleaza...';
                runBtn.disabled = true;
                try {
                    const resp = await fetch('/estudy/api/run-code/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                        body: JSON.stringify({ exercise_id: parseInt(exId, 10), code: input.value }),
                    });
                    const data = await resp.json();
                    if (!resp.ok) {
                        output.textContent = 'Eroare: ' + (data.error || 'Necunoscuta');
                        return;
                    }
                    let lines = [];
                    if (data.error) lines.push('Eroare: ' + data.error);
                    lines.push('Trecut: ' + data.passed + '/' + data.total);
                    lines.push('Timp: ' + data.execution_time_ms + ' ms');
                    (data.test_results || []).forEach((tr, idx) => {
                        lines.push('\nTest #' + (idx + 1) + ': ' + tr.description);
                        lines.push('  Asteptat: ' + tr.expected);
                        lines.push('  Actual: ' + tr.actual);
                        lines.push('  ' + (tr.passed ? '✅ Trecut' : '❌ Picat'));
                    });
                    output.textContent = lines.join('\n');

                    // Update test icons
                    (data.test_results || []).forEach((tr, idx) => {
                        if (testIcons[idx]) {
                            testIcons[idx].textContent = tr.passed ? '✅' : '❌';
                            testIcons[idx].dataset.testIcon = tr.passed ? 'pass' : 'fail';
                        }
                    });

                    if (data.passed === data.total && data.total > 0) {
                        completeStep(currentStep);
                        emitConfetti(runBtn);
                        if (root._checkEasterEggs) root._checkEasterEggs('code_all_tests_passed');
                    }
                } catch (err) {
                    output.textContent = 'Eroare: ' + err.message;
                } finally {
                    runBtn.disabled = false;
                }
            });
        }

        if (hintBtn && hintTexts.length) {
            hintBtn.addEventListener('click', () => {
                if (hintIndex < hintTexts.length) {
                    hintTexts[hintIndex].hidden = false;
                    hintIndex++;
                }
                if (hintIndex >= hintTexts.length) hintBtn.disabled = true;
            });
        }
    });

    // --- Feature 7: Reflection prompts ---
    root.querySelectorAll('[data-ls-reflection-scale]').forEach(scale => {
        const btns = scale.querySelectorAll('[data-scale-val]');
        btns.forEach(btn => {
            btn.addEventListener('click', () => {
                btns.forEach(b => b.classList.remove('is-selected'));
                btn.classList.add('is-selected');
                pulseElement(btn);
            });
        });
    });

    // Drawing canvas
    root.querySelectorAll('[data-ls-canvas]').forEach(canvas => {
        const ctx = canvas.getContext('2d');
        let drawing = false;
        ctx.strokeStyle = '#7C3AED';
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        canvas.addEventListener('pointerdown', e => { drawing = true; ctx.beginPath(); ctx.moveTo(e.offsetX, e.offsetY); });
        canvas.addEventListener('pointermove', e => { if (!drawing) return; ctx.lineTo(e.offsetX, e.offsetY); ctx.stroke(); });
        canvas.addEventListener('pointerup', () => { drawing = false; });
        canvas.addEventListener('pointerleave', () => { drawing = false; });
        const clearBtn = canvas.parentElement.querySelector('[data-ls-canvas-clear]');
        if (clearBtn) clearBtn.addEventListener('click', () => ctx.clearRect(0, 0, canvas.width, canvas.height));
    });

    // --- Streak / Combo system ---
    const streakEl = root.querySelector('[data-ls-streak]');
    const streakValEl = root.querySelector('[data-ls-streak-val]');
    let streak = 0;

    function bumpStreak() {
        streak++;
        LessonAudio.combo();
        if (streakEl && streakValEl) {
            streakEl.hidden = false;
            streakValEl.textContent = streak;
            streakEl.classList.remove('is-hot', 'is-fire', 'is-mega');
            if (streak >= 7) streakEl.classList.add('is-mega');
            else if (streak >= 4) streakEl.classList.add('is-fire');
            else if (streak >= 2) streakEl.classList.add('is-hot');
            // Pulse animation
            streakEl.style.animation = 'none';
            void streakEl.offsetWidth;
            streakEl.style.animation = 'lk-streak-bump 0.4s cubic-bezier(0.22,1,0.36,1)';
        }
        // Bonus XP for streaks
        if (streak >= 2) {
            const bonus = Math.min(streak, 5);
            showFloatingXp(bonus);
            earnedXp = Math.min(earnedXp + bonus, totalXp);
            if (xpEl) xpEl.textContent = earnedXp;
            saveState();
        }
    }

    function resetStreak() {
        streak = 0;
        if (streakEl) {
            streakEl.classList.remove('is-hot', 'is-fire', 'is-mega');
            streakEl.hidden = true;
        }
    }

    // Hook streak into quiz and practice
    root.addEventListener('ls:correct', () => bumpStreak());
    root.addEventListener('ls:wrong', () => resetStreak());

    // --- Achievement Badges ---
    const achievementsEl = root.querySelector('[data-ls-achievements]');
    const earnedAchievements = new Set();

    const ACHIEVEMENTS = [
        { id: 'first_step',   icon: '🚀', title: 'Prima miscare!',    desc: 'Ai completat primul pas',         check: () => completedSteps.size >= 1 },
        { id: 'halfway',      icon: '⭐', title: 'La jumatate!',      desc: 'Ai trecut de jumatatea lectiei',   check: () => completedSteps.size >= Math.ceil(steps.length / 2) },
        { id: 'quiz_ace',     icon: '🧠', title: 'Geniu la test!',    desc: 'Ai raspuns corect din prima',      check: () => !!root.querySelector('.ls-quiz-opt.is-correct.is-selected') },
        { id: 'streak_3',     icon: '🔥', title: 'Combo x3!',         desc: 'Trei raspunsuri corecte la rand',  check: () => streak >= 3 },
        { id: 'streak_5',     icon: '💥', title: 'Combo MEGA!',       desc: 'Cinci raspunsuri corecte la rand', check: () => streak >= 5 },
        { id: 'explorer',     icon: '🗺️', title: 'Explorator!',       desc: 'Ai vizitat toate pasii lectiei',  check: () => { const visited = new Set(); steps.forEach((s, i) => { if (s.classList.contains('is-active') || completedSteps.has(i)) visited.add(i); }); return visited.size >= steps.length; } },
        { id: 'completionist',icon: '🏆', title: 'Campion!',          desc: 'Ai terminat toata lectia',         check: () => completedSteps.size >= steps.length - 1 },
        { id: 'speed_start',  icon: '⚡', title: 'Start rapid!',      desc: 'Ai trecut intro-ul in 10 secunde', check: () => false },
    ];

    function checkAchievements() {
        ACHIEVEMENTS.forEach(a => {
            if (earnedAchievements.has(a.id)) return;
            try {
                if (a.check()) {
                    earnedAchievements.add(a.id);
                    showAchievement(a);
                }
            } catch (e) {}
        });
    }

    function showAchievement(a) {
        if (!achievementsEl) return;
        achievementsEl.hidden = false;

        // Toast notification
        const toast = document.createElement('div');
        toast.className = 'ls-achievement-toast';
        toast.innerHTML =
            '<span class="ls-achievement-toast__icon">' + a.icon + '</span>' +
            '<div class="ls-achievement-toast__body">' +
                '<div class="ls-achievement-toast__label">Realizare deblocata!</div>' +
                '<div class="ls-achievement-toast__title">' + a.title + '</div>' +
                '<div class="ls-achievement-toast__desc">' + a.desc + '</div>' +
            '</div>';
        document.body.appendChild(toast);
        toast.animate([
            { transform: 'translateX(120%)', opacity: 0 },
            { transform: 'translateX(0)', opacity: 1 },
        ], { duration: 500, easing: 'cubic-bezier(0.22,1,0.36,1)', fill: 'forwards' });
        setTimeout(() => {
            toast.animate([
                { transform: 'translateX(0)', opacity: 1 },
                { transform: 'translateX(120%)', opacity: 0 },
            ], { duration: 400, easing: 'ease-in', fill: 'forwards' }).onfinish = () => toast.remove();
        }, 3500);

        // Add badge to achievement wall
        const badge = document.createElement('div');
        badge.className = 'ls-achievement-badge';
        badge.innerHTML = '<span class="ls-achievement-badge__icon">' + a.icon + '</span>' +
                          '<span class="ls-achievement-badge__name">' + a.title + '</span>';
        badge.title = a.desc;
        achievementsEl.appendChild(badge);
        badge.style.animation = 'lk-pop 0.5s cubic-bezier(0.22,1,0.36,1)';

        emitConfetti(toast);
        LessonAudio.achievement();
    }

    // Check achievements periodically and on key events
    const _origCompleteStep = completeStep;
    // Wrap completeStep to also fire events
    const origStepHandler = root.querySelector('[data-ls-action="next"]');

    // Periodic achievement check
    setInterval(checkAchievements, 1500);

    // Speed start tracking
    const lessonStartTime = Date.now();
    const origGoToStep = goToStep;

    // --- Keyboard Navigation ---
    document.addEventListener('keydown', e => {
        // Only handle if lesson is focused (not inside textarea/input)
        const tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'textarea' || tag === 'input' || tag === 'select') return;

        if (e.key === 'ArrowRight' || e.key === 'd') {
            e.preventDefault();
            nextStep();
        } else if (e.key === 'ArrowLeft' || e.key === 'a') {
            e.preventDefault();
            prevStep();
        } else if (e.key === 'Enter' || e.key === ' ') {
            // Trigger the primary action button in current step
            const active = steps[currentStep];
            if (!active) return;
            const primaryBtn = active.querySelector('.ls-btn--primary:not(:disabled)');
            if (primaryBtn) { e.preventDefault(); primaryBtn.click(); }
        } else if (e.key === 'Escape') {
            // Close any open panels
            if (hintsDrawer && !hintsDrawer.hidden) {
                hintsDrawer.hidden = true;
                if (hintsToggle) hintsToggle.innerHTML = '&#128161; Ai nevoie de ajutor?';
            }
        } else if (e.key >= '1' && e.key <= '9') {
            const idx = parseInt(e.key, 10) - 1;
            if (idx < steps.length) goToStep(idx);
        }
    });

    // --- Mascot typing animation ---
    function typewriterEffect(el, speed) {
        const html = el.innerHTML;
        const text = el.textContent;
        if (!text || text.length < 10) return;
        el.textContent = '';
        el.style.visibility = 'visible';
        let i = 0;
        const interval = setInterval(() => {
            i++;
            el.textContent = text.slice(0, i);
            if (i >= text.length) {
                clearInterval(interval);
                el.innerHTML = html; // restore original HTML
            }
        }, speed || 18);
    }

    // Apply to first visible mentor bubble
    const firstBubble = root.querySelector('.lesson-step.is-active .ls-mentor__bubble');
    if (firstBubble) typewriterEffect(firstBubble, 20);

    // Re-apply on step change
    const _origGoToStep = goToStep;

    // --- Emit streak events from quiz/practice ---
    // Patch quiz submit to emit streak events
    if (quizForm) {
        const quizSubmit = quizForm.querySelector('[data-ls-quiz-submit]');
        if (quizSubmit) {
            quizSubmit.addEventListener('click', () => {
                setTimeout(() => {
                    if (root.querySelector('.ls-quiz-opt.is-correct.is-selected')) {
                        root.dispatchEvent(new Event('ls:correct'));
                        // Speed start achievement
                        if (Date.now() - lessonStartTime < 10000) {
                            ACHIEVEMENTS.find(a => a.id === 'speed_start').check = () => true;
                        }
                    } else if (root.querySelector('.ls-quiz-opt.is-wrong')) {
                        root.dispatchEvent(new Event('ls:wrong'));
                    }
                }, 150);
            });
        }
    }

    // Patch practice verify to emit streak events
    if (practiceEl) {
        const vBtn = practiceEl.querySelector('[data-ls-verify]');
        if (vBtn) {
            vBtn.addEventListener('click', () => {
                setTimeout(() => {
                    const wrong = practiceEl.querySelector('.ls-match-slot.is-wrong');
                    root.dispatchEvent(new Event(wrong ? 'ls:wrong' : 'ls:correct'));
                }, 150);
            });
        }
    }

    // --- Inject reverse slide animation ---
    if (!document.querySelector('#lk-extra-keyframes')) {
        const style = document.createElement('style');
        style.id = 'lk-extra-keyframes';
        style.textContent =
            '@keyframes lk-slideBack{from{opacity:0;transform:translateX(-40px)}to{opacity:1;transform:translateX(0)}}' +
            '@keyframes lk-streak-bump{0%{transform:scale(1)}40%{transform:scale(1.3)}100%{transform:scale(1)}}';
        document.head.appendChild(style);
    }

    // --- Init ---
    loadState();
    if (xpEl) xpEl.textContent = earnedXp;
    goToStep(currentStep);

    // Apply typewriter to initial step's mentor bubble after render
    requestAnimationFrame(() => {
        const bubble = root.querySelector('.lesson-step.is-active .ls-mentor__bubble');
        if (bubble) typewriterEffect(bubble, 20);
    });
})();
