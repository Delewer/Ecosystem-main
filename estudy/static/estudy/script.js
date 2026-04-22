/* eslint-env browser */

(() => {

const STORAGE_KEYS = {
    theme: 'unitex-theme',
    lessonFilters: 'unitex-lessons-filters',
};

const safeLocalStorage = {
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
    },
};

const applyTheme = (theme) => {
    const root = document.documentElement;
    const normalized = theme === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-theme', normalized);
    document.body.classList.toggle('theme-dark', normalized === 'dark');
    document.querySelectorAll('[data-theme-toggle]').forEach((toggle) => {
        toggle.setAttribute('data-theme-state', normalized);
        const label = toggle.querySelector('[data-theme-toggle-label]');
        if (label) {
            label.textContent = normalized === 'dark' ? 'Noapte' : 'Zi';
        }
    });
};

const initializeThemeControls = () => {
    const stored = safeLocalStorage.get(STORAGE_KEYS.theme);
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(stored || (prefersDark ? 'dark' : 'light'));

    document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
        if (button.dataset.unitexThemeBound === 'true') {
            return;
        }
        button.dataset.unitexThemeBound = 'true';
        button.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            safeLocalStorage.set(STORAGE_KEYS.theme, next);
            applyTheme(next);
        });
    });
};

const getCsrfToken = () => {
    const value = document.cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith("csrftoken="));
    return value ? decodeURIComponent(value.split("=")[1]) : "";
};

const updateProgressDisplays = ({ percent, completed, total }) => {
    if (percent !== null && percent !== undefined) {
        const roundedPercent = Math.round(percent);
        document.querySelectorAll('[data-progress-bar]').forEach((bar) => {
            bar.dataset.progressInitial = String(roundedPercent);
            const container = bar.closest('[data-progress-container]');
            if (container) {
                container.dataset.progressInitial = String(roundedPercent);
            }
        });
        initializeProgressBars();
    }

    if (Number.isFinite(completed)) {
        document.querySelectorAll('[data-progress-completed]').forEach((node) => {
            node.textContent = completed;
        });
    }

    if (Number.isFinite(total)) {
        document.querySelectorAll('[data-progress-total]').forEach((node) => {
            node.textContent = total;
        });
    }

    if (Number.isFinite(completed) && Number.isFinite(total)) {
        document.querySelectorAll('[data-progress-summary]').forEach((node) => {
            const safeCompleted = Number.parseInt(completed, 10);
            const safeTotal = Number.parseInt(total, 10);
            if (!Number.isFinite(safeCompleted) || !Number.isFinite(safeTotal)) {
                return;
            }

            if (safeCompleted === 1) {
                node.textContent = `1 lecție finalizată din ${safeTotal}`;
            } else {
                node.textContent = `${safeCompleted} lecții finalizate din ${safeTotal}`;
            }
        });
    }
};

const initializeProgressBars = () => {
    document.querySelectorAll('[data-progress-bar]').forEach((bar) => {
        const container = bar.closest('[data-progress-container]');
        const sourceValue =
            bar.dataset.progressInitial ||
            container?.dataset.progressInitial ||
            bar.getAttribute('aria-valuenow');

        if (sourceValue === null || sourceValue === undefined || sourceValue === '') {
            return;
        }

        const parsed = Number.parseFloat(sourceValue);
        if (!Number.isFinite(parsed)) {
            return;
        }

        const clamped = Math.max(0, Math.min(100, Math.round(parsed)));
        bar.dataset.progressInitial = String(clamped);

        const shouldAnimate = !bar.dataset.progressAnimated;
        if (shouldAnimate) {
            bar.dataset.progressAnimated = 'true';
            bar.style.width = '0%';
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    bar.style.width = `${clamped}%`;
                });
            });
        } else {
            bar.style.width = `${clamped}%`;
        }

        bar.setAttribute('aria-valuenow', String(clamped));
        const percentHolder = bar.querySelector('[data-progress-percent]');
        if (percentHolder) {
            percentHolder.textContent = clamped;
        }

        if (container) {
            container.dataset.progressInitial = String(clamped);
            const sparkle = container.querySelector('[data-progress-sparkle]');
            if (clamped >= 100 && sparkle && sparkle.dataset.sparklePlayed !== 'true') {
                container.classList.remove('is-complete');
                requestAnimationFrame(() => {
                    container.classList.add('is-complete');
                    sparkle.dataset.sparklePlayed = 'true';
                });
            } else if (clamped < 100) {
                container.classList.remove('is-complete');
                if (sparkle) {
                    sparkle.dataset.sparklePlayed = 'false';
                }
            }
        }
    });
};

const getNextButton = () => document.querySelector('[data-next-button]');

const splitClasses = (value) => (value || '').split(/\s+/).map((item) => item.trim()).filter(Boolean);

const splitList = (value) => (value || '').split(/[,|]/).map((item) => item.trim().toLowerCase()).filter(Boolean);

const addClasses = (element, value) => {
    splitClasses(value).forEach((className) => element.classList.add(className));
};

const removeClasses = (element, value) => {
    splitClasses(value).forEach((className) => element.classList.remove(className));
};

const getNextButtonMeta = (button) => ({
    url: button.dataset.nextUrl || button.getAttribute('href') || '#',
    enabledClass: button.dataset.nextEnabledClass || 'btn-primary',
    disabledClass: button.dataset.nextDisabledClass || 'btn-outline-secondary',
    labelLocked: button.dataset.nextLabelLocked || '<i class="fa-solid fa-lock me-2"></i>Lecția următoare',
    labelUnlocked: button.dataset.nextLabelUnlocked || '<i class="fa-solid fa-arrow-right me-2"></i>Lecția următoare',
});

const setNextButtonState = (isUnlocked) => {
    const button = getNextButton();
    if (!button) {
        return;
    }

    const meta = getNextButtonMeta(button);
    if (isUnlocked) {
        removeClasses(button, meta.disabledClass);
        addClasses(button, meta.enabledClass);
        button.classList.remove('disabled');
        button.removeAttribute('aria-disabled');
        button.dataset.locked = 'false';
        button.href = meta.url;
        button.innerHTML = meta.labelUnlocked;
    } else {
        removeClasses(button, meta.enabledClass);
        addClasses(button, meta.disabledClass);
        button.classList.add('disabled');
        button.setAttribute('aria-disabled', 'true');
        button.dataset.locked = 'true';
        button.innerHTML = meta.labelLocked;
    }
};

const initializeNextButtonState = () => {
    const button = getNextButton();
    if (!button) {
        return;
    }

    const meta = getNextButtonMeta(button);
    if (!button.dataset.nextLabelLocked) {
        button.dataset.nextLabelLocked = meta.labelLocked;
    }
    if (!button.dataset.nextLabelUnlocked) {
        button.dataset.nextLabelUnlocked = meta.labelUnlocked;
    }

    const isLocked = button.dataset.locked === 'true'
        || button.classList.contains('disabled')
        || button.getAttribute('aria-disabled') === 'true';

    setNextButtonState(!isLocked);
};

const setLessonCompletionUI = (completed, sourceButton) => {
    const statusEl = document.querySelector('[data-lesson-status]');

    if (sourceButton) {
        const card = sourceButton.closest('.lesson-card');
        if (card) {
            card.classList.toggle('lesson-card--completed', completed);
        }

        const isHeroButton = sourceButton.classList.contains('btn-lg');
        if (isHeroButton) {
            sourceButton.classList.toggle('btn-success', completed);
            sourceButton.classList.toggle('btn-light', !completed);
            sourceButton.classList.toggle('text-primary', !completed);
            sourceButton.innerHTML = completed
                ? '<i class="fa-solid fa-check me-2"></i>Bifat deja'
                : '<i class="fa-regular fa-circle-check me-2"></i>Marchează reușita';
        } else {
            sourceButton.classList.toggle('btn-success', completed);
            sourceButton.classList.toggle('btn-outline-success', !completed);
            sourceButton.innerHTML = completed
                ? '<i class="fa-solid fa-check me-1"></i>Finalizată'
                : '<i class="fa-regular fa-circle-check me-1"></i>Marchează finalizarea';
        }
    } else {
        document.querySelectorAll('.lesson-card').forEach((card) => {
            card.classList.toggle('lesson-card--completed', completed);
        });
        document.querySelectorAll('.toggle-completion').forEach((button) => {
            setLessonCompletionUI(completed, button);
        });
    }

    if (statusEl) {
        statusEl.textContent = completed ? 'Finalizată' : 'În curs';
        statusEl.classList.toggle('text-success', completed);
    }
    setNextButtonState(completed);
};

const wireToggleCompletion = () => {
    document.querySelectorAll('.toggle-completion').forEach((button) => {
        button.addEventListener('click', async () => {
            const url = button.dataset.completeHref;
            if (!url) {
                return;
            }

            button.disabled = true;
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });

                if (!response.ok) {
                    throw new Error(`Server responded with ${response.status}`);
                }

                const data = await response.json();
                setLessonCompletionUI(Boolean(data.completed), button);
                updateProgressDisplays({
                    percent: data.progress_percent,
                    completed: data.completed_count,
                    total: data.total_lessons,
                });
            } catch (error) {
                console.error('Failed to toggle lesson completion', error);
                alert('Nu am putut actualiza starea lecției. Încearcă din nou.');
            } finally {
                button.disabled = false;
            }
        });
    });
};

const wireQuizForms = () => {
    document.querySelectorAll('.quiz-card').forEach((card) => {
        const form = card.querySelector('form');
        if (!form) {
            return;
        }

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const submitUrl = card.dataset.submitHref;
            const feedbackEl = card.querySelector('.quiz-feedback');
            const explanationEl = card.querySelector('.quiz-explanation');

            if (!submitUrl) {
                return;
            }

            const formData = new FormData(form);
            const answer = formData.get('answer');
            if (!answer) {
                if (feedbackEl) {
                    feedbackEl.textContent = 'Selectează un răspuns înainte de a trimite.';
                        feedbackEl.textContent = 'Selectează un răspuns înainte de a trimite.';
                    feedbackEl.classList.add('text-danger');
                }
                return;
            }

            feedbackEl?.classList.remove('text-success', 'text-danger');
            feedbackEl.textContent = 'Se verifică răspunsul...';
                feedbackEl.textContent = 'Se verifică răspunsul...';

            try {
                const response = await fetch(submitUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: new URLSearchParams({ answer }),
                });

                if (!response.ok) {
                    throw new Error(`Server responded with ${response.status}`);
                }

                const data = await response.json();
                const correct = Boolean(data.is_correct);

                feedbackEl.textContent = correct ? 'Excelent! Acesta este răspunsul corect.' : 'Răspuns greșit. Încearcă din nou!';
                    feedbackEl.textContent = correct ? 'Excelent! Acesta este răspunsul corect.' : 'Răspuns greșit. Încearcă din nou!';
                feedbackEl.classList.toggle('text-success', correct);
                feedbackEl.classList.toggle('text-danger', !correct);

                card.classList.toggle('quiz-card--success', correct);
                card.classList.toggle('quiz-card--error', !correct);

                if (explanationEl) {
                    explanationEl.classList.toggle('d-none', !correct);
                }

                if (correct && data.lesson_completed) {
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
                feedbackEl.textContent = 'A apărut o eroare. Încearcă din nou.';
                    feedbackEl.textContent = 'A apărut o eroare. Încearcă din nou.';
                feedbackEl.classList.add('text-danger');
            }
        });
    });
};

const wireFormsetAddButtons = () => {
    document.querySelectorAll('[data-add-form]').forEach((button) => {
        button.addEventListener('click', () => {
            const prefix = button.dataset.addForm;
            const container = document.querySelector(`[data-formset-container="${prefix}"]`);
            const templateHolder = document.querySelector(`[data-empty-form="${prefix}"]`);

            if (!container || !templateHolder) {
                return;
            }

            const totalFormsInput = container.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
            if (!totalFormsInput) {
                return;
            }

            const formIndex = parseInt(totalFormsInput.value, 10) || 0;
            const templateHTML = templateHolder.innerHTML.replace(/__prefix__/g, String(formIndex));

            const wrapper = document.createElement('div');
            wrapper.innerHTML = templateHTML.trim();
            const newForm = wrapper.firstElementChild;

            if (!newForm) {
                return;
            }

            newForm.querySelectorAll('input, textarea, select').forEach((input) => {
                if (input.type === 'hidden' && !input.name.endsWith('-DELETE')) {
                    return;
                }
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });

            totalFormsInput.value = String(formIndex + 1);
            container.appendChild(newForm);
        });
    });
};

const wirePracticeDragDrop = () => {
    document.querySelectorAll('[data-practice-station]').forEach((station) => {
        const source = station.querySelector('[data-practice-source]');
        const dropzones = Array.from(station.querySelectorAll('.practice-dropzone'));
        const resetButton = station.querySelector('.practice-reset');
        const successAlert = station.querySelector('.practice-success');
        const feedback = station.querySelector('.practice-feedback');

        if (!source || dropzones.length === 0) {
            return;
        }

        const initialItems = Array.from(source.querySelectorAll('.practice-chip')).map((chip) => ({
            match: chip.dataset.match,
            label: chip.textContent.trim(),
        }));

        let draggedChip = null;

        const showFeedback = (message) => {
            if (!feedback) {
                return;
            }
            if (!message) {
                feedback.classList.add('d-none');
                feedback.textContent = '';
            } else {
                feedback.textContent = message;
                feedback.classList.remove('d-none');
            }
        };

        const attachChipEvents = (chip) => {
            chip.addEventListener('dragstart', (event) => {
                draggedChip = chip;
                event.dataTransfer.setData('text/plain', chip.dataset.match || '');
                event.dataTransfer.effectAllowed = 'move';
                chip.classList.add('is-dragging');
            });
            chip.addEventListener('dragend', () => {
                chip.classList.remove('is-dragging');
                draggedChip = null;
            });
        };

        const renderSource = () => {
            source.innerHTML = '';
            initialItems.forEach((item) => {
                const chip = document.createElement('div');
                chip.className = 'practice-chip';
                chip.dataset.match = item.match;
                chip.draggable = true;
                chip.innerHTML = `<span>${item.label}</span>`;
                attachChipEvents(chip);
                source.appendChild(chip);
            });
        };

        const clearDropzones = () => {
            dropzones.forEach((zone) => {
                zone.classList.remove('practice-dropzone--filled', 'practice-dropzone--error');
                const slot = zone.querySelector('.practice-dropzone__slot');
                if (slot) {
                    slot.innerHTML = '';
                }
            });
        };

        const checkCompletion = () => {
            const allFilled = dropzones.every((zone) => zone.classList.contains('practice-dropzone--filled'));
            if (allFilled && successAlert) {
                successAlert.classList.remove('d-none');
            }
        };

        dropzones.forEach((zone) => {
            zone.addEventListener('dragover', (event) => {
                event.preventDefault();
                zone.classList.add('practice-dropzone--hover');
            });
            zone.addEventListener('dragleave', () => {
                zone.classList.remove('practice-dropzone--hover');
            });
            zone.addEventListener('drop', (event) => {
                event.preventDefault();
                zone.classList.remove('practice-dropzone--hover');

                if (!draggedChip) {
                    return;
                }

                if (zone.classList.contains('practice-dropzone--filled')) {
                    showFeedback('Această zonă este deja completată. Alege altă pereche.');
                    return;
                }

                const expected = zone.dataset.accept || '';
                const actual = draggedChip.dataset.match || '';

                if (expected && expected !== actual) {
                    zone.classList.add('practice-dropzone--error');
                    showFeedback('Ups! Încă nu este potrivirea corectă. Încearcă din nou.');
                    setTimeout(() => zone.classList.remove('practice-dropzone--error'), 700);
                    return;
                }

                showFeedback('');
                zone.classList.add('practice-dropzone--filled');
                const slot = zone.querySelector('.practice-dropzone__slot');
                if (slot) {
                    const ghost = draggedChip.cloneNode(true);
                    ghost.classList.add('practice-chip--ghost');
                    ghost.removeAttribute('draggable');
                    slot.innerHTML = '';
                    slot.appendChild(ghost);
                }
                draggedChip.remove();
                draggedChip = null;
                if (successAlert) {
                    successAlert.classList.add('d-none');
                }
                checkCompletion();
            });
        });

        const resetPractice = () => {
            renderSource();
            clearDropzones();
            showFeedback('');
            if (successAlert) {
                successAlert.classList.add('d-none');
            }
        };

        if (resetButton) {
            resetButton.addEventListener('click', resetPractice);
        }

        // initialise first view
        Array.from(source.querySelectorAll('.practice-chip')).forEach((chip) => attachChipEvents(chip));
    });
};

const wireConceptCards = () => {
    document.querySelectorAll('.concept-card').forEach((card) => {
        card.addEventListener('click', () => {
            card.classList.toggle('concept-card--active');
        });
    });
};

const wireCodeChallenges = () => {
    document.querySelectorAll('[data-code-challenge]').forEach((challenge) => {
        const textarea = challenge.querySelector('.code-editor');
        const checkBtn = challenge.querySelector('.code-check-btn');
        const resetBtn = challenge.querySelector('.code-reset-btn');
        const feedback = challenge.querySelector('.code-feedback');
        const successAlert = challenge.querySelector('.code-success');
        const expectedRaw = challenge.dataset.expectedKeywords || '';
        const starter = textarea ? textarea.value : '';
        const expectedKeywordGroups = expectedRaw
            .split(',')
            .map((keyword) => keyword
                .split('||')
                .map((option) => option.trim().toLowerCase())
                .filter(Boolean)
            )
            .filter((group) => group.length > 0);

        const showFeedback = (message, isSuccess = false) => {
            if (!feedback) {
                return;
            }
            feedback.textContent = message || '';
            feedback.classList.toggle('text-danger', Boolean(message) && !isSuccess);
            feedback.classList.toggle('text-success', Boolean(message) && isSuccess);
        };

        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                if (!textarea) {
                    return;
                }
                const value = textarea.value.toLowerCase();
                const missing = expectedKeywordGroups.filter((group) => !group.some((keyword) => value.includes(keyword)));

                if (missing.length === 0) {
                    showFeedback('Perfect! Toate elementele cheie sunt prezente.', true);
                    if (successAlert) {
                        successAlert.classList.remove('d-none');
                    }
                } else {
                    const hints = missing.map((group) => group[0]).join(', ');
                    showFeedback(`Mai verifică secțiunea de cod. Lipsesc expresii precum: ${hints}`);
                    if (successAlert) {
                        successAlert.classList.add('d-none');
                    }
                }
            });
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (textarea) {
                    textarea.value = starter;
                }
                showFeedback('');
                if (successAlert) {
                    successAlert.classList.add('d-none');
                }
            });
        }
    });
};

const wireVoiceButtons = () => {
    const buttons = document.querySelectorAll('[data-voice-button]');
    if (buttons.length === 0) {
        return;
    }

    const supportsSpeech = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
    if (!supportsSpeech) {
        buttons.forEach((button) => {
            button.addEventListener('click', () => {
                alert('Redarea audio nu este suportată de acest browser.');
            });
        });
        return;
    }

    const synth = window.speechSynthesis;
    const preferredVendors = ['Google', 'Microsoft', 'Amazon', 'Acapela'];
    let availableVoices = [];
    let activeButton = null;

    const refreshVoices = () => {
        availableVoices = synth.getVoices().filter((voice) => voice && voice.lang);
        buttons.forEach((button) => button.classList.remove('is-loading-voice'));
    };

    refreshVoices();
    if (typeof synth.addEventListener === 'function') {
        synth.addEventListener('voiceschanged', refreshVoices);
    } else if (typeof synth.onvoiceschanged !== 'undefined') {
        synth.onvoiceschanged = refreshVoices;
    }

    const normalise = (lang) => (lang || '').toLowerCase();

    const chooseVoice = (button) => {
        if (!availableVoices.length) {
            return null;
        }
        const requested = normalise(button.dataset.voiceLang || 'ro-RO');
        const alternative = normalise(button.dataset.voiceAltLang || '');
        const preferredNames = splitList(button.dataset.voiceNames);
        const candidates = [requested, requested.split('-')[0], alternative, 'ro-ro', 'ro'];

        const findMatches = (lang) => availableVoices.filter((voice) => normalise(voice.lang) === lang);
        const findStartsWith = (lang) => availableVoices.filter((voice) => normalise(voice.lang).startsWith(lang));
        const prefer = (voices) => {
            if (!voices.length) {
                return null;
            }
            const vendorHit = voices.find((voice) => preferredVendors.some((vendor) => (voice.name || '').includes(vendor)));
            if (vendorHit) {
                return vendorHit;
            }
            const romanianName = voices.find((voice) => /ro|romanian/i.test(voice.name || ''));
            if (romanianName) {
                return romanianName;
            }
            return voices[0];
        };

        if (preferredNames.length) {
            const matchPreferred = availableVoices.find((voice) => preferredNames.some((name) => (voice.name || '').toLowerCase().includes(name)));
            if (matchPreferred) {
                return matchPreferred;
            }
        }

        for (const candidate of candidates) {
            if (!candidate) {
                continue;
            }
            const matchesExact = findMatches(candidate);
            if (matchesExact.length) {
                const voice = prefer(matchesExact);
                if (voice) {
                    return voice;
                }
            }
            const matchesStart = findStartsWith(candidate);
            if (matchesStart.length) {
                const voice = prefer(matchesStart);
                if (voice) {
                    return voice;
                }
            }
        }
        return prefer(availableVoices);
    };

    const resetState = () => {
        if (activeButton) {
            activeButton.classList.remove('is-speaking');
            activeButton.removeAttribute('aria-pressed');
        }
        activeButton = null;
    };

    const stopSpeaking = () => {
        if (synth.speaking || synth.pending) {
            synth.cancel();
        }
    };

    const startSpeech = (button) => {
        const rawText = button.dataset.voiceText || '';
        const textContent = rawText.trim();
        if (!textContent) {
            alert('Nu există conținut de redat pentru această explicație.');
            return;
        }

        const utterance = new SpeechSynthesisUtterance(textContent);
        const preferredLang = normalise(button.dataset.voiceLang || 'ro-RO');
        utterance.lang = preferredLang || 'ro-RO';
        const rate = Number.parseFloat(button.dataset.voiceRate || '0.95');
        utterance.rate = Number.isFinite(rate) ? rate : 0.95;
        const pitch = Number.parseFloat(button.dataset.voicePitch || '1');
        utterance.pitch = Number.isFinite(pitch) ? pitch : 1;

        const voice = chooseVoice(button);
        if (voice) {
            utterance.voice = voice;
            utterance.lang = voice.lang || utterance.lang;
        }

        utterance.onend = resetState;
        utterance.onerror = (event) => {
            console.error('Speech synthesis error', event);
            resetState();
            alert('Nu am putut porni redarea audio. Încearcă din nou sau schimbă browserul.');
        };

        activeButton = button;
        button.classList.add('is-speaking');
        button.setAttribute('aria-pressed', 'true');
        synth.speak(utterance);
    };

    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            if (!availableVoices.length) {
                button.classList.add('is-loading-voice');
                refreshVoices();
            }
            if (activeButton === button) {
                stopSpeaking();
                resetState();
                return;
            }
            stopSpeaking();
            resetState();
            startSpeech(button);
        });
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopSpeaking();
            resetState();
        }
    });
};


const wireLessonExperience = () => {
    document.querySelectorAll('[data-lesson-experience]').forEach((root) => {
        const startButton = root.querySelector('[data-lesson-start]');
        const intro = root.querySelector('[data-lesson-intro]');
        const panel = root.querySelector('[data-lesson-panel]');
        const panelFront = root.querySelector('[data-panel-front]');
        const panelSteps = root.querySelector('[data-panel-steps]');
        const scope = panelSteps || root;
        const summary = panelSteps?.querySelector('[data-lesson-summary]') || root.querySelector('[data-lesson-summary]');
        const body = panelSteps?.querySelector('[data-lesson-body]') || root.querySelector('[data-lesson-body]');
        const flow = scope.querySelector('[data-lesson-flow]');
        const steps = Array.from(scope.querySelectorAll('[data-lesson-step]'));
        const nextBtn = root.querySelector('[data-step-next]');
        const prevBtn = root.querySelector('[data-step-prev]');
        const indicatorCurrent = root.querySelector('[data-step-current]');
        const indicatorTotal = root.querySelector('[data-step-total]');
        const indicatorTitle = root.querySelector('[data-step-title]');
        const lockHint = root.querySelector('[data-step-lock-hint]');
        const starSlots = Array.from(root.querySelectorAll('[data-star-slot]'));
        const starsScore = root.querySelector('[data-stars-score]');
        const teamModeButtons = Array.from(root.querySelectorAll('[data-team-mode-btn]'));
        const teamProgress = root.querySelector('[data-team-progress]');
        const teamProgressFill = root.querySelector('[data-team-progress-fill]');
        const teamProgressLabel = root.querySelector('[data-team-progress-label]');
        const rewardNode = root.querySelector('[data-step-reward]');
        const secretBonusNode = root.querySelector('[data-secret-bonus]');
        const mascotNode = root.querySelector('[data-mascot-feedback]');
        const mascotMessage = root.querySelector('[data-mascot-message]');

        let currentStep = 0;
        const totalSteps = steps.length;
        const requirementState = new Map();
        const requirementStats = new Map();
        const stepScores = new Map();
        const completedSteps = new Set();
        const defaultLockMessage = 'Finalizează această etapă înainte să continui.';
        const interactiveRequirements = new Set([
            'hardware-map',
            'hardware-software-match',
        ]);
        const defaultStepRewards = [
            'Sticker nou: Constructor hardware',
            'Sticker nou: Navigator web',
            'Sticker nou: Scut digital',
            'Insignă: Modul finalizat',
        ];
        let stepStartedAt = Date.now();
        let teamMode = 'solo';
        let interactiveSuccessStreak = 0;
        let secretBonusAwarded = false;
        let rewardTimeoutId = null;
        let mascotTimeoutId = null;

        steps.forEach((step) => {
            const requirement = (step.dataset.stepRequires || '').trim();
            if (requirement && !requirementState.has(requirement)) {
                requirementState.set(requirement, false);
                requirementStats.set(requirement, {
                    resets: 0,
                    failures: 0,
                    successes: 0,
                });
            }
        });

        if (indicatorTotal) {
            indicatorTotal.textContent = totalSteps;
        }

        const setLockHint = (message = '') => {
            if (!lockHint) {
                return;
            }
            const text = (message || '').trim();
            if (!text) {
                lockHint.textContent = '';
                lockHint.setAttribute('hidden', '');
                return;
            }
            lockHint.textContent = text;
            lockHint.removeAttribute('hidden');
        };

        const getStepRequirement = (index = currentStep) => (steps[index]?.dataset.stepRequires || '').trim();

        const isStepComplete = (index = currentStep) => {
            const requirement = getStepRequirement(index);
            if (!requirement) {
                return true;
            }
            return Boolean(requirementState.get(requirement));
        };

        const showStepReward = (message, type = 'default') => {
            if (!rewardNode || !message) {
                return;
            }
            rewardNode.textContent = message;
            rewardNode.removeAttribute('hidden');
            rewardNode.classList.remove('is-success', 'is-bonus');
            if (type === 'success') {
                rewardNode.classList.add('is-success');
            }
            if (type === 'bonus') {
                rewardNode.classList.add('is-bonus');
            }
            rewardNode.classList.add('is-visible');
            if (rewardTimeoutId) {
                window.clearTimeout(rewardTimeoutId);
            }
            rewardTimeoutId = window.setTimeout(() => {
                rewardNode.classList.remove('is-visible', 'is-success', 'is-bonus');
                rewardNode.setAttribute('hidden', '');
            }, 2200);
        };

        const showMascot = (message, tone = 'success') => {
            if (!mascotNode || !mascotMessage || !message) {
                return;
            }
            mascotMessage.textContent = message;
            mascotNode.removeAttribute('hidden');
            mascotNode.classList.remove('is-success', 'is-warning');
            mascotNode.classList.add(tone === 'warning' ? 'is-warning' : 'is-success');
            mascotNode.classList.add('is-visible');
            if (mascotTimeoutId) {
                window.clearTimeout(mascotTimeoutId);
            }
            mascotTimeoutId = window.setTimeout(() => {
                mascotNode.classList.remove('is-visible');
                mascotNode.setAttribute('hidden', '');
            }, 1800);
        };

        const showSecretBonus = () => {
            if (!secretBonusNode || secretBonusAwarded) {
                return;
            }
            secretBonusAwarded = true;
            secretBonusNode.removeAttribute('hidden');
            secretBonusNode.classList.add('is-visible');
            showStepReward('Bonus secret de consistență activat!', 'bonus');
            showMascot('Bonus secret deblocat! Echipa ta merge perfect.', 'success');
        };

        const updateStarsUI = (score = 0) => {
            starSlots.forEach((slot, index) => {
                slot.classList.toggle('is-earned', index < score);
            });
            if (starsScore) {
                starsScore.textContent = `${score}/3`;
            }
        };

        const updateStarScoreForStep = (index = currentStep) => {
            const score = stepScores.get(index)?.total || 0;
            updateStarsUI(score);
        };

        const updateTeamModeUI = () => {
            teamModeButtons.forEach((button) => {
                const active = button.dataset.teamModeValue === teamMode;
                button.classList.toggle('is-active', active);
                button.classList.toggle('btn-primary', active);
                button.classList.toggle('btn-outline-primary', !active);
            });
            if (teamProgress) {
                if (teamMode === 'pair') {
                    teamProgress.removeAttribute('hidden');
                } else {
                    teamProgress.setAttribute('hidden', '');
                }
            }
        };

        const updateTeamProgress = () => {
            const completed = completedSteps.size;
            const percent = totalSteps ? Math.round((completed / totalSteps) * 100) : 0;
            if (teamProgressFill) {
                teamProgressFill.style.width = `${percent}%`;
            }
            if (teamProgressLabel) {
                teamProgressLabel.textContent = `Echipă: ${completed}/${totalSteps} pași`;
            }
        };

        const evaluateStepScore = (index) => {
            const stepNode = steps[index];
            const requirement = (stepNode?.dataset.stepRequires || '').trim();
            const elapsedMs = Math.max(0, Date.now() - stepStartedAt);
            const defaultTarget = requirement ? 180 : 110;
            const speedTarget = Number.parseInt(
                stepNode?.dataset.stepSpeedTarget || String(defaultTarget),
                10
            );
            const speed = elapsedMs <= (Number.isFinite(speedTarget) ? speedTarget : defaultTarget) * 1000;
            const accuracy = requirement ? Boolean(requirementState.get(requirement)) : true;
            const stats = requirement
                ? requirementStats.get(requirement) || { resets: 0, failures: 0, successes: 0 }
                : { resets: 0, failures: 0, successes: 0 };
            const noHints = requirement ? stats.resets === 0 && stats.failures === 0 : true;
            const total = [accuracy, speed, noHints].filter(Boolean).length;
            return {
                accuracy,
                speed,
                noHints,
                total,
            };
        };

        const completeStep = (index) => {
            if (completedSteps.has(index)) {
                return;
            }
            const score = evaluateStepScore(index);
            stepScores.set(index, score);
            completedSteps.add(index);
            updateStarScoreForStep(index);
            updateTeamProgress();

            const rewardLabel = steps[index]?.dataset.stepReward || defaultStepRewards[index] || 'Sticker nou';
            showStepReward(`${rewardLabel} • ${score.total}/3 stele`, 'success');
        };

        const refreshNextButton = () => {
            if (!nextBtn || !steps.length) {
                return;
            }
            const stepNode = steps[currentStep];
            const isLast = currentStep === totalSteps - 1;
            const customLabel = stepNode?.dataset.stepButton;
            nextBtn.textContent = customLabel || (isLast ? 'Finalizează lecția' : 'Continuă');
            nextBtn.classList.toggle('btn-success', isLast);

            if (isLast) {
                nextBtn.disabled = false;
                setLockHint('');
                return;
            }

            const complete = isStepComplete(currentStep);
            nextBtn.disabled = !complete;
            if (complete) {
                setLockHint('');
                return;
            }
            setLockHint(stepNode?.dataset.stepLockedMessage || defaultLockMessage);
        };

        const goToStep = (index) => {
            if (!steps.length) {
                return;
            }
            currentStep = Math.max(0, Math.min(index, totalSteps - 1));
            stepStartedAt = Date.now();
            steps.forEach((step, stepIndex) => {
                if (stepIndex === currentStep) {
                    step.removeAttribute('hidden');
                    step.classList.add('lesson-step--active');
                } else {
                    step.setAttribute('hidden', '');
                    step.classList.remove('lesson-step--active');
                }
            });
            if (indicatorCurrent) {
                indicatorCurrent.textContent = currentStep + 1;
            }
            if (indicatorTitle) {
                const title = steps[currentStep]?.dataset.stepTitle || `Pasul ${currentStep + 1}`;
                indicatorTitle.textContent = title;
            }
            if (prevBtn) {
                prevBtn.hidden = currentStep === 0;
                prevBtn.disabled = currentStep === 0;
            }
            updateStarScoreForStep(currentStep);
            updateTeamProgress();
            refreshNextButton();
        };

        teamModeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const nextMode = button.dataset.teamModeValue === 'pair' ? 'pair' : 'solo';
                teamMode = nextMode;
                updateTeamModeUI();
                updateTeamProgress();
            });
        });

        root.addEventListener('lesson:step-requirement', (event) => {
            const detail = event.detail || {};
            const requirement =
                typeof detail.requirement === 'string' ? detail.requirement.trim() : '';
            if (!requirement || !requirementState.has(requirement)) {
                return;
            }
            const complete = Boolean(detail.complete);
            const wasComplete = Boolean(requirementState.get(requirement));
            requirementState.set(requirement, complete);

            const stats = requirementStats.get(requirement) || {
                resets: 0,
                failures: 0,
                successes: 0,
            };
            if (detail.result === 'reset') {
                stats.resets += 1;
            }
            if (detail.result === 'failed') {
                stats.failures += 1;
            }
            if (detail.result === 'success') {
                stats.successes += 1;
            }
            requirementStats.set(requirement, stats);

            if (interactiveRequirements.has(requirement)) {
                if (detail.result === 'success' && !wasComplete) {
                    interactiveSuccessStreak += 1;
                    if (interactiveSuccessStreak >= 2) {
                        showSecretBonus();
                    }
                }
                if (detail.result === 'failed' || detail.result === 'reset') {
                    interactiveSuccessStreak = 0;
                }
            }

            if (getStepRequirement(currentStep) === requirement) {
                refreshNextButton();
            }
        });

        root.addEventListener('lesson:mascot-feedback', (event) => {
            const detail = event.detail || {};
            const message = (detail.message || '').toString().trim();
            const tone = detail.tone === 'warning' ? 'warning' : 'success';
            if (message) {
                showMascot(message, tone);
            }
        });

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (!isStepComplete(currentStep) && currentStep !== totalSteps - 1) {
                    setLockHint(
                        steps[currentStep]?.dataset.stepLockedMessage || defaultLockMessage
                    );
                    showMascot('Mai întâi termină provocarea acestui pas.', 'warning');
                    return;
                }
                completeStep(currentStep);
                if (currentStep === totalSteps - 1) {
                    nextBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i>Lecția finalizată';
                    nextBtn.disabled = true;
                    setLockHint('');
                    root.classList.add('lesson-experience--completed');
                    showMascot('Lecție finalizată. Excelent!', 'success');
                    return;
                }
                goToStep(currentStep + 1);
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                goToStep(currentStep - 1);
                refreshNextButton();
            });
        }

        const activateLesson = () => {
            root.classList.add('lesson-experience--started');
            if (intro) {
                if (intro.hasAttribute('data-keep-visible')) {
                    intro.classList.add('lesson-gate__intro--collapsed');
                    intro.removeAttribute('hidden');
                    intro.removeAttribute('aria-hidden');
                } else {
                    intro.setAttribute('hidden', '');
                    intro.setAttribute('aria-hidden', 'true');
                }
            }
            if (panel) {
                panel.classList.add('lesson-gate__panel--expanded');
            }
            if (panelFront) {
                panelFront.setAttribute('hidden', '');
                panelFront.setAttribute('aria-hidden', 'true');
            }
            if (panelSteps) {
                panelSteps.removeAttribute('hidden');
                panelSteps.removeAttribute('aria-hidden');
            }
            if (summary) {
                summary.removeAttribute('hidden');
                summary.removeAttribute('aria-hidden');
            }
            if (body) {
                body.removeAttribute('hidden');
            }
            if (flow) {
                flow.removeAttribute('hidden');
            }
            if (startButton) {
                startButton.setAttribute('hidden', '');
                startButton.setAttribute('aria-hidden', 'true');
                startButton.setAttribute('disabled', 'disabled');
            }
            updateTeamModeUI();
            updateTeamProgress();
            updateStarScoreForStep(0);
            goToStep(0);
            const focusTarget = flow?.querySelector('.lesson-step--active') || panelSteps?.querySelector('.lesson-step--active');
            if (focusTarget && typeof focusTarget.focus === 'function') {
                focusTarget.setAttribute('tabindex', '-1');
                window.requestAnimationFrame(() => {
                    focusTarget.focus({ preventScroll: true });
                    focusTarget.scrollIntoView({ behavior: 'smooth', block: 'start' });
                });
            }
        };

        if (root.classList.contains('lesson-experience--started')) {
            activateLesson();
            return;
        }

        if (startButton) {
            startButton.addEventListener('click', activateLesson);
        }
    });
};

const wireHardwareMapGame = () => {
    document.querySelectorAll('[data-hardware-map]').forEach((root) => {
        const bank = root.querySelector('[data-bank]');
        const slots = Array.from(root.querySelectorAll('[data-slot]'));
        const pieces = Array.from(root.querySelectorAll('[data-piece]'));
        const feedback = root.querySelector('[data-hardware-feedback]');
        const checkBtn = root.querySelector('[data-hardware-check]');
        const resetBtn = root.querySelector('[data-hardware-reset]');
        const dropzones = Array.from(root.querySelectorAll('[data-dropzone]'));
        const requirement = (root.dataset.stepRequirement || 'hardware-map').trim();
        const lessonExperience = root.closest('[data-lesson-experience]');

        const notifyRequirement = (complete, extra = {}) => {
            if (!lessonExperience || !requirement) {
                return;
            }
            lessonExperience.dispatchEvent(
                new CustomEvent('lesson:step-requirement', {
                    detail: Object.assign({
                        requirement,
                        complete: Boolean(complete),
                    }, extra),
                })
            );
        };

        const notifyMascot = (message, tone = 'success') => {
            if (!lessonExperience || !message) {
                return;
            }
            lessonExperience.dispatchEvent(
                new CustomEvent('lesson:mascot-feedback', {
                    detail: {
                        message,
                        tone,
                    },
                })
            );
        };

        const updateSlotState = () => {
            slots.forEach((slot) => {
                slot.classList.toggle('hardware-slot--filled', Boolean(slot.querySelector('[data-piece]')));
            });
        };

        const clearFeedback = () => {
            if (!feedback) {
                return;
            }
            feedback.textContent = '';
            feedback.className = 'hardware-feedback';
        };

        const placePiece = (piece, target) => {
            if (target.dataset.bank !== undefined) {
                bank.appendChild(piece);
                piece.dataset.placed = '';
            } else if (target.dataset.slot) {
                const existing = target.querySelector('[data-piece]');
                if (existing) {
                    bank.appendChild(existing);
                    existing.dataset.placed = '';
                }
                target.appendChild(piece);
                piece.dataset.placed = target.dataset.slot;
            }
            updateSlotState();
            clearFeedback();
        };

        const removeZoneHighlight = () => {
            dropzones.forEach((zone) => zone.classList.remove('hardware-zone--active'));
        };

        pieces.forEach((piece) => {
            piece.addEventListener('dragstart', (event) => {
                event.dataTransfer.setData('text/plain', piece.dataset.piece);
                event.dataTransfer.effectAllowed = 'move';
                piece.classList.add('is-dragging');
            });
            piece.addEventListener('dragend', () => {
                piece.classList.remove('is-dragging');
                removeZoneHighlight();
            });
        });

        dropzones.forEach((zone) => {
            zone.addEventListener('dragover', (event) => {
                event.preventDefault();
                zone.classList.add('hardware-zone--active');
            });
            zone.addEventListener('dragleave', () => zone.classList.remove('hardware-zone--active'));
            zone.addEventListener('drop', (event) => {
                event.preventDefault();
                const key = event.dataTransfer.getData('text/plain');
                const piece = root.querySelector(`[data-piece="${key}"]`);
                const target = event.target.closest('[data-slot], [data-bank]');
                if (!piece || !target) {
                    return;
                }
                placePiece(piece, target);
                removeZoneHighlight();
            });
        });

        const resetBoard = () => {
            pieces.forEach((piece) => {
                bank.appendChild(piece);
                piece.dataset.placed = '';
            });
            slots.forEach((slot) => {
                slot.classList.remove('hardware-slot--correct', 'hardware-slot--incorrect');
            });
            removeZoneHighlight();
            clearFeedback();
            updateSlotState();
            notifyRequirement(false, { result: 'reset' });
        };

        resetBoard();

        if (resetBtn) {
            resetBtn.addEventListener('click', resetBoard);
        }

        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                if (!feedback) {
                    return;
                }
                let placedCount = 0;
                let correctCount = 0;

                slots.forEach((slot) => {
                    const piece = slot.querySelector('[data-piece]');
                    slot.classList.remove('hardware-slot--correct', 'hardware-slot--incorrect');
                    if (!piece) {
                        return;
                    }
                    placedCount += 1;
                    if (piece.dataset.answer === slot.dataset.slot) {
                        slot.classList.add('hardware-slot--correct');
                        correctCount += 1;
                    } else {
                        slot.classList.add('hardware-slot--incorrect');
                    }
                });

                feedback.className = 'hardware-feedback';
                if (placedCount !== slots.length) {
                    feedback.classList.add('hardware-feedback--warning');
                    feedback.textContent = 'Mai ai componente de plasat. Completează toate zonele și verifică din nou.';
                    notifyRequirement(false, { result: 'failed' });
                    notifyMascot('Completează toate zonele înainte de verificare.', 'warning');
                } else if (correctCount === slots.length) {
                    feedback.classList.add('hardware-feedback--success');
                    feedback.textContent = 'Super! Toate componentele sunt pe locul potrivit.';
                    notifyRequirement(true, { result: 'success' });
                    notifyMascot('Bravo! Ai asamblat corect toate componentele.', 'success');
                } else {
                    feedback.classList.add('hardware-feedback--error');
                    feedback.textContent = 'Unele componente nu se potrivesc zonei. Compară denumirile și încearcă din nou.';
                    notifyRequirement(false, { result: 'failed' });
                    notifyMascot('Ești aproape. Mai verifică o dată potrivirile.', 'warning');
                }
            });
        }
    });
};

const wireHardwareSoftwareMatch = () => {
    document.querySelectorAll('[data-hardware-software]').forEach((root) => {
        const feedback = root.querySelector('[data-match-feedback]');
        const checkBtn = root.querySelector('[data-match-check]');
        const resetBtn = root.querySelector('[data-match-reset]');
        const banks = Array.from(root.querySelectorAll('[data-bank]'));
        const slots = Array.from(root.querySelectorAll('[data-match-slot]'));
        const tokens = Array.from(root.querySelectorAll('[data-match-token]'));
        const dropzones = Array.from(root.querySelectorAll('[data-dropzone]'));
        const tasks = Array.from(root.querySelectorAll('[data-scenario]'));
        const requirement = (root.dataset.stepRequirement || 'hardware-software-match').trim();
        const lessonExperience = root.closest('[data-lesson-experience]');

        const notifyRequirement = (complete, extra = {}) => {
            if (!lessonExperience || !requirement) {
                return;
            }
            lessonExperience.dispatchEvent(
                new CustomEvent('lesson:step-requirement', {
                    detail: Object.assign({
                        requirement,
                        complete: Boolean(complete),
                    }, extra),
                })
            );
        };

        const notifyMascot = (message, tone = 'success') => {
            if (!lessonExperience || !message) {
                return;
            }
            lessonExperience.dispatchEvent(
                new CustomEvent('lesson:mascot-feedback', {
                    detail: {
                        message,
                        tone,
                    },
                })
            );
        };

        const banksByType = {};
        banks.forEach((bank) => {
            banksByType[bank.dataset.bank] = bank;
        });

        tokens.forEach((token) => {
            token.dataset.home = token.closest('[data-bank]')?.dataset.bank || '';
        });

        const clearFeedback = () => {
            if (!feedback) {
                return;
            }
            feedback.textContent = '';
            feedback.className = 'module-match__feedback';
        };

        const updateSlotState = () => {
            slots.forEach((slot) => {
                slot.classList.toggle('match-slot--filled', Boolean(slot.querySelector('[data-match-token]')));
            });
        };

        const moveTokenToBank = (token, preferredBank) => {
            const bank = banksByType[preferredBank] || banksByType[token.dataset.tokenType] || banksByType[token.dataset.home];
            if (bank) {
                bank.appendChild(token);
            }
            token.dataset.placed = '';
        };

        const placeToken = (token, target) => {
            if (target.dataset.bank !== undefined) {
                const bankName = target.dataset.bank;
                const finalBank = bankName === token.dataset.tokenType ? bankName : token.dataset.tokenType;
                moveTokenToBank(token, finalBank);
                updateSlotState();
                clearFeedback();
                return true;
            }

            if (!target.dataset.match) {
                return false;
            }

            const expectedType = target.dataset.accept;
            if (expectedType && token.dataset.tokenType !== expectedType) {
                if (feedback) {
                    feedback.className = 'module-match__feedback module-match__feedback--warning';
                    feedback.textContent = 'Acest cartonaș se potrivește în cealaltă coloană. Încearcă din nou.';
                }
                target.classList.add('match-slot--error');
                setTimeout(() => target.classList.remove('match-slot--error'), 600);
                return false;
            }

            const existing = target.querySelector('[data-match-token]');
            if (existing) {
                moveTokenToBank(existing, existing.dataset.home);
            }

            target.appendChild(token);
            token.dataset.placed = target.dataset.match;
            updateSlotState();
            clearFeedback();
            return true;
        };

        const removeActiveHighlight = () => {
            dropzones.forEach((zone) => zone.classList.remove('match-dropzone--active'));
        };

        tokens.forEach((token) => {
            token.addEventListener('dragstart', (event) => {
                event.dataTransfer.setData('text/plain', token.dataset.tokenValue);
                event.dataTransfer.effectAllowed = 'move';
                token.classList.add('match-token--dragging');
            });
            token.addEventListener('dragend', () => {
                token.classList.remove('match-token--dragging');
                removeActiveHighlight();
            });
        });

        dropzones.forEach((zone) => {
            zone.addEventListener('dragover', (event) => {
                event.preventDefault();
                zone.classList.add('match-dropzone--active');
            });
            zone.addEventListener('dragleave', () => {
                zone.classList.remove('match-dropzone--active');
            });
            zone.addEventListener('drop', (event) => {
                event.preventDefault();
                const tokenValue = event.dataTransfer.getData('text/plain');
                const token = root.querySelector(`[data-match-token][data-token-value="${tokenValue}"]`);
                const target = event.target.closest('[data-match-slot], [data-bank]');
                if (!token || !target) {
                    return;
                }
                placeToken(token, target);
                removeActiveHighlight();
            });
        });

        const resetBoard = () => {
            tokens.forEach((token) => {
                moveTokenToBank(token, token.dataset.home);
            });
            tasks.forEach((row) => {
                row.classList.remove('module-match__row--correct', 'module-match__row--incorrect', 'module-match__row--incomplete');
            });
            updateSlotState();
            clearFeedback();
            notifyRequirement(false, { result: 'reset' });
        };

        if (resetBtn) {
            resetBtn.addEventListener('click', resetBoard);
        }

        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                let allFilled = true;
                let allCorrect = true;

                tasks.forEach((row) => {
                    row.classList.remove('module-match__row--correct', 'module-match__row--incorrect', 'module-match__row--incomplete');

                    const hardwareSlot = row.querySelector('[data-match-slot][data-accept="hardware"]');
                    const softwareSlot = row.querySelector('[data-match-slot][data-accept="software"]');
                    const hardwareToken = hardwareSlot?.querySelector('[data-match-token]');
                    const softwareToken = softwareSlot?.querySelector('[data-match-token]');

                    if (!hardwareToken || !softwareToken) {
                        allFilled = false;
                        row.classList.add('module-match__row--incomplete');
                        return;
                    }

                    const hardwareCorrect = hardwareToken.dataset.tokenValue === hardwareSlot.dataset.match;
                    const softwareCorrect = softwareToken.dataset.tokenValue === softwareSlot.dataset.match;

                    if (hardwareCorrect && softwareCorrect) {
                        row.classList.add('module-match__row--correct');
                    } else {
                        allCorrect = false;
                        row.classList.add('module-match__row--incorrect');
                    }
                });

                if (!feedback) {
                    return;
                }

                feedback.className = 'module-match__feedback';
                if (!allFilled) {
                    feedback.classList.add('module-match__feedback--warning');
                    feedback.textContent = 'Completează fiecare sarcină cu câte două cartonașe înainte de verificare.';
                    notifyRequirement(false, { result: 'failed' });
                    notifyMascot('Mai ai locuri goale. Completează toate perechile.', 'warning');
                } else if (allCorrect) {
                    feedback.classList.add('module-match__feedback--success');
                    feedback.textContent = 'Excelent! Ai găsit combinațiile hardware + software potrivite.';
                    notifyRequirement(true, { result: 'success' });
                    notifyMascot('Perfect! Toate perechile sunt corecte.', 'success');
                } else {
                    feedback.classList.add('module-match__feedback--error');
                    feedback.textContent = 'Mai verifică una dintre perechi: unele cartonașe nu se potrivesc încă.';
                    notifyRequirement(false, { result: 'failed' });
                    notifyMascot('Bun început. Ajustează perechile marcate cu roșu.', 'warning');
                }
            });
        }

        resetBoard();
    });
};

const applyModuleProgress = (root = document) => {
    root.querySelectorAll('[data-module-slug]').forEach((module) => {
        const completedRaw = module.dataset.moduleCompleted;
        const totalRaw = module.dataset.moduleTotal;
        const completed = Number.parseInt(completedRaw || '', 10);
        const total = Number.parseInt(totalRaw || '', 10);
        const bar = module.querySelector('[data-module-progress-bar]');
        const label = module.querySelector('[data-module-progress-label]');

        if (!Number.isFinite(total) || total <= 0) {
            if (bar) {
                bar.style.width = '0%';
            }
            if (label) {
                label.textContent = 'Progres indisponibil';
            }
            return;
        }

        const safeCompleted = Number.isFinite(completed) ? Math.max(0, completed) : 0;
        const clampedTotal = Math.max(1, total);
        const percent = Math.max(0, Math.min(100, Math.round((safeCompleted / clampedTotal) * 100)));

        if (bar) {
            requestAnimationFrame(() => {
                bar.style.width = `${percent}%`;
            });
        }

        if (label) {
            label.textContent =
                safeCompleted === 1
                    ? `1 din ${clampedTotal} lecții finalizate`
                    : `${safeCompleted} din ${clampedTotal} lecții finalizate`;
        }
    });
};

const setupLessonFilters = (dashboard) => {
    if (!dashboard) {
        return;
    }

    const form = dashboard.querySelector('[data-filter-form]');
    if (!form || form.dataset.enhanced === 'true') {
        return;
    }

    const resetButton = form.querySelector('[data-filter-reset]');
    const storageKey = STORAGE_KEYS.lessonFilters;

    const saveFilters = (formData) => {
        const snapshot = {};
        formData.forEach((value, key) => {
            if (key === 'upcoming') {
                snapshot[key] = '1';
            } else {
                snapshot[key] = value;
            }
        });
        if (!formData.has('upcoming')) {
            snapshot.upcoming = '';
        }
        safeLocalStorage.set(storageKey, JSON.stringify(snapshot));
    };

    const applyStateToForm = (state) => {
        if (!state) {
            return;
        }

        form.querySelectorAll('[name]').forEach((field) => {
            if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement)) {
                return;
            }
            if (field.type === 'checkbox') {
                field.checked = state[field.name] === '1';
            } else if (state[field.name] !== undefined) {
                field.value = state[field.name];
            }
        });
    };

    const getFormData = () => {
        const data = new FormData(form);
        const params = new URLSearchParams();
        data.forEach((value, key) => {
            if (key === 'upcoming') {
                params.set(key, '1');
            } else if (typeof value === 'string' && value.trim() === '') {
                params.delete(key);
            } else {
                params.set(key, value);
            }
        });
        return { formData: data, params };
    };

    const updateHistory = (params) => {
        const url = new URL(window.location.href);
        url.search = params.toString();
        const query = params.toString();
        const newUrl = `${url.pathname}${query ? `?${query}` : ''}`;
        window.history.replaceState({}, '', newUrl);
    };

    const fetchAndUpdateLessons = async (params) => {
        const dashboardRoot = document.querySelector('[data-lessons-dashboard]');
        if (!dashboardRoot) {
            return;
        }

        const url = new URL(window.location.href);
        url.search = params.toString();
        form.classList.add('is-loading');
        try {
            const response = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            if (!response.ok) {
                throw new Error(`Request failed with status ${response.status}`);
            }
            const text = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const newDashboard = doc.querySelector('[data-lessons-dashboard]');
            if (!newDashboard) {
                return;
            }

            const selectors = ['.learning-spotlight', '.learning-program', '[data-filters]'];
            selectors.forEach((selector) => {
                const incoming = newDashboard.querySelector(selector);
                const current = dashboardRoot.querySelector(selector);
                if (incoming && current) {
                    current.replaceWith(incoming);
                }
            });

            initializeLessonsDashboard({ rebindFilters: false });
            setupLessonFilters(document.querySelector('[data-lessons-dashboard]'));
            updateHistory(params);
        } catch (error) {
            console.warn('Lesson filter refresh failed', error);
        } finally {
            form.classList.remove('is-loading');
        }
    };

    const restoreState = () => {
        const urlParams = new URLSearchParams(window.location.search);
        if (Array.from(urlParams.keys()).length) {
            const state = {};
            urlParams.forEach((value, key) => {
                state[key] = value;
            });
            applyStateToForm(state);
            safeLocalStorage.set(storageKey, JSON.stringify(state));
            return;
        }

        const stored = safeLocalStorage.get(storageKey);
        if (!stored) {
            return;
        }
        try {
            const parsed = JSON.parse(stored);
            applyStateToForm(parsed);
        } catch (error) {
            console.warn('Failed to restore lesson filters', error);
        }
    };

    restoreState();

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const { formData, params } = getFormData();
        saveFilters(formData);
        fetchAndUpdateLessons(params);
    });

    form.querySelectorAll('input, select').forEach((field) => {
        field.addEventListener('change', () => {
            const { formData } = getFormData();
            saveFilters(formData);
        });
    });

    if (resetButton) {
        resetButton.addEventListener('click', () => {
            form.reset();
            const { formData, params } = getFormData();
            saveFilters(formData);
            fetchAndUpdateLessons(params);
        });
    }

    form.dataset.enhanced = 'true';
};

const initializeLessonsDashboard = ({ rebindFilters = true } = {}) => {
    const dashboard = document.querySelector('[data-lessons-dashboard]');
    if (!dashboard) {
        document.body.classList.remove('lessons-page');
        return;
    }
    document.body.classList.add('lessons-page');
    applyModuleProgress(dashboard);
    initializeProgressBars();
    if (rebindFilters) {
        setupLessonFilters(dashboard);
    }
};

const initializeWorkspaceMessages = () => {
    document.querySelectorAll('[data-dismiss-message]').forEach((button) => {
        button.addEventListener('click', () => {
            const container = button.closest('[data-message]');
            if (container) {
                container.classList.add('is-dismissed');
                setTimeout(() => container.remove(), 220);
            }
        });
    });
};

const initializeHistoryBackLinks = () => {
    if (document.documentElement.dataset.historyBackReady === 'true') {
        return;
    }
    document.documentElement.dataset.historyBackReady = 'true';

    const resolveInternalReferrer = () => {
        if (!document.referrer) {
            return null;
        }
        try {
            const referrer = new URL(document.referrer, window.location.origin);
            if (referrer.origin !== window.location.origin) {
                return null;
            }
            return `${referrer.pathname}${referrer.search}${referrer.hash}`;
        } catch (error) {
            return null;
        }
    };

    document.addEventListener('click', (event) => {
        const trigger = event.target instanceof Element ? event.target.closest('[data-history-back]') : null;
        if (!trigger) {
            return;
        }
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }

        event.preventDefault();

        const fallbackUrl = trigger.getAttribute('href') || '/';
        const referrerUrl = resolveInternalReferrer();
        const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
        const canUseHistory = window.history.length > 1
            && Boolean(referrerUrl)
            && referrerUrl !== currentUrl;

        if (!canUseHistory) {
            window.location.assign(referrerUrl || fallbackUrl);
            return;
        }

        let didNavigate = false;
        const onPageHide = () => {
            didNavigate = true;
        };
        window.addEventListener('pagehide', onPageHide, { once: true });
        window.history.back();

        window.setTimeout(() => {
            if (didNavigate) {
                return;
            }
            window.location.assign(referrerUrl || fallbackUrl);
        }, 320);
    });
};

const initializeEstudyPage = () => {
    initializeLessonsDashboard();
    initializeProgressBars();
    initializeNextButtonState();
    wireLessonExperience();
    wireToggleCompletion();
    wireQuizForms();
    wireFormsetAddButtons();
    wirePracticeDragDrop();
    wireConceptCards();
    wireCodeChallenges();
    wireVoiceButtons();
    wireHardwareMapGame();
    wireHardwareSoftwareMatch();
    initializeWorkspaceMessages();
};

const runEstudyPageForCurrentView = () => {
    const viewKey = `${window.location.pathname}${window.location.search}::${document.body.className}`;
    if (document.documentElement.dataset.estudyPageInitKey === viewKey) {
        return;
    }
    document.documentElement.dataset.estudyPageInitKey = viewKey;
    initializeEstudyPage();
};

const bootstrapEstudy = () => {
    initializeThemeControls();
    initializeHistoryBackLinks();
    runEstudyPageForCurrentView();
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrapEstudy, { once: true });
} else {
    bootstrapEstudy();
}

if (document.documentElement.dataset.estudyPageReadyHook !== 'true') {
    document.documentElement.dataset.estudyPageReadyHook = 'true';
    document.addEventListener('unitex:page-ready', () => {
        runEstudyPageForCurrentView();
    });
}

})();
