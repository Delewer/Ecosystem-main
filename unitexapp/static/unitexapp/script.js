(() => {
    const doc = document;
    const html = doc.documentElement;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const THEME_STORAGE_KEY = 'unitex-theme';
    const COOKIE_CONSENT_KEY = 'unitex_cookie_consent';
    const PAGE_READY_FLAG = 'unitexPageReadyHookBound';

    const ICON_LIGHT = '\u2600';
    const ICON_DARK = '\u263D';
    const themeToggle = doc.querySelector('[data-theme-toggle]');
    const themeLabel = themeToggle?.querySelector('[data-theme-toggle-label]');
    const themeIcon = themeToggle?.querySelector('.theme-toggle__icon');
    const getCookieValue = name => {
        const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const match = doc.cookie.match(new RegExp(`(?:^|; )${escapedName}=([^;]+)`));
        return match ? decodeURIComponent(match[1]) : '';
    };
    const setCookieValue = (name, value, maxAgeSeconds) => {
        const secureFlag = window.location.protocol === 'https:' ? '; Secure' : '';
        doc.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax${secureFlag}`;
    };
    const getCsrfToken = () => {
        return getCookieValue('csrftoken');
    };

    const applyTheme = (theme) => {
        const normalized = theme === 'dark' ? 'dark' : 'light';
        html.setAttribute('data-theme', normalized);
        if (themeToggle) {
            themeToggle.dataset.theme = normalized;
            if (themeLabel) {
                themeLabel.textContent = normalized === 'dark' ? 'Noapte' : 'Zi';
            }
            if (themeIcon) {
                themeIcon.textContent = normalized === 'dark' ? ICON_DARK : ICON_LIGHT;
            }
            themeToggle.setAttribute('aria-pressed', String(normalized === 'dark'));
        }
        try {
            localStorage.setItem(THEME_STORAGE_KEY, normalized);
        } catch (error) {
            /* ignore storage errors */
        }
    };

    const loadTheme = () => {
        try {
            return localStorage.getItem(THEME_STORAGE_KEY);
        } catch (error) {
            return null;
        }
    };

    if (themeToggle) {
        const storedTheme = loadTheme() || html.getAttribute('data-theme');
        if (storedTheme) {
            applyTheme(storedTheme);
        }
        themeToggle.addEventListener('click', () => {
            const nextTheme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme);
        });
    }

    const navToggle = doc.querySelector('[data-navbar-toggle]');
    const navMenu = doc.querySelector('[data-navbar-menu]');
    if (navToggle && navMenu) {
        const closeMenu = () => {
            navMenu.classList.remove('is-open');
            navToggle.setAttribute('aria-expanded', 'false');
        };
        navToggle.addEventListener('click', () => {
            const isOpen = navMenu.classList.toggle('is-open');
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });
        navMenu.querySelectorAll('a.nav-link').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
        doc.addEventListener('keydown', event => {
            if (event.key === 'Escape' && navMenu.classList.contains('is-open')) {
                closeMenu();
            }
        });
        doc.addEventListener('click', event => {
            if (!navMenu.contains(event.target) && !navToggle.contains(event.target) && navMenu.classList.contains('is-open')) {
                closeMenu();
            }
        });
    }

    if (html.dataset.unitexSmoothScrollBound !== 'true') {
        html.dataset.unitexSmoothScrollBound = 'true';
        doc.addEventListener('click', event => {
            if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
                return;
            }
            const anchor = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
            if (!anchor) {
                return;
            }
            const targetId = anchor.getAttribute('href');
            if (!targetId || targetId === '#' || targetId === '#0') {
                return;
            }
            const target = doc.querySelector(targetId);
            if (!target) {
                return;
            }
            event.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            if (typeof target.focus === 'function') {
                requestAnimationFrame(() => target.focus({ preventScroll: true }));
            }
        });
    }

    const scrollProgress = doc.querySelector('[data-scroll-progress]');
    const scrollTopButton = doc.querySelector('[data-scroll-top]');
    const updateScrollState = () => {
        const maxScrollable = doc.documentElement.scrollHeight - window.innerHeight;
        if (scrollProgress) {
            const progress = maxScrollable > 0 ? (window.scrollY / maxScrollable) * 100 : 0;
            scrollProgress.style.width = `${Math.min(100, Math.max(0, progress))}%`;
        }
        if (scrollTopButton) {
            if (window.scrollY > 400) {
                scrollTopButton.classList.add('is-visible');
            } else {
                scrollTopButton.classList.remove('is-visible');
            }
        }
    };

    window.addEventListener('scroll', updateScrollState, { passive: true });
    updateScrollState();

    if (scrollTopButton) {
        scrollTopButton.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    const animationObserver = !prefersReducedMotion && 'IntersectionObserver' in window
        ? new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    animationObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 })
        : null;

    const initializeAnimatedBlocks = () => {
        const animatedBlocks = doc.querySelectorAll('[data-animate]');
        if (!animatedBlocks.length) {
            return;
        }
        if (prefersReducedMotion) {
            animatedBlocks.forEach(el => el.classList.add('is-visible'));
            return;
        }
        if (!animationObserver) {
            animatedBlocks.forEach(el => el.classList.add('is-visible'));
            return;
        }
        animatedBlocks.forEach(el => {
            if (el.dataset.unitexAnimateBound === 'true') {
                return;
            }
            el.dataset.unitexAnimateBound = 'true';
            animationObserver.observe(el);
        });
    };

    const initializeTiltTargets = () => {
        if (prefersReducedMotion) {
            return;
        }
        const tiltTargets = doc.querySelectorAll('.card, .info-card, .learning-card, .category-card, .benefit-card');
        const MAX_ROTATION = 6;
        tiltTargets.forEach(el => {
            if (el.dataset.unitexTiltBound === 'true') {
                return;
            }
            el.dataset.unitexTiltBound = 'true';
            const handleMove = event => {
                const rect = el.getBoundingClientRect();
                const rotateX = ((event.clientY - rect.top) / rect.height - 0.5) * -MAX_ROTATION;
                const rotateY = ((event.clientX - rect.left) / rect.width - 0.5) * MAX_ROTATION;
                el.style.transform = `perspective(900px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-6px)`;
            };
            const reset = () => {
                el.style.transform = '';
            };
            el.addEventListener('pointermove', handleMove);
            el.addEventListener('pointerleave', reset);
            el.addEventListener('pointerup', reset);
        });
    };

    const initLeadForm = () => {
        const leadForm = doc.querySelector('[data-lead-form]');
        if (!leadForm) {
            return;
        }
        if (leadForm.dataset.unitexLeadBound === 'true') {
            return;
        }
        leadForm.dataset.unitexLeadBound = 'true';
        const successNode = leadForm.querySelector('[data-lead-success]');
        const errorNode = leadForm.querySelector('[data-lead-error]');
        const submitButton = leadForm.querySelector('[type="submit"]');
        const fieldsBlock = leadForm.querySelector('[data-lead-fields]');
        const confirmBlock = leadForm.querySelector('[data-lead-confirm]');
        const resetButton = leadForm.querySelector('[data-lead-reset]');
        const toggleStatus = (node, message) => {
            if (!node) {
                return;
            }
            const content = message || '';
            node.textContent = content;
            node.hidden = content.length === 0;
        };
        const showConfirm = () => {
            if (fieldsBlock) {
                fieldsBlock.hidden = true;
            }
            if (confirmBlock) {
                confirmBlock.hidden = false;
            }
        };
        const showForm = () => {
            if (fieldsBlock) {
                fieldsBlock.hidden = false;
            }
            if (confirmBlock) {
                confirmBlock.hidden = true;
            }
            toggleStatus(successNode, '');
            toggleStatus(errorNode, '');
        };
        showForm();
        leadForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            toggleStatus(successNode, '');
            toggleStatus(errorNode, '');
            submitButton?.setAttribute('disabled', 'disabled');
            const formData = new FormData(leadForm);
            try {
                const response = await fetch(leadForm.getAttribute('action') || window.location.href, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: formData,
                });
                const payload = await response.json().catch(() => null);
                if (!response.ok || !payload?.success) {
                    const errors = payload?.errors ? Object.values(payload.errors).filter(Boolean) : [];
                    const message = payload?.message || errors[0] || 'Nu am putut trimite formularul.';
                    throw new Error(message);
                }
                toggleStatus(successNode, payload.message || 'Mulțumim! Revenim curând.');
                leadForm.reset();
                showConfirm();
            } catch (error) {
                toggleStatus(errorNode, error?.message || 'Nu am putut trimite formularul.');
            } finally {
                submitButton?.removeAttribute('disabled');
            }
        });

        resetButton?.addEventListener('click', () => {
            showForm();
        });
    };

    const initCookieBanner = () => {
        const banner = doc.querySelector('[data-cookie-banner]');
        if (!banner || banner.dataset.unitexCookieBound === 'true') {
            return;
        }
        banner.dataset.unitexCookieBound = 'true';

        const showBanner = () => {
            banner.hidden = false;
            requestAnimationFrame(() => {
                banner.classList.add('is-visible');
            });
        };
        const hideBanner = () => {
            banner.classList.remove('is-visible');
            window.setTimeout(() => {
                banner.hidden = true;
            }, 220);
        };

        if (getCookieValue(COOKIE_CONSENT_KEY)) {
            banner.hidden = true;
        } else {
            showBanner();
        }

        banner.querySelectorAll('[data-cookie-consent]').forEach(button => {
            button.addEventListener('click', () => {
                const choice = button.getAttribute('data-cookie-consent') === 'accept'
                    ? 'accept'
                    : 'essential';
                setCookieValue(COOKIE_CONSENT_KEY, choice, 60 * 60 * 24 * 365);
                hideBanner();
            });
        });
    };

    const initializeProgressBars = () => {
        const progressBars = doc.querySelectorAll('[data-progress-bar]');
        if (!progressBars.length) {
            return;
        }
        progressBars.forEach(bar => {
            if (bar.dataset.unitexProgressBound === 'true') {
                return;
            }
            bar.dataset.unitexProgressBound = 'true';
            const targetValue = parseFloat(bar.dataset.progressInitial || bar.getAttribute('aria-valuenow') || '0');
            const clamped = Math.max(0, Math.min(100, isNaN(targetValue) ? 0 : targetValue));
            const valueOutput = bar.querySelector('[data-progress-percent]');
            const container = bar.closest('[data-progress-container]') || bar.parentElement;

            if (prefersReducedMotion) {
                bar.style.width = `${clamped}%`;
                if (valueOutput) {
                    valueOutput.textContent = clamped.toFixed(0);
                }
                if (clamped >= 100) {
                    container?.classList.add('is-complete');
                }
                return;
            }

            let startTime = null;
            const animate = timestamp => {
                if (!startTime) {
                    startTime = timestamp;
                }
                const progress = Math.min((timestamp - startTime) / 900, 1);
                const current = Math.round(progress * clamped);
                bar.style.width = `${current}%`;
                if (valueOutput) {
                    valueOutput.textContent = current.toString();
                }
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else if (clamped >= 100) {
                    container?.classList.add('is-complete');
                }
            };
            requestAnimationFrame(animate);
        });
    };

    const initializePageInteractions = () => {
        initializeAnimatedBlocks();
        initializeTiltTargets();
        initLeadForm();
        initCookieBanner();
        initializeProgressBars();
        updateScrollState();
    };

    initializePageInteractions();

    if (html.dataset[PAGE_READY_FLAG] !== 'true') {
        html.dataset[PAGE_READY_FLAG] = 'true';
        doc.addEventListener('unitex:page-ready', () => {
            initializePageInteractions();
        });
    }
})();
