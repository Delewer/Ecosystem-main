/* eslint-env browser */

const STORAGE_KEYS = {
    theme: 'unitex-theme',
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
    if (percent === null || percent === undefined) {
        return;
    }

    const roundedPercent = Math.round(percent);

    document.querySelectorAll('[data-progress-bar]').forEach((bar) => {
        bar.style.width = `${roundedPercent}%`;
        bar.setAttribute('aria-valuenow', String(roundedPercent));
        bar.dataset.progressInitial = String(roundedPercent);
        const percentHolder = bar.querySelector('[data-progress-percent]');
        if (percentHolder) {
            percentHolder.textContent = roundedPercent;
        }
    });

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
};

const initializeProgressBars = () => {
    document.querySelectorAll('[data-progress-bar]').forEach((bar) => {
        const initialRaw = bar.dataset.progressInitial;
        if (!initialRaw) {
            return;
        }
        const initialValue = Number.parseFloat(initialRaw);
        if (!Number.isFinite(initialValue)) {
            return;
        }
        const clamped = Math.max(0, Math.min(100, Math.round(initialValue)));
        bar.style.width = `${clamped}%`;
        bar.setAttribute('aria-valuenow', String(clamped));
        const percentHolder = bar.querySelector('[data-progress-percent]');
        if (percentHolder) {
            percentHolder.textContent = clamped;
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
    labelLocked: button.dataset.nextLabelLocked || '<i class=\"fa-solid fa-lock me-2\"></i>Lectia urmatoare',
    labelUnlocked: button.dataset.nextLabelUnlocked || '<i class=\"fa-solid fa-arrow-right me-2\"></i>Lectia urmatoare',
});

const applyNextButtonState = (isUnlocked) => {
    const button = getNextButton();
    if (!button) {
        return;
    }
    const meta = getNextButtonMeta(button);
    if (isUnlocked) {
        removeClasses(button, meta.disabledClass);
        button.classList.remove('disabled');
        addClasses(button, meta.enabledClass);
        button.href = meta.url;
        button.dataset.locked = 'false';
        button.removeAttribute('aria-disabled');
        button.innerHTML = meta.labelUnlocked;
    } else {
        removeClasses(button, meta.enabledClass);
        addClasses(button, meta.disabledClass);
        button.classList.add('disabled');
        button.href = '#';
        button.dataset.locked = 'true';
        button.setAttribute('aria-disabled', 'true');
        button.innerHTML = meta.labelLocked;
    }
};

const initializeNextButtonState = () => {
    const button = getNextButton();
    if (!button) {
        return;
    }
    const meta = getNextButtonMeta(button);
    button.dataset.nextLabelLocked = button.dataset.nextLabelLocked || meta.labelLocked;
    button.dataset.nextLabelUnlocked = button.dataset.nextLabelUnlocked || meta.labelUnlocked;
    const isLocked = button.dataset.locked === 'true'
        || button.classList.contains('disabled')
        || button.getAttribute('aria-disabled') === 'true';
    applyNextButtonState(!isLocked);
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
                ? '<i class=\"fa-solid fa-check me-2\"></i>Bifat deja'
                : '<i class=\"fa-regular fa-circle-check me-2\"></i>Marchează reușita';
        } else {
            sourceButton.classList.toggle('btn-success', completed);
            sourceButton.classList.toggle('btn-outline-success', !completed);
            sourceButton.innerHTML = completed
                ? '<i class=\"fa-solid fa-check me-1\"></i>Finalizată'
                : '<i class=\"fa-regular fa-circle-check me-1\"></i>Marchează finalizarea';
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
    applyNextButtonState(completed);
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
                    feedbackEl.classList.add('text-danger');
                }
                return;
            }

            feedbackEl?.classList.remove('text-success', 'text-danger');
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

document.addEventListener('DOMContentLoaded', () => {
    initializeThemeControls();
    initializeProgressBars();
    initializeNextButtonState();
    wireToggleCompletion();
    wireQuizForms();
    wireFormsetAddButtons();
    wirePracticeDragDrop();
    wireConceptCards();
    wireCodeChallenges();
    wireVoiceButtons();
});
