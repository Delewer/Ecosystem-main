(() => {
    const root = document.querySelector("[data-robotlab-play]");
    if (!root) {
        return;
    }

    const levelDataNode = document.querySelector("#robot-lab-level-data");
    if (!levelDataNode) {
        return;
    }

    const parseJSON = (text, fallback) => {
        try {
            const value = JSON.parse(text);
            return value && typeof value === "object" ? value : fallback;
        } catch (error) {
            console.error("Failed to parse Robot Lab level JSON", error);
            return fallback;
        }
    };

    const STAGE_CONFIG = {
        buttons: {
            showBuilder: true,
            readOnly: false,
            codeLabel: "Programul tau",
            emptyConsole: "Apasa butoanele din joc sau scrie direct in editor, apoi ruleaza.",
        },
        buttons_code: {
            showBuilder: true,
            readOnly: false,
            codeLabel: "Programul tau",
            emptyConsole: "Construieste ruta cu butoane sau scrie singur codul, apoi ruleaza.",
        },
        fill_gaps: {
            showBuilder: true,
            readOnly: false,
            codeLabel: "Completeaza linia lipsa",
            emptyConsole: "Completeaza comanda lipsa sau foloseste butoanele, apoi ruleaza programul.",
        },
        code: {
            showBuilder: true,
            readOnly: false,
            codeLabel: "Programul tau",
            emptyConsole: "Scrie singur programul sau foloseste butoanele rapide, apoi apasa Ruleaza codul.",
        },
    };

    const COMMAND_META = {
        up: {
            label: "up()",
            shortLabel: "Sus",
            symbolHtml: "&uarr;",
            className: "dir--up",
            kind: "direction",
        },
        down: {
            label: "down()",
            shortLabel: "Jos",
            symbolHtml: "&darr;",
            className: "dir--down",
            kind: "direction",
        },
        left: {
            label: "left()",
            shortLabel: "Stanga",
            symbolHtml: "&larr;",
            className: "dir--left",
            kind: "direction",
        },
        right: {
            label: "right()",
            shortLabel: "Dreapta",
            symbolHtml: "&rarr;",
            className: "dir--right",
            kind: "direction",
        },
        move: {
            label: "move()",
            shortLabel: "Mergi",
            symbolHtml: "Go",
            kind: "action",
        },
        turn_left: {
            label: "turn_left()",
            shortLabel: "Rotire stanga",
            symbolHtml: "TL",
            kind: "action",
        },
        turn_right: {
            label: "turn_right()",
            shortLabel: "Rotire dreapta",
            symbolHtml: "TR",
            kind: "action",
        },
        pick: {
            label: "pick()",
            shortLabel: "Colecteaza",
            symbolHtml: "Pick",
            kind: "action",
        },
        activate: {
            label: "activate()",
            shortLabel: "Activeaza",
            symbolHtml: "On",
            kind: "action",
        },
    };

    const level = parseJSON(levelDataNode.textContent || "{}", {});
    const runUrl = root.dataset.runUrl || "";
    const levelId = root.dataset.levelId || level.id || "";
    const uiStage = String(level.ui_stage || "code");
    const stageConfig = STAGE_CONFIG[uiStage] || STAGE_CONFIG.code;
    const starterCode = level.starter_code || "";
    const startDir = String(level.start_dir || "E").toUpperCase();
    const allowedApi = Array.isArray(level.allowed_api) ? level.allowed_api.map((item) => String(item)) : [];
    const grid = Array.isArray(level.grid) ? level.grid.map((row) => String(row)) : [];
    const maxCols = grid.reduce((acc, row) => Math.max(acc, row.length), 0);
    const tileSprites = [1, 2, 3, 4].map((idx) => `/static/estudy/game/tiles/tile-${idx}.png`);
    const wallSprites = [1, 2, 3, 4, 5, 6, 7, 8, 9].map((idx) => `/static/estudy/game/walls/wall-${idx}.png`);

    const gridNode = root.querySelector("[data-robot-grid]");
    const codeInput = root.querySelector("[data-code-input]");
    const codeLabel = root.querySelector("[data-code-label]");
    const runBtn = root.querySelector("[data-run-btn]");
    const runStepBtn = root.querySelector("[data-run-step-btn]");
    const resetCodeBtn = root.querySelector("[data-reset-code]");
    const clearCodeButtons = Array.from(root.querySelectorAll("[data-clear-code]"));
    const statusNode = root.querySelector("[data-run-status]");
    const requestSolution = root.querySelector("[data-request-solution]");
    const traceList = root.querySelector("[data-trace-list]");
    const consoleList = root.querySelector("[data-console-list]");
    const builderPanel = root.querySelector("[data-builder-panel]");
    const directionPad = root.querySelector("[data-direction-pad]");
    const extraCommands = root.querySelector("[data-extra-commands]");
    const programList = root.querySelector("[data-program-list]");

    const mentorNodes = {
        what: root.querySelector("[data-mentor-what]"),
        mistake: root.querySelector("[data-mentor-mistake]"),
        hint1: root.querySelector("[data-mentor-h1]"),
        hint2: root.querySelector("[data-mentor-h2]"),
        focus: root.querySelector("[data-mentor-focus]"),
        encourage: root.querySelector("[data-mentor-encourage]"),
        solutionWrap: root.querySelector("[data-mentor-solution-wrap]"),
        solution: root.querySelector("[data-mentor-solution]"),
    };

    const hintModal = root.querySelector("[data-hint-modal]");
    const hintModalTitle = root.querySelector("[data-hint-modal-title]");
    const hintModalContent = root.querySelector("[data-hint-modal-content]");
    const hintButtons = Array.from(root.querySelectorAll("[data-hint-open]"));
    const hintCloseButtons = Array.from(root.querySelectorAll("[data-hint-modal-close]"));

    const HINT_CONFIG = {
        what: {
            title: "Ce s-a intamplat",
            node: mentorNodes.what,
            fallback: "Ruleaza codul pentru a primi feedback pe rezultat.",
        },
        mistake: {
            title: "Explicatie",
            node: mentorNodes.mistake,
            fallback: "Explicatia apare dupa o rulare a codului.",
        },
        hint1: {
            title: "Indiciu 1",
            node: mentorNodes.hint1,
            fallback: "Indiciul de nivel 1 apare dupa evaluare.",
        },
        hint2: {
            title: "Indiciu 2",
            node: mentorNodes.hint2,
            fallback: "Indiciul de nivel 2 apare dupa evaluare.",
        },
        focus: {
            title: "Concept cheie",
            node: mentorNodes.focus,
            fallback: "Conceptul vizat apare dupa rulare.",
        },
        encourage: {
            title: "Incurajare",
            node: mentorNodes.encourage,
            fallback: "RoboMentor iti trimite incurajare dupa rulare.",
        },
        solution: {
            title: "Solutie exemplu",
            node: mentorNodes.solution,
            fallback: 'Bifeaza "Vreau si un exemplu de solutie", apoi ruleaza codul.',
        },
    };

    const playback = {
        trace: [],
        index: -1,
        timer: null,
        robot: null,
    };

    const runnerState = {
        preparedCode: "",
        lastResult: null,
    };

    const getCsrfToken = () => {
        const raw = document.cookie || "";
        for (const part of raw.split(";")) {
            const item = part.trim();
            if (item.startsWith("csrftoken=")) {
                return decodeURIComponent(item.slice("csrftoken=".length));
            }
        }
        return "";
    };

    const findStart = () => {
        for (let rowIndex = 0; rowIndex < grid.length; rowIndex += 1) {
            const row = grid[rowIndex];
            for (let colIndex = 0; colIndex < row.length; colIndex += 1) {
                if (row[colIndex] === "S") {
                    return { r: rowIndex, c: colIndex };
                }
            }
        }
        return { r: 0, c: 0 };
    };

    const startPos = findStart();
    const dirGlyph = {
        N: "N",
        E: "E",
        S: "S",
        W: "W",
    };

    const robotFromTrace = (traceEntry) => {
        if (!traceEntry || !Array.isArray(traceEntry.position)) {
            return null;
        }
        return {
            r: Number(traceEntry.position[0]) || 0,
            c: Number(traceEntry.position[1]) || 0,
            dir: String(traceEntry.dir || startDir).toUpperCase(),
        };
    };

    const normalizeTile = (tile) => {
        if (!tile || tile === "S") {
            return ".";
        }
        return tile;
    };

    const pickSprite = (pool, rowIndex, colIndex) => {
        if (!pool.length) {
            return "";
        }
        const index = Math.abs((rowIndex * 37 + colIndex * 17 + rowIndex * colIndex) % pool.length);
        return pool[index];
    };

    const tileTokenKind = (tile) => {
        if (tile === "G") return "goal";
        if (tile === "T") return "terminal";
        if (tile === "B") return "battery";
        if (tile === "K") return "key";
        if (tile === "H") return "hazard";
        if (tile === "D") return "door";
        return "";
    };

    const renderGrid = () => {
        if (!gridNode) {
            return;
        }
        gridNode.innerHTML = "";
        gridNode.style.gridTemplateColumns = `repeat(${Math.max(1, maxCols)}, minmax(24px, 1fr))`;

        for (let rowIndex = 0; rowIndex < grid.length; rowIndex += 1) {
            const row = grid[rowIndex];
            for (let colIndex = 0; colIndex < maxCols; colIndex += 1) {
                const cell = document.createElement("div");
                cell.className = "robotlab-cell";
                const tile = normalizeTile(row[colIndex] || "#");
                let sprite = "";

                if (tile === "#") {
                    cell.classList.add("is-wall");
                    sprite = pickSprite(wallSprites, rowIndex, colIndex);
                } else if (tile === "G") {
                    cell.classList.add("is-goal");
                    sprite = pickSprite(tileSprites, rowIndex, colIndex);
                } else if (tile === "T") {
                    cell.classList.add("is-terminal");
                    sprite = pickSprite(tileSprites, rowIndex, colIndex);
                } else if (tile === "B" || tile === "K") {
                    cell.classList.add("is-item");
                    sprite = pickSprite(tileSprites, rowIndex, colIndex);
                } else if (tile === "H") {
                    cell.classList.add("is-hazard");
                    sprite = pickSprite(tileSprites, rowIndex, colIndex);
                } else if (tile === "D") {
                    cell.classList.add("is-door");
                    sprite = pickSprite(tileSprites, rowIndex, colIndex);
                } else {
                    cell.classList.add("is-floor");
                    sprite = pickSprite(tileSprites, rowIndex, colIndex);
                }

                if (sprite) {
                    cell.style.setProperty("--robotlab-cell-sprite", `url("${sprite}")`);
                }

                const tokenKind = tileTokenKind(tile);
                if (tokenKind) {
                    const token = document.createElement("span");
                    token.className = `robotlab-cell__token robotlab-cell__token--${tokenKind}`;
                    cell.appendChild(token);
                }

                if (playback.robot && playback.robot.r === rowIndex && playback.robot.c === colIndex) {
                    cell.classList.add("has-robot");

                    const robot = document.createElement("span");
                    robot.className = "robotlab-robot";

                    const eyes = document.createElement("span");
                    eyes.className = "robotlab-robot__eyes";

                    const smile = document.createElement("span");
                    smile.className = "robotlab-robot__smile";

                    const dir = document.createElement("span");
                    dir.className = "robotlab-robot__dir";
                    dir.textContent = dirGlyph[playback.robot.dir] || "E";

                    robot.appendChild(eyes);
                    robot.appendChild(smile);
                    robot.appendChild(dir);
                    cell.appendChild(robot);
                }

                gridNode.appendChild(cell);
            }
        }
    };

    const stopPlayback = () => {
        if (playback.timer) {
            window.clearInterval(playback.timer);
            playback.timer = null;
        }
    };

    const setStatus = (text, kind = "idle") => {
        if (statusNode) {
            statusNode.textContent = text;
            statusNode.dataset.statusKind = kind;
        }
    };

    const renderConsole = (lines) => {
        if (!consoleList) {
            return;
        }
        consoleList.innerHTML = "";
        const safeLines = Array.isArray(lines) && lines.length ? lines : [stageConfig.emptyConsole];
        safeLines.forEach((line) => {
            const item = document.createElement("li");
            item.textContent = line;
            consoleList.appendChild(item);
        });
    };

    const readMentorValue = (type) => {
        const config = HINT_CONFIG[type];
        if (!config) {
            return "Indiciu indisponibil.";
        }
        const value = config.node?.textContent?.trim() || "";
        if (value && value !== "-") {
            return value;
        }
        return config.fallback;
    };

    const updateSolutionHintButton = () => {
        const solutionButton = hintButtons.find((button) => button.dataset.hintType === "solution");
        if (!solutionButton) {
            return;
        }
        const hasSolution = Boolean(mentorNodes.solution?.textContent?.trim());
        solutionButton.disabled = !hasSolution;
        solutionButton.setAttribute("aria-disabled", String(!hasSolution));
    };

    const closeHintModal = () => {
        if (!hintModal || hintModal.hasAttribute("hidden")) {
            return;
        }
        hintModal.setAttribute("hidden", "");
        document.body.classList.remove("robotlab-modal-open");
    };

    const openHintModal = (type) => {
        const config = HINT_CONFIG[type];
        if (!config || !hintModal || !hintModalTitle || !hintModalContent) {
            return;
        }
        hintModalTitle.textContent = config.title;
        hintModalContent.textContent = readMentorValue(type);
        hintModal.removeAttribute("hidden");
        document.body.classList.add("robotlab-modal-open");
    };

    const renderTrace = () => {
        if (!traceList) {
            return;
        }
        traceList.innerHTML = "";
        if (!playback.trace.length) {
            const item = document.createElement("li");
            item.textContent = "Ruleaza codul ca sa vezi pasii executiei.";
            traceList.appendChild(item);
            return;
        }

        playback.trace.forEach((entry) => {
            const item = document.createElement("li");
            const step = Number(entry.step || 0);
            const action = entry.action ? `${entry.action}()` : "";
            const error = entry.error ? `error=${entry.error}` : "";
            const where = Array.isArray(entry.position)
                ? `pos=[${entry.position[0]},${entry.position[1]}]`
                : "";
            item.textContent = [`#${step}`, action, error, where].filter(Boolean).join(" - ");
            traceList.appendChild(item);
        });
    };

    const applyTraceIndex = (index) => {
        if (!playback.trace.length) {
            playback.robot = { r: startPos.r, c: startPos.c, dir: startDir };
            renderGrid();
            return;
        }

        const safeIndex = Math.max(-1, Math.min(index, playback.trace.length - 1));
        playback.index = safeIndex;

        if (safeIndex < 0) {
            playback.robot = { r: startPos.r, c: startPos.c, dir: startDir };
            renderGrid();
            return;
        }

        const robot = robotFromTrace(playback.trace[safeIndex]);
        playback.robot = robot || playback.robot || { r: startPos.r, c: startPos.c, dir: startDir };
        renderGrid();
    };

    const resetPlayback = () => {
        stopPlayback();
        playback.trace = [];
        playback.index = -1;
        playback.robot = { r: startPos.r, c: startPos.c, dir: startDir };
        renderGrid();
        renderTrace();
    };

    const setMentor = (mentor) => {
        if (!mentor || typeof mentor !== "object") {
            return;
        }
        if (mentorNodes.what) mentorNodes.what.textContent = mentor.what_happened || "-";
        if (mentorNodes.mistake) mentorNodes.mistake.textContent = mentor.mistake_explanation || "-";
        if (mentorNodes.hint1) mentorNodes.hint1.textContent = mentor.hint_level_1 || "-";
        if (mentorNodes.hint2) mentorNodes.hint2.textContent = mentor.hint_level_2 || "-";
        if (mentorNodes.focus) mentorNodes.focus.textContent = mentor.concept_focus || "-";
        if (mentorNodes.encourage) mentorNodes.encourage.textContent = mentor.encouragement || "-";
        if (mentor.example_solution) {
            if (mentorNodes.solutionWrap) mentorNodes.solutionWrap.hidden = false;
            if (mentorNodes.solution) mentorNodes.solution.textContent = mentor.example_solution;
        } else {
            if (mentorNodes.solutionWrap) mentorNodes.solutionWrap.hidden = true;
            if (mentorNodes.solution) mentorNodes.solution.textContent = "";
        }
        updateSolutionHintButton();
    };

    const normalizeLines = (rawCode) =>
        String(rawCode || "")
            .split(/\r?\n/)
            .map((line) => line.trim())
            .filter(Boolean);

    const renderProgramList = (lines) => {
        if (!programList) {
            return;
        }
        programList.innerHTML = "";
        const safeLines = lines.length ? lines : ["Adauga comenzi din butoane."];
        safeLines.forEach((line) => {
            const item = document.createElement("li");
            item.textContent = line;
            programList.appendChild(item);
        });
    };

    const syncProgramFromCode = () => {
        const lines = normalizeLines(codeInput?.value || "");
        renderProgramList(lines);
    };

    const insertAtCursor = (line) => {
        if (!codeInput) {
            return;
        }
        const start = typeof codeInput.selectionStart === "number" ? codeInput.selectionStart : codeInput.value.length;
        const end = typeof codeInput.selectionEnd === "number" ? codeInput.selectionEnd : codeInput.value.length;
        const before = codeInput.value.slice(0, start);
        const after = codeInput.value.slice(end);
        const needsLeadingNewline = before && !before.endsWith("\n");
        const needsTrailingNewline = after && !after.startsWith("\n");
        const inserted = `${needsLeadingNewline ? "\n" : ""}${line}${needsTrailingNewline ? "\n" : ""}`;
        codeInput.value = `${before}${inserted}${after}`;
        const caret = before.length + inserted.length;
        codeInput.focus();
        codeInput.selectionStart = caret;
        codeInput.selectionEnd = caret;
    };

    const appendCommand = (command) => {
        const line = `${command}()`;
        if (uiStage === "fill_gaps" && codeInput) {
            if (codeInput.value.includes("___")) {
                codeInput.value = codeInput.value.replace("___", line);
            } else {
                insertAtCursor(line);
            }
            syncProgramFromCode();
            return;
        }

        insertAtCursor(line);
        syncProgramFromCode();
    };

    const clearProgram = () => {
        if (!codeInput) {
            return;
        }
        runnerState.preparedCode = "";
        runnerState.lastResult = null;
        resetPlayback();
        codeInput.value = "";
        syncProgramFromCode();
        renderConsole(["Program golit. Construieste o solutie noua si ruleaza din nou."]);
        setStatus("Program golit.", "idle");
    };

    const resetCode = () => {
        if (!codeInput) {
            return;
        }
        runnerState.preparedCode = "";
        runnerState.lastResult = null;
        resetPlayback();
        codeInput.value = starterCode;
        syncProgramFromCode();
        renderConsole([stageConfig.emptyConsole]);
        setStatus("Cod resetat.", "idle");
    };

    const ensureProgramExists = () => {
        const lines = normalizeLines(codeInput?.value || "");
        if (lines.length) {
            return true;
        }
        resetPlayback();
        renderConsole([
            "Programul este gol.",
            "Adauga macar o comanda din butoane sau scrie un pas in editor.",
        ]);
        setStatus("Adauga cel putin o comanda.", "warning");
        return false;
    };

    const buildFallbackConsole = (data) => {
        const lines = ["Program pornit..."];
        const trace = Array.isArray(data.execution_trace) ? data.execution_trace : [];
        trace.forEach((entry) => {
            const step = Number(entry.step || 0);
            const action = entry.action ? `${entry.action}()` : "actiune";
            lines.push(`Pasul ${step}: ${action}`);
        });
        if (data.solved) {
            lines.push(`Misiune finalizata in ${Number(data.steps_used || 0)} pasi.`);
        } else if (data.primary_error) {
            lines.push(String(data.primary_error));
        } else {
            lines.push("Program terminat.");
        }
        return lines;
    };

    const buildSteppedConsole = (data, targetIndex) => {
        const trace = Array.isArray(data?.execution_trace) ? data.execution_trace : [];
        if (!trace.length || targetIndex < 0) {
            return [stageConfig.emptyConsole];
        }

        const safeIndex = Math.min(targetIndex, trace.length - 1);
        const lines = ["Program pornit..."];
        for (let index = 0; index <= safeIndex; index += 1) {
            const entry = trace[index] || {};
            const step = Number(entry.step || index + 1);
            const action = entry.action ? `${entry.action}()` : "actiune";
            lines.push(`Pasul ${step}: ${action}`);
            if (entry.error) {
                lines.push(`Eroare la pasul ${step}: ${entry.error}`);
                return lines;
            }
        }

        if (safeIndex >= trace.length - 1) {
            if (data?.solved) {
                lines.push(`Misiune finalizata in ${Number(data.steps_used || trace.length)} pasi.`);
            } else if (data?.primary_error) {
                lines.push(String(data.primary_error));
            } else {
                lines.push("Program terminat.");
            }
        }

        return lines;
    };

    const getStepStatus = (data, currentIndex) => {
        const trace = Array.isArray(data?.execution_trace) ? data.execution_trace : [];
        if (!trace.length || currentIndex < 0) {
            return {
                text: data?.status_message || "Nu exista pasi executabili.",
                kind: data?.status_kind || "warning",
            };
        }

        const safeIndex = Math.min(currentIndex, trace.length - 1);
        const entry = trace[safeIndex] || {};
        if (entry.error) {
            return {
                text: `Program oprit la pasul ${Number(entry.step || safeIndex + 1)}.`,
                kind: "error",
            };
        }

        if (safeIndex >= trace.length - 1) {
            if (data?.solved) {
                return {
                    text: data?.status_message || `Misiune finalizata in ${Number(data.steps_used || trace.length)} pasi.`,
                    kind: data?.status_kind || "success",
                };
            }
            return {
                text: data?.status_message || "Program terminat.",
                kind: data?.status_kind || "warning",
            };
        }

        return {
            text: `Execut pasul ${safeIndex + 1} din ${trace.length}.`,
            kind: "busy",
        };
    };

    const setRunButtonsDisabled = (disabled) => {
        [runBtn, runStepBtn].forEach((button) => {
            if (!button) {
                return;
            }
            if (disabled) {
                button.setAttribute("disabled", "disabled");
            } else {
                button.removeAttribute("disabled");
            }
        });
    };

    const requestRun = async ({ preludeLines, busyText }) => {
        if (!runUrl || !levelId || !codeInput) {
            return null;
        }

        stopPlayback();
        setStatus(busyText || "Rulez misiunea...", "busy");
        renderConsole(preludeLines || ["Program pornit...", "Simulare in curs..."]);

        setRunButtonsDisabled(true);

        try {
            const response = await fetch(runUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    level_id: levelId,
                    student_code: codeInput.value || "",
                    student_requested_solution: Boolean(requestSolution?.checked),
                }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || data.detail || "Rularea a esuat");
            }

            runnerState.preparedCode = codeInput.value || "";
            runnerState.lastResult = data;
            playback.trace = Array.isArray(data.execution_trace) ? data.execution_trace : [];
            playback.index = -1;
            renderTrace();
            setMentor(data.mentor || {});
            return data;
        } catch (error) {
            const message = `Eroare: ${error.message}`;
            setStatus(message, "error");
            renderConsole(["Programul s-a oprit inainte de executie.", message]);
            runnerState.preparedCode = "";
            runnerState.lastResult = null;
            playback.trace = [];
            playback.index = -1;
            renderTrace();
            applyTraceIndex(-1);
            return null;
        } finally {
            setRunButtonsDisabled(false);
        }
    };

    const runCode = async () => {
        if (!ensureProgramExists()) {
            return;
        }
        const data = await requestRun({
            preludeLines: ["Program pornit...", "Simulare in curs..."],
            busyText: "Rulez misiunea...",
        });
        if (!data) {
            return;
        }

        const finalIndex = playback.trace.length ? playback.trace.length - 1 : -1;
        applyTraceIndex(finalIndex);
        renderConsole(Array.isArray(data.console_output) ? data.console_output : buildFallbackConsole(data));

        const solved = Boolean(data.solved);
        const kind = data.status_kind || (solved ? "success" : data.error_type === "logic" ? "warning" : "error");
        const statusText =
            data.status_message ||
            (solved
                ? `Misiune finalizata in ${Number(data.steps_used || 0)} pasi.`
                : "Misiunea nu este completa. Verifica consola si indiciile.");
        setStatus(statusText, kind);
    };

    const runSingleStep = async () => {
        if (!codeInput) {
            return;
        }
        if (!ensureProgramExists()) {
            return;
        }

        const currentCode = codeInput.value || "";
        const needsFreshTrace =
            !runnerState.lastResult ||
            runnerState.preparedCode !== currentCode ||
            !playback.trace.length;

        let data = runnerState.lastResult;
        if (needsFreshTrace) {
            data = await requestRun({
                preludeLines: ["Pregatesc executia pas cu pas...", "Analizez traseul robotului..."],
                busyText: "Pregatesc executia pe pasi...",
            });
            if (!data) {
                return;
            }
            if (!playback.trace.length) {
                applyTraceIndex(-1);
                renderConsole(Array.isArray(data.console_output) ? data.console_output : buildFallbackConsole(data));
                const emptyStatus = getStepStatus(data, -1);
                setStatus(emptyStatus.text, emptyStatus.kind);
                return;
            }
            applyTraceIndex(0);
            renderConsole(buildSteppedConsole(data, 0));
            const firstStatus = getStepStatus(data, 0);
            setStatus(firstStatus.text, firstStatus.kind);
            return;
        }

        const nextIndex =
            playback.index >= playback.trace.length - 1
                ? 0
                : Math.min(playback.index + 1, playback.trace.length - 1);
        applyTraceIndex(nextIndex);
        renderConsole(buildSteppedConsole(data, nextIndex));
        const nextStatus = getStepStatus(data, nextIndex);
        setStatus(nextStatus.text, nextStatus.kind);
    };

    const createCommandButton = (command) => {
        const meta = COMMAND_META[command] || {
            label: `${command}()`,
            shortLabel: `${command}()`,
            symbolHtml: `${command}()`,
            kind: "action",
        };
        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn--ghost btn--small robotlab-command-btn";
        if (meta.className) {
            button.classList.add(meta.className);
        }
        if (meta.kind === "direction") {
            button.classList.add("robotlab-command-btn--direction");
        }
        button.dataset.command = command;
        button.title = meta.label;
        button.setAttribute("aria-label", meta.label);
        button.innerHTML = meta.symbolHtml;
        button.addEventListener("click", () => {
            appendCommand(command);
            setStatus(`Adaugat ${meta.label}.`, "idle");
        });
        return button;
    };

    const renderBuilderControls = () => {
        if (!builderPanel) {
            return;
        }
        builderPanel.hidden = !stageConfig.showBuilder;
        if (!stageConfig.showBuilder) {
            return;
        }

        const directionCommands = ["up", "left", "right", "down"].filter((command) => allowedApi.includes(command));
        const extraActionCommands = allowedApi.filter(
            (command) =>
                !["up", "down", "left", "right", "at_goal", "front_is_clear", "on_item", "near_terminal", "has_item"].includes(command)
        );

        if (directionPad) {
            directionPad.innerHTML = "";
            directionCommands.forEach((command) => {
                directionPad.appendChild(createCommandButton(command));
            });
        }

        if (extraCommands) {
            extraCommands.innerHTML = "";
            extraActionCommands.forEach((command) => {
                extraCommands.appendChild(createCommandButton(command));
            });
        }
    };

    const applyStageUI = () => {
        if (codeLabel) {
            codeLabel.textContent = stageConfig.codeLabel;
        }
        if (codeInput) {
            codeInput.readOnly = Boolean(stageConfig.readOnly);
        }
        renderBuilderControls();
    };

    root.querySelector("[data-playback-step]")?.addEventListener("click", () => {
        if (!playback.trace.length) {
            return;
        }
        const next = playback.index + 1;
        applyTraceIndex(next >= playback.trace.length ? playback.trace.length - 1 : next);
    });

    root.querySelector("[data-playback-play]")?.addEventListener("click", () => {
        if (!playback.trace.length || playback.timer) {
            return;
        }
        playback.timer = window.setInterval(() => {
            if (playback.index >= playback.trace.length - 1) {
                stopPlayback();
                return;
            }
            applyTraceIndex(playback.index + 1);
        }, 550);
    });

    root.querySelector("[data-playback-pause]")?.addEventListener("click", () => {
        stopPlayback();
    });

    root.querySelector("[data-playback-reset]")?.addEventListener("click", () => {
        applyTraceIndex(-1);
        setStatus("Robotul s-a intors la start.", "idle");
    });

    hintButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const type = button.dataset.hintType;
            if (!type) {
                return;
            }
            openHintModal(type);
        });
    });

    hintCloseButtons.forEach((button) => {
        button.addEventListener("click", () => {
            closeHintModal();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeHintModal();
        }
    });

    runBtn?.addEventListener("click", () => {
        runCode();
    });

    runStepBtn?.addEventListener("click", () => {
        runSingleStep();
    });

    resetCodeBtn?.addEventListener("click", () => {
        resetCode();
    });

    clearCodeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            clearProgram();
        });
    });

    codeInput?.addEventListener("input", () => {
        runnerState.preparedCode = "";
        runnerState.lastResult = null;
        if (stageConfig.showBuilder) {
            syncProgramFromCode();
        }
    });

    if (uiStage === "buttons" || uiStage === "buttons_code") {
        if (codeInput && !codeInput.value.trim() && starterCode) {
            codeInput.value = starterCode;
        }
        syncProgramFromCode();
    } else {
        if (codeInput && !codeInput.value.trim() && starterCode) {
            codeInput.value = starterCode;
        }
        syncProgramFromCode();
    }

    applyStageUI();
    resetPlayback();
    renderConsole([stageConfig.emptyConsole]);
    setStatus("Pregatit.", "idle");
    updateSolutionHintButton();
})();
