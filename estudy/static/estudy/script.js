/* eslint-env browser */

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

document.addEventListener('DOMContentLoaded', () => {
    wireToggleCompletion();
    wireQuizForms();
    wireFormsetAddButtons();
    wirePracticeDragDrop();
    wireConceptCards();
    wireCodeChallenges();
});
