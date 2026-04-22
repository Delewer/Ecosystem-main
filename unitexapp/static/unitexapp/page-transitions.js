(() => {
    // Enabled by default. Can be disabled via `window.UNITEX_ENABLE_PJAX = false`.
    const TRANSITIONS_ENABLED = window.UNITEX_ENABLE_PJAX !== false;

    const OVERLAY_SELECTOR = '[data-page-transition]';
    const MAIN_SELECTOR = '#main';
    const HEAD_STYLE_SELECTOR = 'link[rel~="stylesheet"], style';
    const MANAGED_STYLE_ATTR = 'data-unitex-head-style';
    const MANAGED_HEAD_STYLE_SELECTOR = `link[rel~="stylesheet"][${MANAGED_STYLE_ATTR}], style[${MANAGED_STYLE_ATTR}]`;
    const MANAGED_SCRIPT_ATTR = 'data-unitex-body-script';
    const MANAGED_SCRIPT_KEY_ATTR = 'data-unitex-script-key';
    const CORE_SCRIPT_PATHS = [
        '/static/unitexapp/script.js',
        '/static/unitexapp/vendor/barba.umd.js',
        '/static/unitexapp/page-transitions.js'
    ];
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const EASING = 'cubic-bezier(0.65, 0, 0.35, 1)';
    const DURATION = 450;
    const scrollPositions = new Map();
    const domParser = new DOMParser();

    const shouldReduceMotion = () => prefersReducedMotion.matches;

    const playOverlay = (phase) => {
        const overlay = document.querySelector(OVERLAY_SELECTOR);
        if (!overlay || shouldReduceMotion()) {
            if (phase === 'reveal' && overlay) {
                overlay.style.transform = 'scaleY(0)';
                overlay.style.display = 'none';
            }
            return Promise.resolve();
        }
        overlay.style.display = 'block';

        const frames = phase === 'cover'
            ? [
                { transform: 'scaleY(0)', transformOrigin: 'top center' },
                { transform: 'scaleY(1)', transformOrigin: 'top center' }
            ]
            : [
                { transform: 'scaleY(1)', transformOrigin: 'bottom center' },
                { transform: 'scaleY(0)', transformOrigin: 'bottom center' }
            ];

        try {
            const animation = overlay.animate(frames, {
                duration: DURATION,
                easing: EASING,
                fill: 'forwards'
            });
            return animation.finished.then(() => {
                if (phase === 'reveal') {
                    overlay.style.display = 'none';
                }
            }).catch(() => {});
        } catch (error) {
            if (phase === 'reveal') {
                overlay.style.display = 'none';
            }
            return Promise.resolve();
        }
    };

    const markHeadStylesManaged = () => {
        document.head.querySelectorAll(HEAD_STYLE_SELECTOR).forEach(styleNode => {
            styleNode.setAttribute(MANAGED_STYLE_ATTR, 'true');
        });
    };

    const normalizeUrl = (url) => {
        if (!url) {
            return '';
        }
        try {
            return new URL(url, window.location.href).href;
        } catch (error) {
            return String(url).trim();
        }
    };

    const getStyleKey = (styleNode) => {
        if (!styleNode) {
            return '';
        }
        if (styleNode.tagName === 'LINK') {
            const href = normalizeUrl(styleNode.getAttribute('href'));
            const media = (styleNode.getAttribute('media') || '').trim();
            return `link::${href}::${media}`;
        }
        if (styleNode.tagName === 'STYLE') {
            return `style::${(styleNode.textContent || '').trim()}`;
        }
        return '';
    };

    const isCoreScriptNode = (scriptNode) => {
        if (!scriptNode) {
            return false;
        }
        const src = scriptNode.getAttribute('src');
        if (!src) {
            return false;
        }
        const normalized = normalizeUrl(src);
        try {
            const pathname = new URL(normalized, window.location.href).pathname;
            return CORE_SCRIPT_PATHS.some((corePath) => pathname.endsWith(corePath));
        } catch (error) {
            return CORE_SCRIPT_PATHS.some((corePath) => normalized.includes(corePath));
        }
    };

    const getScriptKey = (scriptNode) => {
        if (!scriptNode) {
            return '';
        }
        const src = scriptNode.getAttribute('src');
        if (src) {
            return `src::${normalizeUrl(src)}`;
        }
        const type = (scriptNode.getAttribute('type') || '').trim();
        const inlineContent = (scriptNode.textContent || '').trim();
        return `inline::${type}::${inlineContent}`;
    };

    const markCurrentDynamicScripts = () => {
        document.body.querySelectorAll('script').forEach((scriptNode) => {
            if (scriptNode.hasAttribute(MANAGED_SCRIPT_ATTR)) {
                return;
            }
            if (isCoreScriptNode(scriptNode)) {
                return;
            }
            const key = getScriptKey(scriptNode);
            if (!key) {
                return;
            }
            scriptNode.setAttribute(MANAGED_SCRIPT_ATTR, 'true');
            scriptNode.setAttribute(MANAGED_SCRIPT_KEY_ATTR, key);
        });
    };

    const waitForScript = (scriptNode) => {
        if (!(scriptNode instanceof HTMLScriptElement) || !scriptNode.src) {
            return Promise.resolve();
        }
        return new Promise((resolve) => {
            let settled = false;
            const finish = () => {
                if (settled) {
                    return;
                }
                settled = true;
                resolve();
            };
            scriptNode.addEventListener('load', finish, { once: true });
            scriptNode.addEventListener('error', finish, { once: true });
            window.setTimeout(finish, 4000);
        });
    };

    const cloneScriptNode = (sourceNode) => {
        const clone = document.createElement('script');
        Array.from(sourceNode.attributes).forEach(({ name, value }) => {
            clone.setAttribute(name, value);
        });
        if (!sourceNode.src) {
            clone.textContent = sourceNode.textContent || '';
        }
        return clone;
    };

    const syncBodyScripts = async (nextDocument) => {
        if (!nextDocument?.body) {
            return;
        }

        const nextScriptNodes = Array.from(nextDocument.body.querySelectorAll('script'))
            .filter((scriptNode) => !isCoreScriptNode(scriptNode));
        const uniqueScripts = [];
        const seenKeys = new Set();

        nextScriptNodes.forEach((scriptNode) => {
            const key = getScriptKey(scriptNode);
            if (!key || seenKeys.has(key)) {
                return;
            }
            seenKeys.add(key);
            uniqueScripts.push({ key, scriptNode });
        });

        document.body.querySelectorAll(`script[${MANAGED_SCRIPT_ATTR}]`).forEach((node) => {
            if (!isCoreScriptNode(node)) {
                node.remove();
            }
        });

        for (const { key, scriptNode } of uniqueScripts) {
            const clone = cloneScriptNode(scriptNode);
            clone.setAttribute(MANAGED_SCRIPT_ATTR, 'true');
            clone.setAttribute(MANAGED_SCRIPT_KEY_ATTR, key);
            document.body.appendChild(clone);
            await waitForScript(clone);
        }
    };

    const waitForStylesheet = (styleNode) => {
        if (!(styleNode instanceof HTMLLinkElement)) {
            return Promise.resolve();
        }

        if (styleNode.sheet) {
            return Promise.resolve();
        }

        return new Promise(resolve => {
            let settled = false;
            const complete = () => {
                if (settled) {
                    return;
                }
                settled = true;
                resolve();
            };

            styleNode.addEventListener('load', complete, { once: true });
            styleNode.addEventListener('error', complete, { once: true });
            window.setTimeout(complete, 2000);
        });
    };

    const parseNextDocument = (rawHtml) => {
        if (!rawHtml || typeof rawHtml !== 'string') {
            return null;
        }
        try {
            return domParser.parseFromString(rawHtml, 'text/html');
        } catch (error) {
            return null;
        }
    };

    const syncDocumentShell = (nextDocument) => {
        if (!nextDocument) {
            return;
        }
        if (nextDocument.title) {
            document.title = nextDocument.title;
        }
        if (nextDocument.body && typeof nextDocument.body.className === 'string') {
            document.body.className = nextDocument.body.className;
        }
    };

    const syncHeadStyles = async (nextDocument) => {
        if (!nextDocument?.head) {
            return;
        }

        const nextStyles = Array.from(nextDocument.head.querySelectorAll(HEAD_STYLE_SELECTOR));
        const currentStyles = Array.from(document.head.querySelectorAll(MANAGED_HEAD_STYLE_SELECTOR));
        const currentByKey = new Map();
        const requiredStyleKeys = new Set();
        const orderedStyles = [];
        const pendingLoads = [];

        currentStyles.forEach(styleNode => {
            const key = getStyleKey(styleNode);
            if (key) {
                currentByKey.set(key, styleNode);
            }
        });

        nextStyles.forEach(styleNode => {
            const key = getStyleKey(styleNode);
            if (!key || requiredStyleKeys.has(key)) {
                return;
            }

            requiredStyleKeys.add(key);
            let currentStyleNode = currentByKey.get(key);

            if (!currentStyleNode) {
                currentStyleNode = styleNode.cloneNode(true);
                currentStyleNode.setAttribute(MANAGED_STYLE_ATTR, 'true');
                document.head.appendChild(currentStyleNode);
                pendingLoads.push(waitForStylesheet(currentStyleNode));
            }

            orderedStyles.push(currentStyleNode);
        });

        orderedStyles.forEach(styleNode => {
            document.head.appendChild(styleNode);
        });

        if (pendingLoads.length) {
            await Promise.all(pendingLoads);
        }

        currentStyles.forEach(styleNode => {
            const key = getStyleKey(styleNode);
            if (!requiredStyleKeys.has(key)) {
                styleNode.remove();
            }
        });
    };

    const focusMain = (container) => {
        const main = container?.querySelector(MAIN_SELECTOR);
        if (main && typeof main.focus === 'function') {
            requestAnimationFrame(() => {
                main.focus({ preventScroll: true });
            });
        }
    };

    const shouldPrevent = ({ el }) => {
        if (!el) {
            return false;
        }
        const href = el.getAttribute('href') || '';
        return href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || el.hasAttribute('data-barba-prevent');
    };

    const shouldRestoreScroll = (trigger) => trigger === 'popstate';

    const handleScrollRestoration = (trigger, namespace) => {
        const stored = scrollPositions.get(namespace);
        const target = shouldRestoreScroll(trigger) && typeof stored === 'number' ? stored : 0;
        window.scrollTo(0, target);
    };

    const dispatchPageReady = (data) => {
        const detail = {
            namespace: data?.next?.namespace || '',
            trigger: data?.trigger || 'programmatic',
            url: window.location.href
        };
        document.dispatchEvent(new CustomEvent('unitex:page-ready', { detail }));
    };

    const bootstrap = () => {
        if (!TRANSITIONS_ENABLED) {
            return;
        }
        if (typeof window === 'undefined' || typeof window.barba === 'undefined') {
            return;
        }

        window.history.scrollRestoration = 'manual';
        markHeadStylesManaged();
        markCurrentDynamicScripts();

        window.barba.init({
            prefetch: true,
            prevent: shouldPrevent,
            schema: {
                wrapper: 'wrapper',
                container: 'container'
            },
            transitions: [{
                name: 'unitex-overlay',
                async leave(data) {
                    scrollPositions.set(data.current.namespace, window.scrollY);
                    await playOverlay('cover');
                },
                async beforeEnter(data) {
                    const nextDocument = parseNextDocument(data.next?.html);
                    syncDocumentShell(nextDocument);
                    await syncHeadStyles(nextDocument);
                    await syncBodyScripts(nextDocument);
                    handleScrollRestoration(data.trigger, data.next.namespace);
                },
                async enter(data) {
                    await playOverlay('reveal');
                    focusMain(data.next.container);
                    dispatchPageReady(data);
                }
            }]
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
    } else {
        bootstrap();
    }
})();
