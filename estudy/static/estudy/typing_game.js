/* typing_game.js — Fun typing adventure for kids 8-10 */
'use strict';
(() => {
    const root = document.querySelector('[data-typing-game]');
    if (!root) return;

    // === DOM refs ===
    const screens = {
        start:   root.querySelector('[data-tg-screen="start"]'),
        play:    root.querySelector('[data-tg-screen="play"]'),
        arcade:  root.querySelector('[data-tg-screen="arcade"]'),
        results: root.querySelector('[data-tg-screen="results"]'),
    };
    const hudEls = {
        levelName: root.querySelector('[data-tg-level-name]'),
        wpm:       root.querySelector('[data-tg-wpm]'),
        accuracy:  root.querySelector('[data-tg-accuracy]'),
        score:     root.querySelector('[data-tg-score]'),
        combo:     root.querySelector('[data-tg-combo]'),
        comboVal:  root.querySelector('[data-tg-combo-val]'),
        lives:     root.querySelectorAll('.tg-life'),
    };
    const playEls = {
        promptText: root.querySelector('[data-tg-prompt-text]'),
        typed:      root.querySelector('[data-tg-typed]'),
        cursor:     root.querySelector('[data-tg-cursor]'),
        roundFill:  root.querySelector('[data-tg-round-fill]'),
        roundLabel: root.querySelector('[data-tg-round-label]'),
        fingerGuide: root.querySelector('[data-tg-finger]'),
        fingerText: root.querySelector('[data-tg-finger-text]'),
        fingerKey:  root.querySelector('[data-tg-finger-key]'),
        fingerParts: root.querySelectorAll('[data-tg-finger-part]'),
        hands:      root.querySelectorAll('[data-tg-hand]'),
        keyboard:   root.querySelector('[data-tg-keyboard]'),
    };
    const resultEls = {
        badge:  root.querySelector('[data-tg-result-badge]'),
        title:  root.querySelector('[data-tg-result-title]'),
        sub:    root.querySelector('[data-tg-result-sub]'),
        wpm:    root.querySelector('[data-tg-result-wpm]'),
        acc:    root.querySelector('[data-tg-result-acc]'),
        score:  root.querySelector('[data-tg-result-score]'),
        combo:  root.querySelector('[data-tg-result-combo]'),
        stars:  root.querySelectorAll('.tg-star'),
    };

    // === Level definitions ===
    const LEVELS = [
        {
            name: 'Primele litere',
            chars: 'asdfghjkl',
            mode: 'letters',
            count: 20,
        },
        {
            name: 'Randul de sus',
            chars: 'qwertyuiop',
            mode: 'letters',
            count: 20,
        },
        {
            name: 'Toate literele',
            chars: 'abcdefghijklmnopqrstuvwxyz',
            mode: 'letters',
            count: 25,
        },
        {
            name: 'Cuvinte',
            mode: 'words',
            count: 15,
            words: [
                'casa', 'mama', 'tata', 'soare', 'luna', 'carte', 'masa',
                'floare', 'copil', 'scoala', 'prieten', 'joc', 'lapte',
                'pisica', 'caine', 'mere', 'para', 'apa', 'foc', 'lemn',
                'drum', 'cer', 'nor', 'ploaie', 'zapada', 'vant', 'cal',
                'urs', 'leu', 'pom', 'lac', 'munte', 'mare', 'riu',
                'peste', 'paine', 'ciocolata', 'carte', 'muzica', 'dans',
                'culoare', 'rosu', 'verde', 'albastru', 'galben',
            ],
        },
        {
            name: 'Propozitii',
            mode: 'sentences',
            count: 8,
            sentences: [
                'pisica doarme pe canapea',
                'soarele straluceste pe cer',
                'mama face o prajitura buna',
                'copiii se joaca in parc',
                'cartea este pe masa',
                'apa curge prin rau',
                'floarea creste in gradina',
                'cainele alearga prin iarba',
                'luna si stelele sunt sus',
                'eu iubesc ciocolata cu lapte',
                'scoala este casa mea a doua',
                'prietenul meu e foarte amuzant',
                'imi place sa citesc povesti',
                'norul arata ca un iepure',
                'pasarea canta frumos dimineata',
            ],
        },
        {
            name: 'Ploaie de litere',
            mode: 'arcade',
            chars: 'abcdefghijklmnopqrstuvwxyz',
        },
    ];

    // === Finger map for hints ===
    const FINGER_MAP = {
        q: { targets: ['left-pinky'], label: 'Deget mic stang' },
        w: { targets: ['left-ring'], label: 'Inelar stang' },
        e: { targets: ['left-middle'], label: 'Mijlociu stang' },
        r: { targets: ['left-index'], label: 'Aratator stang' },
        t: { targets: ['left-index'], label: 'Aratator stang' },
        y: { targets: ['right-index'], label: 'Aratator drept' },
        u: { targets: ['right-index'], label: 'Aratator drept' },
        i: { targets: ['right-middle'], label: 'Mijlociu drept' },
        o: { targets: ['right-ring'], label: 'Inelar drept' },
        p: { targets: ['right-pinky'], label: 'Deget mic drept' },
        a: { targets: ['left-pinky'], label: 'Deget mic stang' },
        s: { targets: ['left-ring'], label: 'Inelar stang' },
        d: { targets: ['left-middle'], label: 'Mijlociu stang' },
        f: { targets: ['left-index'], label: 'Aratator stang' },
        g: { targets: ['left-index'], label: 'Aratator stang' },
        h: { targets: ['right-index'], label: 'Aratator drept' },
        j: { targets: ['right-index'], label: 'Aratator drept' },
        k: { targets: ['right-middle'], label: 'Mijlociu drept' },
        l: { targets: ['right-ring'], label: 'Inelar drept' },
        z: { targets: ['left-pinky'], label: 'Deget mic stang' },
        x: { targets: ['left-ring'], label: 'Inelar stang' },
        c: { targets: ['left-middle'], label: 'Mijlociu stang' },
        v: { targets: ['left-index'], label: 'Aratator stang' },
        b: { targets: ['left-index'], label: 'Aratator stang' },
        n: { targets: ['right-index'], label: 'Aratator drept' },
        m: { targets: ['right-index'], label: 'Aratator drept' },
        ' ': { targets: ['left-thumb', 'right-thumb'], label: 'Deget mare pentru spatiu' },
    };

    // === Game state ===
    let currentLevel = 0;
    let prompts = [];
    let promptIdx = 0;
    let charIdx = 0;
    let score = 0;
    let combo = 0;
    let maxCombo = 0;
    let lives = 5;
    let totalChars = 0;
    let correctChars = 0;
    let startTime = 0;
    let gameActive = false;

    // === Audio (Web Audio API for click/error sounds) ===
    let audioCtx = null;
    function getAudioCtx() {
        if (!audioCtx) {
            try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {}
        }
        return audioCtx;
    }

    function playTone(freq, duration, type) {
        const ctx = getAudioCtx();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type || 'sine';
        osc.frequency.value = freq;
        gain.gain.value = 0.08;
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + duration);
    }

    function playCorrect() { playTone(880, 0.08, 'sine'); }
    function playWrong() { playTone(220, 0.15, 'square'); }
    function playCombo() {
        playTone(660, 0.06, 'sine');
        setTimeout(() => playTone(880, 0.06, 'sine'), 60);
        setTimeout(() => playTone(1100, 0.08, 'sine'), 120);
    }
    function playLevelUp() {
        [523, 659, 784, 1047].forEach((f, i) => {
            setTimeout(() => playTone(f, 0.12, 'sine'), i * 100);
        });
    }

    // === Screen management ===
    function showScreen(name) {
        Object.values(screens).forEach(s => { if (s) s.classList.remove('is-active'); });
        if (screens[name]) screens[name].classList.add('is-active');
    }

    // === Generate prompts for a level ===
    function generatePrompts(level) {
        const lv = LEVELS[level];
        if (lv.mode === 'letters') {
            const arr = [];
            for (let i = 0; i < lv.count; i++) {
                arr.push(lv.chars[Math.floor(Math.random() * lv.chars.length)]);
            }
            return arr;
        } else if (lv.mode === 'words') {
            const arr = [];
            const pool = [...lv.words];
            for (let i = 0; i < lv.count; i++) {
                arr.push(pool[Math.floor(Math.random() * pool.length)]);
            }
            return arr;
        } else if (lv.mode === 'sentences') {
            const arr = [];
            const pool = [...lv.sentences];
            for (let i = 0; i < lv.count; i++) {
                arr.push(pool[Math.floor(Math.random() * pool.length)]);
            }
            return arr;
        }
        return [];
    }

    // === Start a level ===
    function startLevel(level) {
        currentLevel = level;
        const lv = LEVELS[level];

        if (lv.mode === 'arcade') {
            startArcade(lv);
            return;
        }

        prompts = generatePrompts(level);
        promptIdx = 0;
        charIdx = 0;
        score = 0;
        combo = 0;
        maxCombo = 0;
        lives = 5;
        totalChars = 0;
        correctChars = 0;
        startTime = Date.now();
        gameActive = true;

        hudEls.levelName.textContent = 'Nivel ' + (level + 1) + ': ' + lv.name;
        updateHud();
        resetLives();
        showScreen('play');
        renderPrompt();
    }

    // === Render current prompt ===
    function renderPrompt() {
        if (promptIdx >= prompts.length) {
            endGame();
            return;
        }
        const text = prompts[promptIdx];
        let html = '';
        for (let i = 0; i < text.length; i++) {
            const ch = text[i] === ' ' ? '&nbsp;' : escHtml(text[i]);
            if (i < charIdx) {
                html += '<span class="tg-char tg-char--done">' + ch + '</span>';
            } else if (i === charIdx) {
                html += '<span class="tg-char tg-char--current">' + ch + '</span>';
            } else {
                html += '<span class="tg-char">' + ch + '</span>';
            }
        }
        playEls.promptText.innerHTML = html;
        playEls.typed.textContent = '';

        // Update round progress
        const total = prompts.length;
        playEls.roundFill.style.width = ((promptIdx / total) * 100) + '%';
        playEls.roundLabel.textContent = promptIdx + ' / ' + total;

        // Highlight key on keyboard
        highlightKey(text[charIdx] || '');

        // Finger guide
        updateFingerGuide(text[charIdx] || '');
    }

    function updateFingerGuide(ch) {
        const key = (ch || '').toLowerCase();
        const finger = FINGER_MAP[key];

        playEls.fingerParts.forEach(part => part.classList.remove('is-active'));
        playEls.hands.forEach(hand => hand.classList.remove('is-active'));

        if (!finger) {
            if (playEls.fingerKey) playEls.fingerKey.textContent = '';
            if (playEls.fingerText) playEls.fingerText.textContent = '';
            return;
        }

        (finger.targets || []).forEach(target => {
            const part = root.querySelector('[data-tg-finger-part="' + target + '"]');
            if (part) part.classList.add('is-active');

            const handName = target.split('-')[0];
            const hand = root.querySelector('[data-tg-hand="' + handName + '"]');
            if (hand) hand.classList.add('is-active');
        });

        if (playEls.fingerKey) playEls.fingerKey.textContent = key === ' ' ? 'SPATIU' : key.toUpperCase();
        if (playEls.fingerText) playEls.fingerText.textContent = finger.label;
    }

    function highlightKey(ch) {
        if (!playEls.keyboard) return;
        playEls.keyboard.querySelectorAll('.tg-key').forEach(k => {
            k.classList.remove('is-target', 'is-correct', 'is-wrong');
        });
        if (!ch) return;
        const keyEl = playEls.keyboard.querySelector('[data-key="' + ch.toLowerCase() + '"]');
        if (keyEl) keyEl.classList.add('is-target');
    }

    function flashKey(ch, correct) {
        if (!playEls.keyboard) return;
        const keyEl = playEls.keyboard.querySelector('[data-key="' + ch.toLowerCase() + '"]');
        if (!keyEl) return;
        keyEl.classList.add(correct ? 'is-correct' : 'is-wrong');
        setTimeout(() => keyEl.classList.remove('is-correct', 'is-wrong'), 300);
    }

    // === Handle keypress ===
    function handleKey(e) {
        if (!gameActive) return;
        if (e.ctrlKey || e.altKey || e.metaKey) return;
        if (e.key === 'Escape') { endGame(); return; }
        if (e.key.length !== 1) return;

        e.preventDefault();
        const text = prompts[promptIdx];
        if (!text) return;

        const expected = text[charIdx];
        const typed = e.key;
        totalChars++;

        if (typed.toLowerCase() === expected.toLowerCase()) {
            // Correct
            correctChars++;
            combo++;
            if (combo > maxCombo) maxCombo = combo;
            charIdx++;

            playCorrect();
            if (combo > 0 && combo % 5 === 0) playCombo();
            flashKey(expected, true);

            // Score: base 10 + combo bonus
            const comboBonus = Math.min(combo, 10);
            score += 10 + comboBonus;

            // Floating +points
            showFloatingPoints(10 + comboBonus, e);

            // Check if prompt done
            if (charIdx >= text.length) {
                promptIdx++;
                charIdx = 0;
                // Bonus for completing a prompt
                score += 25;
                showFloatingPoints(25, e, true);
            }

            renderPrompt();
        } else {
            // Wrong
            combo = 0;
            lives--;
            playWrong();
            flashKey(expected, false);
            shakeScreen();

            if (lives <= 0) {
                gameActive = false;
                endGame();
                return;
            }
        }

        updateHud();
    }

    // === HUD updates ===
    function updateHud() {
        // WPM
        const elapsed = (Date.now() - startTime) / 60000; // minutes
        const wpm = elapsed > 0 ? Math.round(correctChars / 5 / elapsed) : 0;
        hudEls.wpm.textContent = wpm;

        // Accuracy
        const acc = totalChars > 0 ? Math.round((correctChars / totalChars) * 100) : 100;
        hudEls.accuracy.textContent = acc;

        // Score
        hudEls.score.textContent = score;

        // Combo
        if (combo >= 2) {
            hudEls.combo.hidden = false;
            hudEls.comboVal.textContent = combo;
            hudEls.combo.classList.toggle('is-fire', combo >= 5);
            hudEls.combo.classList.toggle('is-mega', combo >= 10);
        } else {
            hudEls.combo.hidden = true;
        }

        // Lives
        hudEls.lives.forEach((el, i) => {
            if (i < lives) {
                el.classList.add('is-alive');
                el.classList.remove('is-lost');
                el.innerHTML = '&#10084;&#65039;';
            } else {
                el.classList.remove('is-alive');
                el.classList.add('is-lost');
                el.innerHTML = '&#128420;';
            }
        });
    }

    function resetLives() {
        lives = 5;
        updateHud();
    }

    // === End game / show results ===
    function endGame() {
        gameActive = false;
        const elapsed = (Date.now() - startTime) / 60000;
        const wpm = elapsed > 0 ? Math.round(correctChars / 5 / elapsed) : 0;
        const acc = totalChars > 0 ? Math.round((correctChars / totalChars) * 100) : 100;

        // Determine stars
        let stars = 0;
        if (acc >= 60) stars = 1;
        if (acc >= 80) stars = 2;
        if (acc >= 95 && wpm >= 10) stars = 3;

        // Badge & title
        const titles = ['Continua sa exersezi!', 'Bine lucrat!', 'Foarte bine!', 'PERFECT! Esti un campion!'];
        const badges = ['&#128170;', '&#11088;', '&#127942;', '&#127775;'];

        resultEls.badge.innerHTML = badges[stars];
        resultEls.title.textContent = titles[stars];
        resultEls.sub.textContent = lives > 0 ? 'Ai terminat nivelul!' : 'Ai ramas fara vieti, dar ai luptat bine!';
        resultEls.wpm.textContent = wpm;
        resultEls.acc.textContent = acc + '%';
        resultEls.score.textContent = score;
        resultEls.combo.textContent = maxCombo;

        // Stars animation
        resultEls.stars.forEach((el, i) => {
            el.classList.toggle('is-earned', i < stars);
            el.style.animationDelay = (i * 0.2) + 's';
        });

        showScreen('results');
        playLevelUp();

        // Confetti for 2+ stars
        if (stars >= 2) emitConfetti();
        if (stars >= 3) emitEmojiRain();

        // Save best score
        try {
            const key = 'tg-best-' + currentLevel;
            const prev = parseInt(localStorage.getItem(key) || '0', 10);
            if (score > prev) localStorage.setItem(key, String(score));
        } catch (e) {}
    }

    // === Arcade mode (falling letters) ===
    let arcadeRaf = null;
    let arcadeLetters = [];
    let arcadeScore = 0;
    let arcadeLives = 5;
    let arcadeActive = false;
    const arcadeCanvas = root.querySelector('[data-tg-arcade-canvas]');
    const arcadeScoreEl = root.querySelector('[data-tg-arcade-score]');

    function startArcade(lv) {
        showScreen('arcade');
        if (!arcadeCanvas) return;
        const ctx = arcadeCanvas.getContext('2d');
        arcadeCanvas.width = arcadeCanvas.parentElement.clientWidth || 800;
        arcadeCanvas.height = arcadeCanvas.parentElement.clientHeight || 500;

        arcadeLetters = [];
        arcadeScore = 0;
        arcadeLives = 5;
        arcadeActive = true;
        score = 0;
        combo = 0;
        maxCombo = 0;
        totalChars = 0;
        correctChars = 0;
        startTime = Date.now();
        lives = 5;

        hudEls.levelName.textContent = 'Ploaie de litere!';
        updateHud();

        let spawnTimer = 0;
        let spawnInterval = 60; // frames
        let speed = 1.2;
        let elapsed = 0;

        function spawnLetter() {
            const ch = lv.chars[Math.floor(Math.random() * lv.chars.length)];
            arcadeLetters.push({
                ch: ch,
                x: 40 + Math.random() * (arcadeCanvas.width - 80),
                y: -30,
                speed: speed + Math.random() * 0.5,
                size: 32 + Math.random() * 12,
                color: ['#7C3AED', '#EC4899', '#3B82F6', '#10B981', '#F59E0B'][Math.floor(Math.random() * 5)],
                alive: true,
            });
        }

        function tick() {
            if (!arcadeActive) return;
            ctx.clearRect(0, 0, arcadeCanvas.width, arcadeCanvas.height);
            elapsed++;

            // Increase difficulty
            if (elapsed % 300 === 0 && spawnInterval > 20) spawnInterval -= 5;
            if (elapsed % 600 === 0) speed += 0.2;

            // Spawn
            spawnTimer++;
            if (spawnTimer >= spawnInterval) {
                spawnLetter();
                spawnTimer = 0;
            }

            // Draw & move letters
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            for (let i = arcadeLetters.length - 1; i >= 0; i--) {
                const lt = arcadeLetters[i];
                if (!lt.alive) {
                    arcadeLetters.splice(i, 1);
                    continue;
                }
                lt.y += lt.speed;

                // Draw bubble
                ctx.beginPath();
                ctx.arc(lt.x, lt.y, lt.size * 0.7, 0, Math.PI * 2);
                ctx.fillStyle = lt.color + '22';
                ctx.fill();
                ctx.strokeStyle = lt.color;
                ctx.lineWidth = 3;
                ctx.stroke();

                // Draw letter
                ctx.font = 'bold ' + lt.size + 'px Nunito, sans-serif';
                ctx.fillStyle = lt.color;
                ctx.fillText(lt.ch.toUpperCase(), lt.x, lt.y);

                // Fallen off screen
                if (lt.y > arcadeCanvas.height + 30) {
                    lt.alive = false;
                    arcadeLives--;
                    lives = arcadeLives;
                    combo = 0;
                    playWrong();
                    updateHud();
                    if (arcadeLives <= 0) {
                        arcadeActive = false;
                        endGame();
                        return;
                    }
                }
            }

            // Score display on canvas
            if (arcadeScoreEl) arcadeScoreEl.textContent = score;

            arcadeRaf = requestAnimationFrame(tick);
        }

        arcadeRaf = requestAnimationFrame(tick);
    }

    function handleArcadeKey(e) {
        if (!arcadeActive) return;
        if (e.key.length !== 1) return;
        e.preventDefault();

        const typed = e.key.toLowerCase();
        totalChars++;

        // Find lowest matching letter
        let target = null;
        let targetIdx = -1;
        for (let i = 0; i < arcadeLetters.length; i++) {
            const lt = arcadeLetters[i];
            if (lt.alive && lt.ch === typed) {
                if (!target || lt.y > target.y) {
                    target = lt;
                    targetIdx = i;
                }
            }
        }

        if (target) {
            target.alive = false;
            correctChars++;
            combo++;
            if (combo > maxCombo) maxCombo = combo;
            score += 15 + Math.min(combo, 10);
            playCorrect();
            if (combo > 0 && combo % 5 === 0) playCombo();

            // Explosion effect on canvas
            explodeAt(target.x, target.y, target.color);

            updateHud();
        } else {
            combo = 0;
            playWrong();
            updateHud();
        }
    }

    function explodeAt(x, y, color) {
        if (!arcadeCanvas) return;
        const ctx = arcadeCanvas.getContext('2d');
        let frame = 0;
        function draw() {
            frame++;
            const r = frame * 4;
            const alpha = 1 - frame / 12;
            if (alpha <= 0) return;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.strokeStyle = color + Math.round(alpha * 255).toString(16).padStart(2, '0');
            ctx.lineWidth = 3;
            ctx.stroke();
            // Particles
            for (let i = 0; i < 6; i++) {
                const angle = (Math.PI * 2 / 6) * i;
                const px = x + Math.cos(angle) * r;
                const py = y + Math.sin(angle) * r;
                ctx.beginPath();
                ctx.arc(px, py, 3, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.globalAlpha = alpha;
                ctx.fill();
                ctx.globalAlpha = 1;
            }
            requestAnimationFrame(draw);
        }
        requestAnimationFrame(draw);
    }

    // === Visual effects ===
    function showFloatingPoints(pts, e, isBonus) {
        const el = document.createElement('div');
        el.textContent = '+' + pts;
        el.className = 'tg-float-pts' + (isBonus ? ' tg-float-pts--bonus' : '');
        el.style.left = (e && e.clientX ? e.clientX : window.innerWidth / 2) + 'px';
        el.style.top = (e && e.clientY ? e.clientY - 20 : 200) + 'px';
        document.body.appendChild(el);
        el.animate([
            { transform: 'translateY(0) scale(1)', opacity: 1 },
            { transform: 'translateY(-70px) scale(1.4)', opacity: 0 },
        ], { duration: 800, easing: 'cubic-bezier(0.22,1,0.36,1)' }).onfinish = () => el.remove();
    }

    function shakeScreen() {
        root.classList.add('tg--shake');
        setTimeout(() => root.classList.remove('tg--shake'), 400);
    }

    function emitConfetti() {
        const cx = window.innerWidth / 2;
        const cy = window.innerHeight / 2;
        const colors = ['#7C3AED', '#EC4899', '#10B981', '#F59E0B', '#3B82F6', '#EF4444'];
        for (let i = 0; i < 40; i++) {
            const el = document.createElement('div');
            const size = 6 + Math.random() * 8;
            const color = colors[i % colors.length];
            el.style.cssText =
                'position:fixed;pointer-events:none;z-index:9999;border-radius:' + (Math.random() > 0.5 ? '50%' : '2px') + ';' +
                'width:' + size + 'px;height:' + size + 'px;background:' + color + ';' +
                'left:' + cx + 'px;top:' + cy + 'px;';
            document.body.appendChild(el);
            const angle = (Math.PI * 2 / 40) * i + (Math.random() - 0.5) * 0.5;
            const vel = 120 + Math.random() * 180;
            const dx = Math.cos(angle) * vel;
            const dy = Math.sin(angle) * vel - 100;
            el.animate([
                { transform: 'translate(0,0) rotate(0deg) scale(1)', opacity: 1 },
                { transform: 'translate(' + dx + 'px,' + dy + 'px) rotate(' + (Math.random() * 720) + 'deg) scale(0)', opacity: 0 },
            ], { duration: 900 + Math.random() * 500, easing: 'cubic-bezier(0.22,1,0.36,1)' })
            .onfinish = () => el.remove();
        }
    }

    function emitEmojiRain() {
        const emojis = ['🎉', '🌟', '🏆', '💎', '⭐', '✨', '🚀', '🎯', '💪', '🥇'];
        for (let i = 0; i < 15; i++) {
            const el = document.createElement('div');
            el.textContent = emojis[i % emojis.length];
            el.style.cssText =
                'position:fixed;top:-40px;z-index:9998;pointer-events:none;font-size:32px;' +
                'left:' + (Math.random() * 100) + 'vw;';
            document.body.appendChild(el);
            el.animate([
                { transform: 'translateY(0) rotate(0deg)', opacity: 1 },
                { transform: 'translateY(110vh) rotate(' + (360 + Math.random() * 360) + 'deg)', opacity: 0.3 },
            ], { duration: 2500 + Math.random() * 1500, delay: Math.random() * 600, easing: 'ease-in' })
            .onfinish = () => el.remove();
        }
    }

    // === Utility ===
    function escHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // === Event listeners ===

    // Level select
    root.querySelectorAll('[data-tg-start-level]').forEach(btn => {
        btn.addEventListener('click', () => {
            const lvl = parseInt(btn.dataset.tgStartLevel, 10);
            startLevel(lvl);
        });
    });

    // Keyboard input
    document.addEventListener('keydown', e => {
        if (screens.play && screens.play.classList.contains('is-active')) {
            handleKey(e);
        } else if (screens.arcade && screens.arcade.classList.contains('is-active')) {
            handleArcadeKey(e);
        }
    });

    // Retry / menu buttons
    const retryBtn = root.querySelector('[data-tg-retry]');
    const menuBtn = root.querySelector('[data-tg-menu]');
    if (retryBtn) retryBtn.addEventListener('click', () => startLevel(currentLevel));
    if (menuBtn) menuBtn.addEventListener('click', () => {
        if (arcadeRaf) cancelAnimationFrame(arcadeRaf);
        arcadeActive = false;
        showScreen('start');
    });

    // Resize arcade canvas
    window.addEventListener('resize', () => {
        if (arcadeCanvas && screens.arcade.classList.contains('is-active')) {
            arcadeCanvas.width = arcadeCanvas.parentElement.clientWidth || 800;
            arcadeCanvas.height = arcadeCanvas.parentElement.clientHeight || 500;
        }
    });

    // Cursor blink
    if (playEls.cursor) {
        setInterval(() => {
            playEls.cursor.style.opacity = playEls.cursor.style.opacity === '0' ? '1' : '0';
        }, 530);
    }

    // Init: show start screen
    showScreen('start');
})();
