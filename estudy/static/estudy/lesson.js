(() => {
    const lessonRoot = document.querySelector('.lesson-root');
    if (!lessonRoot) {
        return;
    }

    const lessonSlug = lessonRoot.dataset.lessonSlug || 'lesson';
    const PROGRESS_STEPS = ['concept', 'example', 'practice', 'test', 'summary'];
    const sectionToStage = {
        'adventure-mode': 'concept',
        concept: 'concept',
        'code-exercises': 'example',
        example: 'example',
        practice: 'practice',
        test: 'test',
        summary: 'summary'
    };

    const safeStorage = {
        get(key) {
            try {
                return window.localStorage.getItem(key);
            } catch (error) {
                console.warn('LocalStorage get failed', error);
                return null;
            }
        },
        set(key, value) {
            try {
                window.localStorage.setItem(key, value);
            } catch (error) {
                console.warn('LocalStorage set failed', error);
            }
    }
};

const getCsrfToken = () => {
    const token = document.cookie
        .split(';')
        .map((row) => row.trim())
        .find((row) => row.startsWith('csrftoken='));
    return token ? decodeURIComponent(token.split('=')[1]) : '';
};

const loadState = (key, fallback = null) => {
    const raw = safeStorage.get(key);
    if (!raw) {
            return fallback;
        }
        try {
            return JSON.parse(raw);
        } catch (error) {
            console.warn('Failed to parse stored state', error);
            return fallback;
        }
    };

    if (window.Prism?.highlightAll) {
        window.Prism.highlightAll();
    }

    const initTabs = () => {
        document.querySelectorAll('[data-tab-group]').forEach((group) => {
            const triggers = group.querySelectorAll('[data-tab-trigger]');
            const panels = group.querySelectorAll('[data-tab-panel]');
            triggers.forEach((trigger) => {
                trigger.addEventListener('click', () => {
                    const targetId = trigger.dataset.tabTrigger;
                    if (!targetId) {
                        return;
                    }
                    triggers.forEach((btn) => {
                        const isActive = btn === trigger;
                        btn.classList.toggle('is-active', isActive);
                        btn.setAttribute('aria-selected', String(isActive));
                    });
                    panels.forEach((panel) => {
                        const matches = panel.dataset.tabPanel === targetId;
                        panel.classList.toggle('is-active', matches);
                        panel.toggleAttribute('hidden', !matches);
                    });
                });
            });
        });
    };

    initTabs();

    const initAdventureMode = () => {
        const adventureRoot = document.querySelector('#adventure-mode');
        if (!adventureRoot) {
            return;
        }

        const characterCards = Array.from(adventureRoot.querySelectorAll('[data-character-card]'));
        if (characterCards.length > 1) {
            let activeIndex = characterCards.findIndex((card) => card.classList.contains('is-active'));
            if (activeIndex < 0) {
                activeIndex = 0;
                characterCards[0].classList.add('is-active');
            }

            const activateCard = (index) => {
                activeIndex = index;
                characterCards.forEach((card, cardIndex) => {
                    card.classList.toggle('is-active', cardIndex === activeIndex);
                });
            };

            characterCards.forEach((card, index) => {
                card.addEventListener('click', () => activateCard(index));
            });

            let castIntervalId = null;
            const startRotation = () => {
                if (castIntervalId) {
                    return;
                }
                castIntervalId = window.setInterval(() => {
                    const next = (activeIndex + 1) % characterCards.length;
                    activateCard(next);
                }, 3800);
            };
            const stopRotation = () => {
                if (!castIntervalId) {
                    return;
                }
                window.clearInterval(castIntervalId);
                castIntervalId = null;
            };

            adventureRoot.addEventListener('pointerenter', stopRotation);
            adventureRoot.addEventListener('pointerleave', startRotation);
            startRotation();
        }

        const missions = Array.from(adventureRoot.querySelectorAll('[data-arena-mission]'));
        if (!missions.length) {
            return;
        }

        const statusTitle = adventureRoot.querySelector('[data-arena-status-title]');
        const statusGoal = adventureRoot.querySelector('[data-arena-status-goal]');
        const statusXp = adventureRoot.querySelector('[data-arena-status-xp]');
        const statusLink = adventureRoot.querySelector('[data-arena-status-link]');

        const activateMission = (button) => {
            missions.forEach((missionButton) => {
                missionButton.classList.toggle('is-active', missionButton === button);
            });
            const missionTitle = button.dataset.missionTitle || button.textContent.trim();
            const missionGoal = button.dataset.missionGoal || 'Misiune activă.';
            const missionXp = button.dataset.missionXp || '10';
            const missionTarget = button.dataset.missionTarget || '#example';

            if (statusTitle) {
                statusTitle.textContent = missionTitle;
            }
            if (statusGoal) {
                statusGoal.textContent = missionGoal;
            }
            if (statusXp) {
                statusXp.textContent = `+${missionXp} XP`;
            }
            if (statusLink) {
                statusLink.setAttribute('href', missionTarget);
            }
        };

        missions.forEach((button) => {
            button.addEventListener('click', () => activateMission(button));
        });

        activateMission(missions[0]);
    };

    initAdventureMode();

    const sections = Array.from(document.querySelectorAll('[data-lesson-section]'));
    const tocLinks = Array.from(document.querySelectorAll('[data-lesson-toc-link]'));
    const mobileSelect = document.querySelector('#lesson-mobile-toc');
    const stageButtons = new Map(
        Array.from(document.querySelectorAll('[data-progress-stage]')).map((btn) => [btn.dataset.progressStage, btn])
    );
    let activeSectionId = null;
    let activeStage = 'concept';
    const immersiveMode = document.body.classList.contains('lesson-page--immersive');
    const coreImmersivePanels = new Set(['concept', 'example', 'practice', 'test', 'summary']);
    const immersiveSections = immersiveMode
        ? Array.from(document.querySelectorAll('.lesson-body > .lesson-section[id]'))
        : [];
    let activateImmersivePanel = null;
    let initialImmersivePanel = 'concept';

    const setActiveSection = (id) => {
        if (!id || activeSectionId === id) {
            return;
        }
        activeSectionId = id;
        tocLinks.forEach((link) => {
            const matches = link.getAttribute('href') === `#${id}`;
            link.classList.toggle('is-active', matches);
        });
        if (mobileSelect && mobileSelect.value !== `#${id}`) {
            mobileSelect.value = `#${id}`;
        }
        const mapped = sectionToStage[id];
        if (mapped) {
            activeStage = mapped;
            updateProgressUI();
        }
    };

    const updateActiveSectionFromScroll = () => {
        if (!sections.length) {
            return;
        }
        const threshold = window.innerHeight * 0.35;
        let candidate = sections[0].id;
        sections.forEach((section) => {
            const top = section.getBoundingClientRect().top;
            if (top <= threshold) {
                candidate = section.id;
            }
        });
        setActiveSection(candidate);
    };

    let sectionUpdateScheduled = false;
    const scheduleSectionUpdate = () => {
        if (sectionUpdateScheduled) {
            return;
        }
        sectionUpdateScheduled = true;
        window.requestAnimationFrame(() => {
            updateActiveSectionFromScroll();
            sectionUpdateScheduled = false;
        });
    };

    if (immersiveMode && immersiveSections.length) {
        const applyPanelVisibility = (targetId) => {
            immersiveSections.forEach((section) => {
                if (!coreImmersivePanels.has(section.id)) {
                    section.classList.remove('is-panel-active');
                    section.setAttribute('hidden', '');
                    return;
                }
                const isActive = section.id === targetId;
                section.classList.toggle('is-panel-active', isActive);
                section.toggleAttribute('hidden', !isActive);
            });
        };

        activateImmersivePanel = (targetId, { updateHash = true } = {}) => {
            if (!targetId || !coreImmersivePanels.has(targetId)) {
                return;
            }
            applyPanelVisibility(targetId);
            setActiveSection(targetId);
            if (updateHash) {
                window.history.replaceState(null, '', `#${targetId}`);
            }
        };

        const requestedHash = window.location.hash?.slice(1);
        if (requestedHash && coreImmersivePanels.has(requestedHash)) {
            initialImmersivePanel = requestedHash;
        } else if (coreImmersivePanels.has('example')) {
            initialImmersivePanel = 'example';
        }

        document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
            anchor.addEventListener('click', (event) => {
                const href = anchor.getAttribute('href');
                if (!href || href === '#' || href === '#0') {
                    return;
                }
                const targetId = href.slice(1);
                if (!coreImmersivePanels.has(targetId)) {
                    return;
                }
                event.preventDefault();
                activateImmersivePanel?.(targetId);
            });
        });

        tocLinks.forEach((link) => {
            link.addEventListener('click', (event) => {
                const href = link.getAttribute('href');
                if (!href || !href.startsWith('#')) {
                    return;
                }
                const targetId = href.slice(1);
                if (!coreImmersivePanels.has(targetId)) {
                    return;
                }
                event.preventDefault();
                activateImmersivePanel?.(targetId);
            });
        });

        mobileSelect?.addEventListener('change', (event) => {
            const targetId = String(event.target.value || '').replace('#', '');
            if (!coreImmersivePanels.has(targetId)) {
                return;
            }
            activateImmersivePanel?.(targetId);
        });
    } else {
        document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
            anchor.addEventListener('click', (event) => {
                const targetId = anchor.getAttribute('href');
                if (!targetId || targetId === '#' || targetId === '#0') {
                    return;
                }
                const target = document.querySelector(targetId);
                if (!target) {
                    return;
                }
                event.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });

        tocLinks.forEach((link) => {
            link.addEventListener('click', (event) => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    event.preventDefault();
                    const target = document.querySelector(href);
                    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });

        mobileSelect?.addEventListener('change', (event) => {
            const target = document.querySelector(event.target.value);
            target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });

        window.addEventListener('scroll', scheduleSectionUpdate, { passive: true });
        window.addEventListener('resize', scheduleSectionUpdate);
    }

    const progressKey = `lesson-progress-state-${lessonSlug}`;
    const defaultProgressState = PROGRESS_STEPS.reduce((acc, step) => {
        acc[step] = false;
        return acc;
    }, { summaryRewarded: false });

    const progressState = Object.assign(defaultProgressState, loadState(progressKey, {}));
    if (typeof progressState.summaryRewarded !== 'boolean') {
        progressState.summaryRewarded = false;
    }

    const progressBar = document.querySelector('[data-lesson-progress-bar]');
    const progressLabels = document.querySelectorAll('[data-lesson-progress-count]');
    const levelupBanner = document.querySelector('[data-levelup]');
    const summaryCard = document.querySelector('[data-summary-card]');

    const persistProgressState = () => {
        safeStorage.set(progressKey, JSON.stringify(progressState));
    };

    const xpCard = document.querySelector('[data-xp-card]');
    const xpAmountNode = xpCard?.querySelector('[data-xp-amount]');
    const xpLevelNode = xpCard?.querySelector('[data-xp-level]');
    const xpBadgeNode = xpCard?.querySelector('[data-xp-badge]');
    const xpStreakNode = xpCard?.querySelector('[data-xp-streak]');
    const xpMessageNode = xpCard?.querySelector('[data-xp-message]');
    const streakMessages = document.querySelectorAll('[data-streak-message]');
    const xpRewardTotal = Number.parseInt(xpCard?.dataset.xpReward || '0', 10) || 40;
    const xpStorageKey = xpCard?.dataset.xpKey || `lesson-xp-${lessonSlug}`;

    const defaultXpState = {
        total: Number.parseInt(xpAmountNode?.textContent || '0', 10) || 0,
        level: 1,
        badge: 'Beginner',
        streak: 0,
        lastPlayedAt: null
    };

    const xpState = Object.assign(defaultXpState, loadState(xpStorageKey, null) || {});

    const computeLevel = (xp) => Math.max(1, Math.floor(xp / 120) + 1);
    const computeBadge = (level) => {
        if (level >= 5) {
            return 'Legendă';
        }
        if (level >= 3) {
            return 'Explorator';
        }
        return 'Începător';
    };

    const persistXpState = () => {
        safeStorage.set(xpStorageKey, JSON.stringify(xpState));
    };

    const updateStreakMessage = () => {
        const text = xpState.streak
            ? `Tu deja ai parcurs ${xpState.streak} zile la rand. Tine-l aprins!`
            : 'Prima zi din streak incepe acum.';
        streakMessages.forEach((node) => {
            node.textContent = text;
        });
    };

    const updateXpCard = () => {
        if (!xpCard) {
            return;
        }
        if (xpAmountNode) {
            xpAmountNode.textContent = xpState.total;
        }
        if (xpLevelNode) {
            xpLevelNode.textContent = xpState.level;
        }
        if (xpBadgeNode) {
            xpBadgeNode.textContent = xpState.badge;
        }
        if (xpStreakNode) {
            xpStreakNode.textContent = xpState.streak || 0;
        }
        if (xpMessageNode) {
            xpMessageNode.textContent = xpState.streak
                ? `Tu deja ai trecut ${xpState.streak} misiuni la rand!`
                : 'Completeaza prima misiune pentru a porni streak-ul.';
        }
        updateStreakMessage();
    };

    const awardXp = (amount, reason) => {
        if (!xpCard || !amount) {
            return;
        }
        const now = new Date();
        const lastAward = xpState.lastPlayedAt ? new Date(xpState.lastPlayedAt) : null;
        xpState.total = Math.max(0, Math.round(xpState.total + amount));
        if (lastAward) {
            const diffDays = Math.floor((now - lastAward) / 86400000);
            if (diffDays === 1) {
                xpState.streak = (xpState.streak || 0) + 1;
            } else if (diffDays > 1) {
                xpState.streak = 1;
            }
        } else {
            xpState.streak = 1;
        }
        xpState.lastPlayedAt = now.toISOString();
        xpState.level = computeLevel(xpState.total);
        xpState.badge = computeBadge(xpState.level);
        xpState.lastReason = reason || '';
        persistXpState();
        updateXpCard();
    };

    updateXpCard();

    const STEP_XP = {
        example: 10,
        practice: 5,
        test: 7,
        summary: xpRewardTotal
    };

    const triggerXpReward = (step) => {
        const amount = STEP_XP[step];
        if (amount) {
            awardXp(amount, step);
        }
    };

    const updateProgressUI = () => {
        const completed = PROGRESS_STEPS.reduce((acc, step) => acc + (progressState[step] ? 1 : 0), 0);
        const percent = Math.round((completed / PROGRESS_STEPS.length) * 100);
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', String(percent));
        }
        progressLabels.forEach((node) => {
            node.textContent = percent;
        });
        stageButtons.forEach((button, stage) => {
            button.classList.toggle('is-complete', !!progressState[stage]);
            button.classList.toggle('is-active', stage === activeStage);
        });
    };

    const handleSummaryUnlocked = () => {
        if (levelupBanner) {
            levelupBanner.removeAttribute('aria-hidden');
            levelupBanner.classList.add('is-visible');
        }
        summaryCard?.classList.add('is-celebrating');
        if (!progressState.summaryRewarded) {
            triggerXpReward('summary');
            progressState.summaryRewarded = true;
            persistProgressState();
        }
    };

    const setProgressStep = (step, value, { skipAuto = false } = {}) => {
        if (!(step in progressState) || progressState[step] === value) {
            return false;
        }
        progressState[step] = value;
        if (!value && step !== 'summary' && progressState.summary) {
            progressState.summary = false;
        }
        persistProgressState();
        updateProgressUI();
        if (value && step !== 'summary') {
            triggerXpReward(step);
        }
        if (step === 'summary' && value) {
            handleSummaryUnlocked();
        }
        if (!skipAuto && step !== 'summary') {
            const coreStepsComplete = PROGRESS_STEPS
                .filter((name) => name !== 'summary')
                .every((name) => progressState[name]);
            if (coreStepsComplete) {
                setProgressStep('summary', true, { skipAuto: true });
            }
        }
        return true;
    };

    updateProgressUI();

    if (immersiveMode) {
        setProgressStep('concept', true, { skipAuto: true });
        activateImmersivePanel?.(initialImmersivePanel, { updateHash: false });
    }

    const conceptSection = document.querySelector('#concept');
    if (!immersiveMode && conceptSection && !progressState.concept && 'IntersectionObserver' in window) {
        const conceptObserver = new IntersectionObserver((entries) => {
            if (entries.some((entry) => entry.isIntersecting)) {
                setProgressStep('concept', true);
                conceptObserver.disconnect();
            }
        }, { threshold: 0.4 });
        conceptObserver.observe(conceptSection);
    }

    document.querySelectorAll('[data-copy-code]').forEach((button) => {
        button.addEventListener('click', async () => {
            const wrapper = button.closest('[data-code-block]') || button.closest('.lesson-snippet');
            const codeElement = wrapper?.querySelector('code');
            if (!codeElement) {
                return;
            }
            try {
                await navigator.clipboard.writeText(codeElement.innerText.trim());
                const original = button.textContent;
                button.textContent = 'Copiat!';
                setTimeout(() => {
                button.textContent = original || 'Copiaza';
                }, 1600);
            } catch (error) {
                console.error('Copy failed', error);
            }
        });
    });

    const codeLab = document.querySelector('[data-code-lab]');
    if (codeLab) {
        const codeInput = codeLab.querySelector('[data-code-input]');
        const codePreviewWrapper = codeLab.querySelector('[data-code-preview]');
        const codePreview = codePreviewWrapper?.querySelector('code') || codePreviewWrapper;
        const codeOutput = codeLab.querySelector('[data-code-output]');
        const codeStatus = codeLab.querySelector('[data-code-status]');
        const stdinField = codeLab.querySelector('[data-code-stdin]');
        const runButton = codeLab.querySelector('[data-code-run]');
        const resetButton = codeLab.querySelector('[data-code-reset]');
        const rewardBadge = codeLab.querySelector('[data-code-reward]');
        const missionStatus = codeLab.querySelector('[data-code-mission-status]');
        const checkAssignNode = codeLab.querySelector('[data-code-check="assign"]');
        const checkPrintNode = codeLab.querySelector('[data-code-check="print"]');
        const arenaGrid = codeLab.querySelector('[data-code-arena-grid]');
        const arenaStatus = codeLab.querySelector('[data-code-arena-status]');
        const normalizeStarterCode = (source) => {
            const normalized = String(source || '').replace(/\r\n/g, '\n');
            if (!normalized.includes('\n') && normalized.includes('\\n')) {
                return normalized.replace(/\\n/g, '\n');
            }
            return normalized;
        };

        const initialCode = normalizeStarterCode(codeInput?.value || '');
        const defaultConsoleText = (codeOutput?.textContent || 'Consola așteaptă să rulezi codul...').trim();
        const arenaTrack = ['S', '.', 'V', '.', 'P', '.', 'G'];
        const arenaCells = [];
        let arenaRobotIndex = 0;
        let arenaAnimationToken = 0;
        let arenaMissionState = {
            hasAssignment: false,
            hasPrint: false,
            completed: false,
        };
        const evaluateMissionState = () => {
            const source = codeInput?.value || '';
            const hasAssignment = /[A-Za-z_]\w*\s*=\s*.+/m.test(source);
            const hasPrint = /\bprint\s*\(/m.test(source);
            checkAssignNode?.classList.toggle('is-done', hasAssignment);
            checkPrintNode?.classList.toggle('is-done', hasPrint);
            return {
                hasAssignment,
                hasPrint,
                completed: hasAssignment && hasPrint,
            };
        };

        const setArenaStatus = (message) => {
            if (arenaStatus) {
                arenaStatus.textContent = message;
            }
        };

        const arenaTargetIndex = (missionState) => {
            if (missionState.completed) {
                return 6;
            }
            if (missionState.hasPrint) {
                return 4;
            }
            if (missionState.hasAssignment) {
                return 2;
            }
            return 0;
        };

        const applyArenaCellState = () => {
            if (!arenaCells.length) {
                return;
            }
            arenaCells.forEach((cell, index) => {
                const marker = arenaTrack[index];
                const isCheckpoint = index === 2 || index === 4 || index === 6;
                const isComplete = index === 0
                    || (index === 2 && arenaMissionState.hasAssignment)
                    || (index === 4 && arenaMissionState.hasPrint)
                    || (index === 6 && arenaMissionState.completed);
                cell.classList.toggle('is-checkpoint', isCheckpoint);
                cell.classList.toggle('is-goal', index === 6);
                cell.classList.toggle('is-complete', isComplete);
                cell.classList.toggle('has-robot', index === arenaRobotIndex);
                cell.textContent = index === arenaRobotIndex ? 'R' : (marker === '.' ? '-' : marker);
            });
        };

        const syncArenaFeedback = () => {
            if (arenaMissionState.completed) {
                setArenaStatus('Super! Ai trecut prin toate checkpoint-urile.');
                return;
            }
            if (arenaMissionState.hasAssignment && !arenaMissionState.hasPrint) {
                setArenaStatus('Variabila este gata. Acum adauga print() pentru poarta finala.');
                return;
            }
            if (!arenaMissionState.hasAssignment && arenaMissionState.hasPrint) {
                setArenaStatus('Ai print(), dar lipseste definirea variabilei.');
                return;
            }
            setArenaStatus('Scrie o variabila si un print(), apoi apasa Run.');
        };

        const animateArenaTo = async (targetIndex) => {
            if (!arenaCells.length) {
                return;
            }
            const token = ++arenaAnimationToken;
            const safeTarget = Math.max(0, Math.min(targetIndex, arenaTrack.length - 1));
            while (arenaRobotIndex !== safeTarget) {
                arenaRobotIndex += safeTarget > arenaRobotIndex ? 1 : -1;
                applyArenaCellState();
                await new Promise((resolve) => window.setTimeout(resolve, 170));
                if (token !== arenaAnimationToken) {
                    return;
                }
            }
        };

        const updateArena = async (missionState, { animate = false, forceReset = false } = {}) => {
            if (!arenaGrid) {
                return;
            }
            arenaMissionState = missionState;
            const target = forceReset ? 0 : arenaTargetIndex(missionState);
            if (animate) {
                await animateArenaTo(target);
            } else {
                arenaRobotIndex = target;
            }
            applyArenaCellState();
            syncArenaFeedback();
        };

        if (arenaGrid) {
            arenaGrid.innerHTML = '';
            arenaTrack.forEach((_, index) => {
                const cell = document.createElement('div');
                cell.className = 'code-lab__arena-cell';
                cell.dataset.arenaIndex = String(index);
                arenaGrid.appendChild(cell);
                arenaCells.push(cell);
            });
        }

        if (codeInput && codeInput.value !== initialCode) {
            codeInput.value = initialCode;
        }

        const syncPreview = () => {
            if (!codeInput || !codePreview) {
                return;
            }
            codePreview.textContent = codeInput.value;
            if (window.Prism?.highlightElement) {
                window.Prism.highlightElement(codePreview);
            }
        };

        codeInput?.addEventListener('input', () => {
            syncPreview();
            const missionState = evaluateMissionState();
            updateArena(missionState);
            setProgressStep('example', false, { skipAuto: true });
        });
        syncPreview();
        const initialMissionState = evaluateMissionState();
        updateArena(initialMissionState);

        if (codeOutput) {
            codeOutput.textContent = defaultConsoleText;
        }

        let pyodideReady = null;
        const ensurePyodide = async () => {
            if (!pyodideReady) {
                pyodideReady = loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/' });
            }
            return pyodideReady;
        };

        const runPythonCode = async (sourceCode) => {
            const pyodide = await ensurePyodide();
            pyodide.globals.set('UNITEX_STDIN_RAW', (stdinField?.value || '').toString());
            await pyodide.runPythonAsync(`
from io import StringIO
import sys, builtins
from collections import deque
_unitex_stdout = sys.stdout
_unitex_stderr = sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()
try:
    _unitex_original_input
except NameError:
    _unitex_original_input = builtins.input
_unitex_queue = deque(UNITEX_STDIN_RAW.splitlines()) if UNITEX_STDIN_RAW else deque()
def _unitex_input(prompt=None):
    return _unitex_queue.popleft() if _unitex_queue else ""
builtins.input = _unitex_input
`);
            let resultText = '';
            try {
                const result = await pyodide.runPythonAsync(sourceCode);
                const stdout = pyodide.runPython('sys.stdout.getvalue()');
                const stderr = pyodide.runPython('sys.stderr.getvalue()');
                resultText = [stdout, stderr].filter(Boolean).join('\n').trim();
                if (!resultText && typeof result !== 'undefined') {
                    resultText = String(result);
                }
            } finally {
                await pyodide.runPythonAsync(`
sys.stdout = _unitex_stdout
sys.stderr = _unitex_stderr
import builtins
builtins.input = _unitex_original_input
`);
            }
            return resultText || 'Nu există output. Folosește print() pentru a afișa valori.';
        };

        const showCodeReward = () => {
            if (!rewardBadge) {
                return;
            }
            rewardBadge.classList.add('is-visible');
            setTimeout(() => {
                rewardBadge.classList.remove('is-visible');
            }, 1900);
        };

        runButton?.addEventListener('click', async () => {
            if (!codeInput || !codeOutput || runButton.disabled) {
                return;
            }
            runButton.disabled = true;
            if (codeStatus) {
                codeStatus.textContent = 'Se încarcă runtime-ul...';
            }
            try {
                await ensurePyodide();
                if (codeStatus) {
                    codeStatus.textContent = 'Rulez codul...';
                }
                const textResult = await runPythonCode(codeInput.value);
                codeOutput.textContent = `Rezultat:\n${textResult}`;
                codeOutput.style.color = 'var(--lesson-success)';
                const missionState = evaluateMissionState();
                await updateArena(missionState, { animate: true });
                if (missionState.completed) {
                    if (codeStatus) {
                        codeStatus.textContent = 'Executarea a reușit. Misiunea e completă.';
                    }
                    if (missionStatus) {
                        missionStatus.textContent = 'Perfect! Ai bifat ambele obiective.';
                    }
                    const changed = setProgressStep('example', true);
                    if (changed) {
                        showCodeReward();
                    }
                } else {
                    if (codeStatus) {
                        codeStatus.textContent = 'Codul rulează, dar misiunea nu e completă.';
                    }
                    if (missionStatus) {
                        missionStatus.textContent = 'Mai ai un pas: adaugă variabilă și/sau print().';
                    }
                    setProgressStep('example', false, { skipAuto: true });
                }
            } catch (error) {
                console.error(error);
                codeOutput.textContent = `Rezultat:\nUps! Codul s-a oprit.\nMesaj: ${error.message}`;
                codeOutput.style.color = 'var(--lesson-danger)';
                const missionState = evaluateMissionState();
                await updateArena(missionState, { animate: false });
                setArenaStatus('Rulare oprita. Corecteaza codul si incearca din nou.');
                if (codeStatus) {
                    codeStatus.textContent = 'Încearcă să corectezi codul și rulează din nou.';
                }
                setProgressStep('example', false);
            } finally {
                runButton.disabled = false;
            }
        });

        resetButton?.addEventListener('click', () => {
            if (!codeInput || !codeOutput) {
                return;
            }
            codeInput.value = initialCode;
            if (stdinField) {
                stdinField.value = '';
            }
            syncPreview();
            codeOutput.textContent = defaultConsoleText;
            codeOutput.style.color = '';
            if (codeStatus) {
                codeStatus.textContent = 'Pregătit ⚡';
            }
            if (missionStatus) {
                missionStatus.textContent = 'Completează checklist-ul, apoi apasă Run.';
            }
            const missionState = evaluateMissionState();
            updateArena(missionState, { animate: true, forceReset: true });
            setProgressStep('example', false, { skipAuto: true });
        });
    }

    const robotLabPreviewMap = document.querySelector('[data-robotlab-preview-map]');
    if (robotLabPreviewMap) {
        const previewCells = Array.from(
            robotLabPreviewMap.querySelectorAll('[data-robotlab-preview-cell]')
        );
        const previewStatus = document.querySelector('[data-robotlab-preview-status]');
        const previewProgress = document.querySelector('[data-robotlab-preview-progress]');
        const previewControls = Array.from(
            document.querySelectorAll('[data-robotlab-preview-control]')
        );

        const previewKey = (row, col) => `${row}:${col}`;
        const previewCellsByKey = new Map();
        previewCells.forEach((cell) => {
            previewCellsByKey.set(
                previewKey(Number(cell.dataset.row || 0), Number(cell.dataset.col || 0)),
                cell
            );
        });

        const findPreviewCell = (kind) =>
            previewCells.find((cell) => cell.dataset.kind === kind) || null;

        const startPreviewCell = findPreviewCell('start');
        const terminalPreviewCell =
            findPreviewCell('terminal') || findPreviewCell('goal');

        const startPreviewPos = startPreviewCell
            ? {
                  row: Number(startPreviewCell.dataset.row || 0),
                  col: Number(startPreviewCell.dataset.col || 0),
              }
            : { row: 0, col: 0 };

        let previewRobotPos = { ...startPreviewPos };
        let previewSteps = 0;

        const previewWalkable = (row, col) => {
            const targetCell = previewCellsByKey.get(previewKey(row, col));
            return Boolean(targetCell && targetCell.dataset.kind !== 'wall');
        };

        const computePreviewDistance = () => {
            if (!terminalPreviewCell) {
                return 1;
            }

            const target = {
                row: Number(terminalPreviewCell.dataset.row || 0),
                col: Number(terminalPreviewCell.dataset.col || 0),
            };
            const seen = new Set([previewKey(startPreviewPos.row, startPreviewPos.col)]);
            const queue = [{ ...startPreviewPos, distance: 0 }];

            while (queue.length) {
                const current = queue.shift();
                if (!current) {
                    break;
                }
                if (current.row === target.row && current.col === target.col) {
                    return Math.max(1, current.distance);
                }
                [
                    [0, 1],
                    [1, 0],
                    [0, -1],
                    [-1, 0],
                ].forEach(([dr, dc]) => {
                    const nextRow = current.row + dr;
                    const nextCol = current.col + dc;
                    const nextKey = previewKey(nextRow, nextCol);
                    if (seen.has(nextKey) || !previewWalkable(nextRow, nextCol)) {
                        return;
                    }
                    seen.add(nextKey);
                    queue.push({
                        row: nextRow,
                        col: nextCol,
                        distance: current.distance + 1,
                    });
                });
            }

            return 1;
        };

        const previewGoalDistance = computePreviewDistance();

        const setPreviewStatus = (message, kind = '') => {
            if (!previewStatus) {
                return;
            }
            previewStatus.textContent = message;
            previewStatus.classList.toggle('is-success', kind === 'success');
        };

        const syncPreviewProgress = () => {
            if (!previewProgress) {
                return;
            }
            const ratio = Math.min(1, previewSteps / previewGoalDistance);
            previewProgress.style.width = `${Math.max(16, Math.round(ratio * 100))}%`;
        };

        const applyPreviewRobot = () => {
            previewCells.forEach((cell) => {
                const row = Number(cell.dataset.row || 0);
                const col = Number(cell.dataset.col || 0);
                cell.classList.toggle(
                    'is-robot',
                    row === previewRobotPos.row && col === previewRobotPos.col
                );
            });
        };

        const resetPreviewRobot = () => {
            previewRobotPos = { ...startPreviewPos };
            previewSteps = 0;
            applyPreviewRobot();
            syncPreviewProgress();
            setPreviewStatus('Ghideaza-l pe Robo spre terminal.');
        };

        const movePreviewRobot = (dr, dc) => {
            const nextRow = previewRobotPos.row + dr;
            const nextCol = previewRobotPos.col + dc;
            if (!previewWalkable(nextRow, nextCol)) {
                setPreviewStatus('Directia este blocata. Incearca alta ruta.');
                return;
            }

            previewRobotPos = { row: nextRow, col: nextCol };
            previewSteps += 1;
            applyPreviewRobot();
            syncPreviewProgress();

            const currentCell = previewCellsByKey.get(previewKey(nextRow, nextCol));
            const currentKind = currentCell?.dataset.kind || '';
            if (currentKind === 'terminal' || currentKind === 'goal') {
                setPreviewStatus('Terminal activat. Robo a ajuns!', 'success');
                if (previewProgress) {
                    previewProgress.style.width = '100%';
                }
                return;
            }

            setPreviewStatus('Bun. Continua sa-l ghidezi pe Robo spre terminal.');
        };

        previewControls.forEach((button) => {
            button.addEventListener('click', () => {
                const control = button.dataset.robotlabPreviewControl;
                if (control === 'reset') {
                    resetPreviewRobot();
                    return;
                }
                if (control === 'up') {
                    movePreviewRobot(-1, 0);
                    return;
                }
                if (control === 'right') {
                    movePreviewRobot(0, 1);
                    return;
                }
                if (control === 'down') {
                    movePreviewRobot(1, 0);
                    return;
                }
                if (control === 'left') {
                    movePreviewRobot(0, -1);
                }
            });
        });

        resetPreviewRobot();
    }

    const hintModal = document.querySelector('[data-lesson-hint-modal]');
    const hintModalTitle = hintModal?.querySelector('[data-lesson-hint-modal-title]');
    const hintModalContent = hintModal?.querySelector('[data-lesson-hint-modal-content]');

    const closeHintModal = () => {
        if (!hintModal || hintModal.hasAttribute('hidden')) {
            return;
        }
        hintModal.setAttribute('hidden', '');
        document.body.classList.remove('lesson-hint-modal-open');
    };

    const openHintModal = ({ title, content }) => {
        if (!hintModal || !hintModalTitle || !hintModalContent) {
            return;
        }
        hintModalTitle.textContent = title || 'Hint';
        hintModalContent.textContent = content || 'Ruleaza activitatea pentru a primi un indiciu.';
        hintModal.removeAttribute('hidden');
        document.body.classList.add('lesson-hint-modal-open');
    };

    document.querySelectorAll('[data-hint-modal-open]').forEach((button) => {
        button.addEventListener('click', () => {
            const title = button.dataset.hintModalTitle || 'Hint';
            const content = button.dataset.hintModalContent || '';
            openHintModal({ title, content });
        });
    });

    document.querySelectorAll('[data-hint-toggle]').forEach((button) => {
        const panel = button.closest('.practice-subcard')?.querySelector('[data-hint-panel]');
        button.addEventListener('click', () => {
            const panelContent = panel?.textContent?.trim() || '';
            openHintModal({
                title: 'Hint practica',
                content: panelContent || 'Ruleaza activitatea pentru a primi un indiciu.',
            });
        });
    });

    hintModal?.querySelectorAll('[data-lesson-hint-modal-close]').forEach((closeButton) => {
        closeButton.addEventListener('click', () => {
            closeHintModal();
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeHintModal();
        }
    });

    const juniorGamesRoot = document.querySelector('[data-junior-games]');
    if (juniorGamesRoot) {
        const juniorStorageKey = `lesson-junior-games-${lessonSlug}`;
        const defaultJuniorState = {
            order: false,
            colors: false,
            memory: false
        };
        const juniorState = Object.assign(defaultJuniorState, loadState(juniorStorageKey, {}));
        const juniorCount = juniorGamesRoot.querySelector('[data-junior-progress-count]');
        const juniorLabel = juniorGamesRoot.querySelector('[data-junior-progress-label]');
        const juniorReward = juniorGamesRoot.querySelector('[data-junior-reward]');
        const juniorCards = new Map(
            Array.from(juniorGamesRoot.querySelectorAll('[data-junior-game]')).map((card) => [card.dataset.juniorGame, card])
        );

        const persistJuniorState = () => {
            safeStorage.set(juniorStorageKey, JSON.stringify(juniorState));
        };

        const refreshJuniorSummary = () => {
            const completed = Object.values(juniorState).filter(Boolean).length;
            if (juniorCount) {
                juniorCount.textContent = `${completed}/3`;
            }
            if (juniorLabel) {
                juniorLabel.textContent = completed === 3
                    ? 'Toate jocurile sunt gata'
                    : 'Misiuni complete';
            }
            juniorCards.forEach((card, gameId) => {
                card.classList.toggle('is-complete', !!juniorState[gameId]);
            });
            if (juniorReward) {
                juniorReward.toggleAttribute('hidden', completed !== 3);
            }
            if (completed === 3) {
                setProgressStep('example', true);
            } else {
                setProgressStep('example', false, { skipAuto: true });
            }
            persistJuniorState();
        };

        const markJuniorGameComplete = (gameId) => {
            if (juniorState[gameId]) {
                return;
            }
            juniorState[gameId] = true;
            refreshJuniorSummary();
        };

        const orderGame = juniorGamesRoot.querySelector('[data-junior-order-game]');
        if (orderGame) {
            const expectedMoves = (orderGame.dataset.juniorOrderExpected || '')
                .split(',')
                .map((item) => item.trim())
                .filter(Boolean);
            const orderTokens = Array.from(orderGame.querySelectorAll('[data-junior-order-token]'));
            const orderSlots = Array.from(orderGame.querySelectorAll('[data-junior-order-slot]'));
            const orderBoardCells = Array.from(orderGame.querySelectorAll('[data-junior-order-board-cell]'));
            const orderFeedback = orderGame.querySelector('[data-junior-order-feedback]');
            const orderVerify = orderGame.querySelector('[data-junior-order-verify]');
            const orderReset = orderGame.querySelector('[data-junior-order-reset]');
            const tokenById = new Map(orderTokens.map((button) => [button.dataset.tokenId, button]));
            const selectedTokens = [];
            let orderAnimationToken = 0;

            const boardKey = (row, col) => `${row}:${col}`;
            const boardCellByKey = new Map(
                orderBoardCells.map((cell) => [boardKey(Number(cell.dataset.row || 0), Number(cell.dataset.col || 0)), cell])
            );
            const startCell = orderBoardCells.find((cell) => cell.dataset.kind === 'start');
            const startPosition = {
                row: Number(startCell?.dataset.row || 0),
                col: Number(startCell?.dataset.col || 0)
            };

            const applyOrderRobot = (position) => {
                orderBoardCells.forEach((cell) => {
                    const row = Number(cell.dataset.row || 0);
                    const col = Number(cell.dataset.col || 0);
                    cell.classList.toggle('is-robot', row === position.row && col === position.col);
                });
            };

            const renderOrderSlots = () => {
                orderSlots.forEach((slot, index) => {
                    const tokenId = selectedTokens[index];
                    const token = tokenId ? tokenById.get(tokenId) : null;
                    slot.classList.toggle('is-filled', !!token);
                    slot.dataset.tokenId = tokenId || '';
                    slot.innerHTML = token
                        ? `<span>${token.querySelector('.junior-token__icon')?.textContent || '?'}</span>`
                        : '<span>?</span>';
                });
                orderTokens.forEach((token) => {
                    token.disabled = selectedTokens.includes(token.dataset.tokenId);
                });
            };

            const resetOrderBoard = () => {
                orderAnimationToken += 1;
                applyOrderRobot(startPosition);
            };

            const resetOrderGame = ({ keepFeedback = false } = {}) => {
                selectedTokens.length = 0;
                renderOrderSlots();
                resetOrderBoard();
                if (!keepFeedback && orderFeedback) {
                    orderFeedback.textContent = 'Robo merge doua casute la dreapta, apoi una in jos.';
                    orderFeedback.classList.remove('is-success', 'is-error');
                }
            };

            const animateOrderSuccess = async () => {
                let position = { ...startPosition };
                const token = ++orderAnimationToken;
                const deltaByMove = {
                    right: [0, 1],
                    left: [0, -1],
                    up: [-1, 0],
                    down: [1, 0]
                };
                applyOrderRobot(position);
                for (const move of expectedMoves) {
                    const [dr, dc] = deltaByMove[move] || [0, 0];
                    position = { row: position.row + dr, col: position.col + dc };
                    const cell = boardCellByKey.get(boardKey(position.row, position.col));
                    if (!cell) {
                        break;
                    }
                    await new Promise((resolve) => window.setTimeout(resolve, 260));
                    if (token !== orderAnimationToken) {
                        return;
                    }
                    applyOrderRobot(position);
                }
            };

            orderTokens.forEach((token) => {
                token.addEventListener('click', () => {
                    if (selectedTokens.length >= orderSlots.length) {
                        return;
                    }
                    selectedTokens.push(token.dataset.tokenId || '');
                    renderOrderSlots();
                    if (orderFeedback) {
                        orderFeedback.textContent = 'Bine! Continua pana completezi toate locurile.';
                        orderFeedback.classList.remove('is-success', 'is-error');
                    }
                });
            });

            orderSlots.forEach((slot, index) => {
                slot.addEventListener('click', () => {
                    if (!selectedTokens[index]) {
                        return;
                    }
                    selectedTokens.splice(index, 1);
                    renderOrderSlots();
                });
            });

            orderVerify?.addEventListener('click', async () => {
                const selectedMoves = selectedTokens.map((tokenId) => tokenById.get(tokenId)?.dataset.move || '');
                if (selectedMoves.length !== expectedMoves.length) {
                    if (orderFeedback) {
                        orderFeedback.textContent = 'Mai completeaza toate locurile pana la terminal.';
                        orderFeedback.classList.add('is-error');
                        orderFeedback.classList.remove('is-success');
                    }
                    return;
                }
                const wrongIndex = selectedMoves.findIndex((move, index) => move !== expectedMoves[index]);
                if (wrongIndex !== -1) {
                    orderSlots[wrongIndex]?.classList.add('is-wrong');
                    window.setTimeout(() => orderSlots[wrongIndex]?.classList.remove('is-wrong'), 700);
                    if (orderFeedback) {
                        orderFeedback.textContent = `Pasul ${wrongIndex + 1} nu este bun. Incearca din nou.`;
                        orderFeedback.classList.add('is-error');
                        orderFeedback.classList.remove('is-success');
                    }
                    return;
                }
                if (orderFeedback) {
                    orderFeedback.textContent = 'Perfect! Robo a gasit drumul pana la terminal.';
                    orderFeedback.classList.add('is-success');
                    orderFeedback.classList.remove('is-error');
                }
                await animateOrderSuccess();
                markJuniorGameComplete('order');
            });

            orderReset?.addEventListener('click', () => {
                resetOrderGame();
            });

            resetOrderGame({ keepFeedback: !!juniorState.order });
            if (juniorState.order && orderFeedback) {
                orderFeedback.textContent = 'Labirintul este deja rezolvat. Poti sa il rejoci oricand.';
                orderFeedback.classList.add('is-success');
            }
        }

        const colorGame = juniorGamesRoot.querySelector('[data-junior-color-game]');
        if (colorGame) {
            const colorButtons = Array.from(colorGame.querySelectorAll('[data-junior-color-card]'));
            const actionButtons = Array.from(colorGame.querySelectorAll('[data-junior-action-card]'));
            const colorFeedback = colorGame.querySelector('[data-junior-color-feedback]');
            const colorProgress = colorGame.querySelector('[data-junior-color-progress]');
            const colorReset = colorGame.querySelector('[data-junior-color-reset]');
            const solvedPairs = new Set();
            let selectedColor = null;
            let selectedAction = null;

            const updateColorBoard = () => {
                colorButtons.forEach((button) => {
                    const pairId = button.dataset.pairId || '';
                    button.classList.toggle('is-selected', button === selectedColor);
                    button.classList.toggle('is-matched', solvedPairs.has(pairId));
                });
                actionButtons.forEach((button) => {
                    const pairId = button.dataset.pairId || '';
                    button.classList.toggle('is-selected', button === selectedAction);
                    button.classList.toggle('is-matched', solvedPairs.has(pairId));
                });
                if (colorProgress) {
                    colorProgress.textContent = `${solvedPairs.size} / ${colorButtons.length} potriviri`;
                }
            };

            const completeColorMatch = () => {
                if (solvedPairs.size === colorButtons.length) {
                    if (colorFeedback) {
                        colorFeedback.textContent = 'Super! Toate culorile sunt potrivite corect.';
                        colorFeedback.classList.add('is-success');
                        colorFeedback.classList.remove('is-error');
                    }
                    markJuniorGameComplete('colors');
                }
            };

            const resolveColorAttempt = () => {
                if (!selectedColor || !selectedAction) {
                    return;
                }
                const colorPair = selectedColor.dataset.pairId || '';
                const actionPair = selectedAction.dataset.pairId || '';
                if (colorPair === actionPair) {
                    solvedPairs.add(colorPair);
                    if (colorFeedback) {
                        colorFeedback.textContent = 'Corect! Ai gasit o pereche buna.';
                        colorFeedback.classList.add('is-success');
                        colorFeedback.classList.remove('is-error');
                    }
                } else if (colorFeedback) {
                    colorFeedback.textContent = 'Nu se potriveste. Mai incearca o data.';
                    colorFeedback.classList.add('is-error');
                    colorFeedback.classList.remove('is-success');
                }
                selectedColor = null;
                selectedAction = null;
                updateColorBoard();
                completeColorMatch();
            };

            colorButtons.forEach((button) => {
                button.addEventListener('click', () => {
                    if (solvedPairs.has(button.dataset.pairId || '')) {
                        return;
                    }
                    selectedColor = button;
                    updateColorBoard();
                    resolveColorAttempt();
                });
            });

            actionButtons.forEach((button) => {
                button.addEventListener('click', () => {
                    if (solvedPairs.has(button.dataset.pairId || '')) {
                        return;
                    }
                    selectedAction = button;
                    updateColorBoard();
                    resolveColorAttempt();
                });
            });

            colorReset?.addEventListener('click', () => {
                solvedPairs.clear();
                selectedColor = null;
                selectedAction = null;
                updateColorBoard();
                if (colorFeedback) {
                    colorFeedback.textContent = 'Alege o culoare, apoi regula potrivita.';
                    colorFeedback.classList.remove('is-success', 'is-error');
                }
            });

            if (juniorState.colors) {
                colorButtons.forEach((button) => solvedPairs.add(button.dataset.pairId || ''));
                if (colorFeedback) {
                    colorFeedback.textContent = 'Jocul de culori este deja completat.';
                    colorFeedback.classList.add('is-success');
                }
            }
            updateColorBoard();
        }

        const memoryGame = juniorGamesRoot.querySelector('[data-junior-memory-game]');
        if (memoryGame) {
            const memoryDeck = memoryGame.querySelector('[data-junior-memory-deck]');
            const memoryCards = Array.from(memoryGame.querySelectorAll('[data-junior-memory-card]'));
            const memoryFeedback = memoryGame.querySelector('[data-junior-memory-feedback]');
            const memoryProgress = memoryGame.querySelector('[data-junior-memory-progress]');
            const memoryReset = memoryGame.querySelector('[data-junior-memory-reset]');
            const allPairs = [...new Set(memoryCards.map((card) => card.dataset.pair || ''))].filter(Boolean);
            const matchedPairs = new Set(juniorState.memory ? allPairs : []);
            let openedCards = [];
            let memoryLocked = false;

            const shuffleMemoryCards = () => {
                if (!memoryDeck || matchedPairs.size === allPairs.length) {
                    return;
                }
                [...memoryCards]
                    .sort(() => Math.random() - 0.5)
                    .forEach((card) => memoryDeck.appendChild(card));
            };

            const updateMemoryBoard = () => {
                memoryCards.forEach((card) => {
                    const pairId = card.dataset.pair || '';
                    const isMatched = matchedPairs.has(pairId);
                    const isOpened = openedCards.includes(card);
                    card.classList.toggle('is-flipped', isMatched || isOpened);
                    card.classList.toggle('is-matched', isMatched);
                });
                if (memoryProgress) {
                    memoryProgress.textContent = `${matchedPairs.size} / ${allPairs.length} perechi`;
                }
            };

            const completeMemoryGame = () => {
                if (matchedPairs.size === allPairs.length) {
                    if (memoryFeedback) {
                        memoryFeedback.textContent = 'Excelent! Ai gasit toate perechile.';
                        memoryFeedback.classList.add('is-success');
                        memoryFeedback.classList.remove('is-error');
                    }
                    markJuniorGameComplete('memory');
                }
            };

            memoryCards.forEach((card) => {
                card.addEventListener('click', () => {
                    const pairId = card.dataset.pair || '';
                    if (memoryLocked || matchedPairs.has(pairId) || openedCards.includes(card)) {
                        return;
                    }
                    openedCards.push(card);
                    updateMemoryBoard();
                    if (openedCards.length < 2) {
                        return;
                    }
                    const [firstCard, secondCard] = openedCards;
                    const isMatch = (firstCard.dataset.pair || '') === (secondCard.dataset.pair || '');
                    if (isMatch) {
                        matchedPairs.add(firstCard.dataset.pair || '');
                        openedCards = [];
                        updateMemoryBoard();
                        if (memoryFeedback) {
                            memoryFeedback.textContent = 'Pereche gasita! Continua.';
                            memoryFeedback.classList.add('is-success');
                            memoryFeedback.classList.remove('is-error');
                        }
                        completeMemoryGame();
                        return;
                    }
                    memoryLocked = true;
                    if (memoryFeedback) {
                        memoryFeedback.textContent = 'Nu sunt la fel. Incearca alte doua carti.';
                        memoryFeedback.classList.add('is-error');
                        memoryFeedback.classList.remove('is-success');
                    }
                    window.setTimeout(() => {
                        openedCards = [];
                        memoryLocked = false;
                        updateMemoryBoard();
                    }, 700);
                });
            });

            memoryReset?.addEventListener('click', () => {
                openedCards = [];
                matchedPairs.clear();
                memoryLocked = false;
                shuffleMemoryCards();
                updateMemoryBoard();
                if (memoryFeedback) {
                    memoryFeedback.textContent = 'Intoarce doua carti si gaseste perechile.';
                    memoryFeedback.classList.remove('is-success', 'is-error');
                }
            });

            shuffleMemoryCards();
            updateMemoryBoard();
            if (juniorState.memory && memoryFeedback) {
                memoryFeedback.textContent = 'Memory deck este deja completat.';
                memoryFeedback.classList.add('is-success');
            }
        }

        refreshJuniorSummary();
    }

    const practiceContainer = document.querySelector('[data-drag-container]');
    const orderFeedback = document.querySelector('[data-order-feedback]');
    const orderCelebration = document.querySelector('[data-order-celebration]');
    const practiceExplanation = document.querySelector('[data-practice-explanation]');
    const practiceDefaultExplanation = practiceExplanation?.dataset.practiceDefault || practiceExplanation?.textContent || '';
    const successMessage = document.querySelector('[data-draggable-target]')?.dataset.successMessage || 'Super! Ordinea este corectă.';

    if (practiceContainer && window.Sortable) {
        const sourceList = practiceContainer.querySelector('[data-draggable-source]');
        const dropZones = Array.from(practiceContainer.querySelectorAll('[data-drop-zone]'));

        const ensurePlaceholder = (zone) => {
            if (!zone.querySelector('[data-placeholder]')) {
                const placeholder = document.createElement('span');
                placeholder.dataset.placeholder = 'true';
                placeholder.textContent = 'Trage elementul aici';
                zone.appendChild(placeholder);
            }
        };

        const resetPractice = () => {
            if (!sourceList) {
                return;
            }
            dropZones.forEach((zone) => {
                const slot = zone.closest('.match-slot');
                const tokens = Array.from(zone.querySelectorAll('.match-token'));
                tokens.forEach((token) => {
                    token.classList.remove('match-token--compact', 'is-correct', 'is-wrong');
                    sourceList.appendChild(token);
                });
                zone.innerHTML = '';
                ensurePlaceholder(zone);
                slot?.classList.remove('is-filled', 'is-correct', 'is-wrong');
            });
            orderCelebration?.classList.remove('is-visible');
            if (orderFeedback) {
                orderFeedback.textContent = '';
                orderFeedback.classList.remove('success', 'error');
            }
            if (practiceExplanation) {
                practiceExplanation.textContent = practiceDefaultExplanation;
            }
            setProgressStep('practice', false);
        };

        if (sourceList) {
            Sortable.create(sourceList, {
                group: { name: 'lesson-practice', pull: true, put: true },
                animation: 180,
                sort: false
            });
        }

        dropZones.forEach((zone) => {
            ensurePlaceholder(zone);
            Sortable.create(zone, {
                group: { name: 'lesson-practice', pull: true, put: true },
                animation: 150,
                sort: false,
                onAdd(evt) {
                    const slot = zone.closest('.match-slot');
                    zone.querySelector('[data-placeholder]')?.remove();
                    const existing = zone.querySelectorAll('.match-token');
                    if (existing.length > 1 && sourceList) {
                        Array.from(existing)
                            .slice(0, -1)
                            .forEach((token) => sourceList.appendChild(token));
                    }
                    evt.item.classList.add('match-token--compact');
                    slot?.classList.add('is-filled');
                    orderFeedback?.classList.remove('success', 'error');
                    setProgressStep('practice', false, { skipAuto: true });
                },
                onRemove() {
                    if (!zone.querySelector('.match-token')) {
                        zone.closest('.match-slot')?.classList.remove('is-filled', 'is-correct', 'is-wrong');
                        ensurePlaceholder(zone);
                    }
                }
            });
        });

        const checkButton = document.querySelector('[data-order-check]');
        const resetButton = document.querySelector('[data-order-reset]');

        checkButton?.addEventListener('click', () => {
            if (!dropZones.length) {
                return;
            }
            let perfectMatch = true;
            let firstWrongLabel = '';
            dropZones.forEach((zone) => {
                const slot = zone.closest('.match-slot');
                slot?.classList.remove('is-correct', 'is-wrong');
                const expected = zone.dataset.expectedId;
                const token = zone.querySelector('.match-token');
                if (token && expected && token.dataset.id === expected) {
                    slot?.classList.add('is-correct');
                } else {
                    slot?.classList.add('is-wrong');
                    perfectMatch = false;
                    if (!firstWrongLabel) {
                        firstWrongLabel = slot?.querySelector('.match-slot__label')?.textContent?.trim() || '';
                    }
                }
            });

            if (perfectMatch) {
                if (orderFeedback) {
                    orderFeedback.textContent = successMessage;
                    orderFeedback.classList.add('success');
                    orderFeedback.classList.remove('error');
                }
                orderCelebration?.classList.add('is-visible');
                if (practiceExplanation) {
                    practiceExplanation.textContent = 'Ai asociat perfect toate conceptele. XP +5!';
                }
                setProgressStep('practice', true);
            } else {
                if (orderFeedback) {
                    orderFeedback.textContent = firstWrongLabel
                        ? `Mai verifică potrivirea pentru \"${firstWrongLabel}\".`
                        : 'Mai încearcă - unele potriviri sunt greșite.';
                    orderFeedback.classList.add('error');
                    orderFeedback.classList.remove('success');
                }
                if (practiceExplanation) {
                    practiceExplanation.textContent = firstWrongLabel
                        ? `Indiciu: recitește descrierea pentru \"${firstWrongLabel}\" și caută cuvintele cheie din token.`
                        : practiceDefaultExplanation;
                }
                orderCelebration?.classList.remove('is-visible');
                setProgressStep('practice', false, { skipAuto: true });
            }
        });

        resetButton?.addEventListener('click', () => {
            resetPractice();
        });

        if (progressState.practice) {
            orderCelebration?.classList.add('is-visible');
            if (orderFeedback) {
                orderFeedback.textContent = successMessage;
                orderFeedback.classList.add('success');
            }
        }
    }

    const quizCard = document.querySelector('[data-quiz]');
    const quizForm = quizCard?.querySelector('form');
    const quizSubmitUrl = quizCard?.dataset.submitHref || quizForm?.getAttribute('action');
    const quizOptions = Array.from(quizCard?.querySelectorAll('[data-quiz-option]') ?? []);
    const quizReset = quizCard?.querySelector('[data-quiz-reset]');
    const quizFeedback = quizCard?.querySelector('[data-quiz-feedback]');
    const quizExplanationBlock = quizCard?.querySelector('[data-quiz-explanation-block]');
    const quizExplanationText = quizCard?.querySelector('[data-quiz-explanation-text]');
    const quizExplanation = quizCard?.dataset.quizExplanation || 'Gândește-te la definiția conceptului și cum îl folosești ulterior.';
    const quizStorageKey = `lesson-quiz-${lessonSlug}`;
    const quizSubmitButton = quizForm?.querySelector('button[type="submit"]');

    const updateOptionStates = () => {
        quizOptions.forEach((label) => {
            const input = label.querySelector('input');
            label.classList.toggle('is-selected', input?.checked || false);
        });
    };

    const clearOptionHighlights = () => {
        quizOptions.forEach((label) => label.classList.remove('is-correct', 'is-wrong'));
    };

    const highlightQuizResult = ({ selectedValue, correctValue, isCorrect }) => {
        clearOptionHighlights();
        quizOptions.forEach((label) => {
            const input = label.querySelector('input');
            if (!input) {
                return;
            }
            if (input.value === selectedValue) {
                label.classList.add(isCorrect ? 'is-correct' : 'is-wrong');
            }
            if (!isCorrect && input.value === correctValue) {
                label.classList.add('is-correct');
            }
        });
    };

    const persistQuiz = (value) => {
        safeStorage.set(quizStorageKey, JSON.stringify(value));
    };

    const applyStoredQuiz = () => {
        const stored = loadState(quizStorageKey, null);
        quizForm?.reset();
        clearOptionHighlights();
        updateOptionStates();
        if (!stored || !stored.answer) {
            quizFeedback?.classList.remove('success', 'error');
            if (quizFeedback) {
                quizFeedback.textContent = '';
            }
            quizExplanationBlock?.classList.add('hidden');
            if (quizExplanationText) {
                quizExplanationText.textContent = quizExplanation;
            }
            setProgressStep('test', false);
            return;
        }
        quizForm?.querySelectorAll('input[name="answer"]').forEach((input) => {
            input.checked = input.value === stored.answer;
        });
        updateOptionStates();
        highlightQuizResult({
            selectedValue: stored.answer,
            correctValue: stored.correctAnswer || stored.answer,
            isCorrect: !!stored.correct,
        });
        if (quizFeedback) {
            quizFeedback.textContent = stored.message || '';
            quizFeedback.classList.toggle('success', !!stored.correct);
            quizFeedback.classList.toggle('error', !stored.correct);
        }
        if (quizExplanationBlock) {
            quizExplanationBlock.classList.remove('hidden');
        }
        if (quizExplanationText) {
            quizExplanationText.textContent = stored.explanation || quizExplanation;
        }
        setProgressStep('test', !!stored.correct);
    };

    quizOptions.forEach((label) => {
        const input = label.querySelector('input');
        input?.addEventListener('change', () => {
            updateOptionStates();
            clearOptionHighlights();
            quizFeedback?.classList.remove('success', 'error');
        });
    });

    quizForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (!quizSubmitUrl) {
            return;
        }
        const formData = new FormData(quizForm);
        const answer = formData.get('answer');
        if (!answer) {
            if (quizFeedback) {
                quizFeedback.textContent = 'Alege o variantă înainte de a trimite.';
                quizFeedback.classList.add('error');
                quizFeedback.classList.remove('success');
            }
            return;
        }
        quizFeedback?.classList.remove('success', 'error');
        if (quizFeedback) {
            quizFeedback.textContent = 'Se verifică răspunsul...';
        }
        quizSubmitButton?.setAttribute('disabled', 'disabled');
        try {
            const response = await fetch(quizSubmitUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ answer }),
            });
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            const data = await response.json();
            const isCorrect = Boolean(data.is_correct);
            const correctAnswer = data.correct_answer || answer;
            const explanationText = data.explanation || quizExplanation;
            highlightQuizResult({ selectedValue: answer, correctValue: correctAnswer, isCorrect });
            if (quizFeedback) {
                quizFeedback.textContent = isCorrect
                    ? 'Corect! Continuă seria.'
                    : `Răspunsul corect este: ${correctAnswer}.`;
                quizFeedback.classList.toggle('success', isCorrect);
                quizFeedback.classList.toggle('error', !isCorrect);
            }
            if (quizExplanationBlock) {
                quizExplanationBlock.classList.remove('hidden');
            }
            if (quizExplanationText) {
                quizExplanationText.textContent = explanationText;
            }
            persistQuiz({
                answer,
                correct: isCorrect,
                correctAnswer,
                explanation: explanationText,
                message: quizFeedback?.textContent,
            });
            setProgressStep('test', isCorrect);
            if (isCorrect && data.lesson_completed) {
                const toggleButton = document.querySelector('.toggle-completion');
                setLessonCompletionUI(true, toggleButton || null);
                updateProgressDisplays({
                    percent: data.progress_percent,
                    completed: data.completed_count,
                    total: data.total_lessons,
                });
            }
        } catch (error) {
            console.error('Quiz submission failed', error);
            if (quizFeedback) {
                quizFeedback.textContent = 'A apărut o eroare. Încearcă din nou.';
                quizFeedback.classList.add('error');
                quizFeedback.classList.remove('success');
            }
        } finally {
            quizSubmitButton?.removeAttribute('disabled');
        }
    });

    quizReset?.addEventListener('click', () => {
        quizForm?.reset();
        clearOptionHighlights();
        updateOptionStates();
        if (quizFeedback) {
            quizFeedback.textContent = '';
            quizFeedback.classList.remove('success', 'error');
        }
        quizExplanationBlock?.classList.add('hidden');
        if (quizExplanationText) {
            quizExplanationText.textContent = quizExplanation;
        }
        persistQuiz({});
        setProgressStep('test', false);
    });

    applyStoredQuiz();

    const wireAiHintForms = () => {
        document.querySelectorAll('[data-ai-hint-form]').forEach((form) => {
            const action = form.getAttribute('action');
            const textarea = form.querySelector('textarea[name="question"]');
            const submitButton = form.querySelector('button[type="submit"]');
            const statusNode = form.querySelector('[data-ai-hint-status]');
            const resultBlock = form.querySelector('[data-ai-hint-output]');
            const resultText = resultBlock?.querySelector('p');

            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                if (!action || !textarea) {
                    return;
                }
                const question = textarea.value.trim();
                if (question.length < 6) {
                    if (statusNode) {
                        statusNode.textContent = 'Scrie o întrebare puțin mai detaliată.';
                    }
                    return;
                }
                submitButton?.setAttribute('disabled', 'disabled');
                if (statusNode) {
                    statusNode.textContent = 'Se trimite cererea către asistent...';
                }
                resultBlock?.classList.add('hidden');
                try {
                    const response = await fetch(action, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCsrfToken(),
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({ question }),
                    });
                    if (!response.ok) {
                        throw new Error(`Server responded with ${response.status}`);
                    }
                    const data = await response.json();
                    if (resultText) {
                        resultText.textContent = data.answer || 'Nu am reușit să generăm un indiciu acum.';
                    }
                    resultBlock?.classList.remove('hidden');
                    if (statusNode) {
                        statusNode.textContent = 'Gata! Vezi răspunsul mai jos.';
                    }
                } catch (error) {
                    console.error('AI hint failed', error);
                    if (statusNode) {
                        statusNode.textContent = 'Nu am putut obține indiciul. Încearcă din nou.';
                    }
                } finally {
                    submitButton?.removeAttribute('disabled');
                }
            });
        });
    };

    wireAiHintForms();

    document.querySelectorAll('[data-accordion]').forEach((accordion) => {
        const toggle = accordion.querySelector('[data-accordion-toggle]');
        const panel = accordion.querySelector('[data-accordion-panel]');
        toggle?.addEventListener('click', () => {
            if (!panel) {
                return;
            }
            const isOpen = panel.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', String(isOpen));
        });
    });

    if (!immersiveMode) {
        scheduleSectionUpdate();
    }
})();
