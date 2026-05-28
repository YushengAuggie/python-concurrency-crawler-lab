const durations = [4, 3, 5, 2, 4];
const crawlStates = [
  { discovered: ["/"], queued: ["/"], running: [], fetched: [] },
  { discovered: ["/"], queued: [], running: ["/"], fetched: [] },
  {
    discovered: ["/", "/tutorial", "/reference"],
    queued: ["/tutorial", "/reference"],
    running: [],
    fetched: ["/"],
  },
  {
    discovered: ["/", "/tutorial", "/reference"],
    queued: [],
    running: ["/tutorial", "/reference"],
    fetched: ["/"],
  },
  {
    discovered: [
      "/",
      "/tutorial",
      "/reference",
      "/examples/basic",
      "/examples/concurrent",
    ],
    queued: ["/examples/basic", "/examples/concurrent"],
    running: ["/tutorial"],
    fetched: ["/", "/reference"],
  },
  {
    discovered: [
      "/",
      "/tutorial",
      "/reference",
      "/examples/basic",
      "/examples/concurrent",
    ],
    queued: ["/examples/concurrent"],
    running: ["/tutorial", "/examples/basic"],
    fetched: ["/", "/reference"],
  },
  {
    discovered: [
      "/",
      "/tutorial",
      "/reference",
      "/examples/basic",
      "/examples/concurrent",
    ],
    queued: ["/examples/concurrent"],
    running: [],
    fetched: ["/", "/reference", "/tutorial", "/examples/basic"],
  },
  {
    discovered: [
      "/",
      "/tutorial",
      "/reference",
      "/examples/basic",
      "/examples/concurrent",
    ],
    queued: [],
    running: ["/examples/concurrent"],
    fetched: ["/", "/reference", "/tutorial", "/examples/basic"],
  },
  {
    discovered: [
      "/",
      "/tutorial",
      "/reference",
      "/examples/basic",
      "/examples/concurrent",
    ],
    queued: [],
    running: [],
    fetched: [
      "/",
      "/reference",
      "/tutorial",
      "/examples/basic",
      "/examples/concurrent",
    ],
  },
];

function renderTimeline() {
  const slider = document.querySelector("#concurrency");
  const timeline = document.querySelector("#timeline");
  const metric = document.querySelector("#elapsed");
  const insight = document.querySelector("#timeline-insight");
  if (!slider || !timeline || !metric) {
    return;
  }

  const concurrency = Number(slider.value);
  const lab = document.querySelector(".timeline-lab");
  const slotLabel = lab.dataset.slotLabel;
  const pageLabel = lab.dataset.pageLabel;
  const timeLabel = lab.dataset.timeLabel;
  document.querySelector("#concurrency-value").textContent = concurrency;

  const availableAt = Array(concurrency).fill(0);
  const scheduled = durations.map((duration, index) => {
    const worker = availableAt.indexOf(Math.min(...availableAt));
    const startsAt = availableAt[worker];
    availableAt[worker] += duration;
    return { name: `${pageLabel} ${index + 1}`, duration, startsAt, worker };
  });
  const totalTime = Math.max(...availableAt);

  timeline.textContent = "";
  for (let worker = 0; worker < concurrency; worker += 1) {
    const lane = document.createElement("div");
    lane.className = "lane";
    lane.innerHTML = `<span class="lane-label">${slotLabel} ${worker + 1}</span>`;
    const track = document.createElement("div");
    track.className = "track";

    scheduled
      .filter((request) => request.worker === worker)
      .forEach((request) => {
        const bar = document.createElement("div");
        bar.className = "request";
        bar.title = `${request.name}: ${request.duration} ticks`;
        bar.style.left = `${(request.startsAt / totalTime) * 100}%`;
        bar.style.width = `${(request.duration / totalTime) * 100}%`;
        track.appendChild(bar);
      });

    lane.appendChild(track);
    timeline.appendChild(lane);
  }

  metric.textContent = `${totalTime} ${timeLabel}`;
  if (insight) {
    insight.textContent = lab.dataset.insight
      .replace("{concurrency}", String(concurrency))
      .replace("{total}", String(totalTime));
  }
}

function wireQuizzes() {
  document.querySelectorAll(".quiz").forEach((quiz) => {
    const feedback = quiz.querySelector(".feedback");
    quiz.querySelectorAll(".choice").forEach((button) => {
      button.addEventListener("click", () => {
        quiz.querySelectorAll(".choice").forEach((choice) => {
          choice.classList.remove("correct", "incorrect");
        });

        if (button.dataset.correct === "true") {
          button.classList.add("correct");
          feedback.textContent = quiz.dataset.success;
        } else {
          button.classList.add("incorrect");
          feedback.textContent = quiz.dataset.retry;
        }
      });
    });
  });
}

function wireCodeStudio() {
  const tabs = Array.from(document.querySelectorAll(".code-tab"));
  const panels = document.querySelectorAll(".code-panel");

  const selectTab = (tab, focus = false) => {
    tabs.forEach((candidate) => {
      const active = candidate === tab;
      candidate.classList.toggle("active", active);
      candidate.setAttribute("aria-selected", String(active));
      candidate.tabIndex = active ? 0 : -1;
    });

    panels.forEach((panel) => {
      const active = panel.dataset.codePanel === tab.dataset.codeTarget;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
    if (focus) {
      tab.focus();
    }
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => selectTab(tab));
    tab.addEventListener("keydown", (event) => {
      const direction = {
        ArrowRight: 1,
        ArrowLeft: -1,
      }[event.key];
      let nextIndex;
      if (direction) {
        nextIndex = (index + direction + tabs.length) % tabs.length;
      } else if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = tabs.length - 1;
      } else {
        return;
      }
      event.preventDefault();
      selectTab(tabs[nextIndex], true);
    });
  });
}

function wireSourceBrowser() {
  const browser = document.querySelector(".source-browser");
  const treeButtons = Array.from(document.querySelectorAll("[data-source-path]"));
  const code = document.querySelector("#source-code");
  const meta = document.querySelector("#source-meta");
  const focus = document.querySelector("#source-focus");
  const sourceLink = document.querySelector("#source-github-link");
  const sourceFiles = window.CRAWLER_SOURCE_FILES || {};
  if (!browser || !treeButtons.length || !code || !meta || !focus) {
    return;
  }

  const pythonKeywords = new Set([
    "and",
    "as",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
  ]);
  const pythonConstants = new Set(["False", "None", "True"]);
  const pythonBuiltins = new Set([
    "ConnectionError",
    "Future",
    "RuntimeError",
    "ThreadPoolExecutor",
    "ValueError",
    "bool",
    "dict",
    "float",
    "int",
    "list",
    "print",
    "set",
    "str",
    "tuple",
  ]);

  const parseHighlightedLines = (highlightText) => {
    const highlightedLines = new Set();
    highlightText
      .split(",")
      .map((range) => range.trim())
      .filter(Boolean)
      .forEach((range) => {
        const [startText, endText] = range.split("-");
        const startLine = Number(startText);
        const endLine = Number(endText || startText);
        for (let line = startLine; line <= endLine; line += 1) {
          highlightedLines.add(line);
        }
      });
    return highlightedLines;
  };

  const appendToken = (container, text, className = "") => {
    if (!text) {
      return;
    }
    const token = document.createElement("span");
    if (className) {
      token.className = className;
    }
    token.textContent = text;
    container.appendChild(token);
  };

  const appendHighlightedPython = (container, lineText, state) => {
    let position = 0;

    while (position < lineText.length) {
      if (state.tripleQuote) {
        const end = lineText.indexOf(state.tripleQuote, position);
        if (end === -1) {
          appendToken(container, lineText.slice(position), "token-string");
          return;
        }

        appendToken(
          container,
          lineText.slice(position, end + state.tripleQuote.length),
          "token-string",
        );
        position = end + state.tripleQuote.length;
        state.tripleQuote = "";
        continue;
      }

      const character = lineText[position];
      const tripleQuote = lineText.slice(position, position + 3);
      if (tripleQuote === '"""' || tripleQuote === "'''") {
        const end = lineText.indexOf(tripleQuote, position + 3);
        if (end === -1) {
          appendToken(container, lineText.slice(position), "token-string");
          state.tripleQuote = tripleQuote;
          return;
        }

        appendToken(
          container,
          lineText.slice(position, end + 3),
          "token-string",
        );
        position = end + 3;
        continue;
      }

      if (character === "#") {
        appendToken(container, lineText.slice(position), "token-comment");
        return;
      }

      if (character === '"' || character === "'") {
        let end = position + 1;
        while (end < lineText.length) {
          if (lineText[end] === "\\") {
            end += 2;
            continue;
          }
          if (lineText[end] === character) {
            end += 1;
            break;
          }
          end += 1;
        }
        appendToken(container, lineText.slice(position, end), "token-string");
        position = end;
        continue;
      }

      if (/[A-Za-z_]/.test(character)) {
        let end = position + 1;
        while (end < lineText.length && /[A-Za-z0-9_]/.test(lineText[end])) {
          end += 1;
        }
        const word = lineText.slice(position, end);
        let className = "";
        if (pythonKeywords.has(word)) {
          className = "token-keyword";
        } else if (pythonConstants.has(word)) {
          className = "token-constant";
        } else if (pythonBuiltins.has(word)) {
          className = "token-builtin";
        } else if (word === "self") {
          className = "token-self";
        }
        appendToken(container, word, className);
        position = end;
        continue;
      }

      if (/\d/.test(character)) {
        let end = position + 1;
        while (end < lineText.length && /[\d_.]/.test(lineText[end])) {
          end += 1;
        }
        appendToken(container, lineText.slice(position, end), "token-number");
        position = end;
        continue;
      }

      appendToken(container, character);
      position += 1;
    }
  };

  const renderCodeLines = (sourceText, highlightedLines) => {
    code.textContent = "";
    const sourceLines = sourceText.endsWith("\n")
      ? sourceText.slice(0, -1).split("\n")
      : sourceText.split("\n");
    const syntaxState = { tripleQuote: "" };
    sourceLines.forEach((lineText, index) => {
      const lineNumber = index + 1;
      const row = document.createElement("span");
      row.className = "source-line";
      if (highlightedLines.has(lineNumber)) {
        row.classList.add("highlighted");
      }

      const gutter = document.createElement("span");
      gutter.className = "source-line-number";
      gutter.textContent = String(lineNumber);

      const line = document.createElement("span");
      line.className = "source-line-code";
      if (lineText) {
        appendHighlightedPython(line, lineText, syntaxState);
      } else {
        line.textContent = " ";
      }

      row.append(gutter, line);
      code.appendChild(row);
    });
  };

  const renderSource = (sourcePath, activeHighlight = "") => {
    const selectedButton =
      treeButtons.find((button) => button.dataset.sourcePath === sourcePath) ||
      treeButtons[0];
    const selectedPath = selectedButton.dataset.sourcePath;
    const sourceText = sourceFiles[selectedPath] || "";
    const lineCount = sourceText
      ? sourceText.split("\n").length - (sourceText.endsWith("\n") ? 1 : 0)
      : 0;
    const highlightText = activeHighlight || selectedButton.dataset.highlight || "";
    const highlightedLines = parseHighlightedLines(highlightText);

    treeButtons.forEach((button) => {
      const active = button === selectedButton;
      button.classList.toggle("active", active);
      button.setAttribute("aria-current", active ? "true" : "false");
    });

    if (sourceText) {
      renderCodeLines(sourceText, highlightedLines);
    } else {
      code.textContent = browser.dataset.missing;
    }
    meta.textContent = browser.dataset.meta
      .replace("{file}", selectedPath)
      .replace("{lines}", String(lineCount));
    focus.textContent = selectedButton.dataset.focus || "";
    if (sourceLink) {
      sourceLink.href = `https://github.com/YushengAuggie/python-concurrency-crawler-lab/blob/main/${selectedPath}`;
    }
  };

  treeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      renderSource(button.dataset.sourcePath);
    });
  });
  document.querySelectorAll("[data-source-target]").forEach((jump) => {
    jump.addEventListener("click", () => {
      renderSource(jump.dataset.sourceTarget, jump.dataset.sourceHighlight || "");
    });
  });
  renderSource(treeButtons[0].dataset.sourcePath);
}

function wireLessonLinks() {
  const openLesson = () => {
    if (!window.location.hash) {
      return;
    }
    const target = document.querySelector(window.location.hash);
    if (target instanceof HTMLDetailsElement) {
      target.open = true;
    }
  };

  document.querySelectorAll('a[href^="#lesson-"]').forEach((link) => {
    link.addEventListener("click", () => {
      const target = document.querySelector(link.getAttribute("href"));
      if (target instanceof HTMLDetailsElement) {
        target.open = true;
      }
    });
  });
  openLesson();
  window.addEventListener("hashchange", openLesson);
}

function renderChips(container, values) {
  container.textContent = "";
  values.forEach((value) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    container.appendChild(chip);
  });
}

function wireStateLab() {
  const board = document.querySelector(".state-board");
  const nextButton = document.querySelector("#state-next");
  const resetButton = document.querySelector("#state-reset");
  if (!board || !nextButton || !resetButton) {
    return;
  }

  const eventText = document.querySelector("#state-event");
  let stateIndex = 0;

  const renderState = () => {
    const state = crawlStates[stateIndex];
    renderChips(document.querySelector("#state-discovered"), state.discovered);
    renderChips(document.querySelector("#state-queued"), state.queued);
    renderChips(document.querySelector("#state-running"), state.running);
    renderChips(document.querySelector("#state-fetched"), state.fetched);
    if (stateIndex === 0) {
      eventText.textContent = board.dataset.initial;
    } else if (stateIndex === crawlStates.length - 1) {
      eventText.textContent = `${board.getAttribute(`data-event-${stateIndex}`)} ${board.dataset.finished}`;
    } else {
      eventText.textContent = board.getAttribute(`data-event-${stateIndex}`);
    }
    nextButton.disabled = stateIndex === crawlStates.length - 1;
  };

  nextButton.addEventListener("click", () => {
    stateIndex = Math.min(stateIndex + 1, crawlStates.length - 1);
    renderState();
  });
  resetButton.addEventListener("click", () => {
    stateIndex = 0;
    renderState();
  });
  renderState();
}

function renderResilienceLab() {
  const lab = document.querySelector(".resilience-lab");
  if (!lab) {
    return;
  }

  const timeout = Number(document.querySelector("#timeout-budget").value);
  const latency = Number(document.querySelector("#page-latency").value);
  const failures = Number(document.querySelector("#temporary-failures").value);
  const output = document.querySelector("#resilience-result");
  const chinese = document.documentElement.lang.startsWith("zh");
  document.querySelector("#timeout-value").textContent = timeout;
  document.querySelector("#latency-value").textContent = latency;
  document.querySelector("#failures-value").textContent = failures;
  output.classList.remove("failure");

  if (latency > timeout) {
    output.textContent = lab.dataset.timeout;
    output.classList.add("failure");
    return;
  }

  if (failures >= 3) {
    output.textContent = lab.dataset.exhausted;
    output.classList.add("failure");
    return;
  }

  const successfulAttempt = failures + 1;
  const backoffTicks = failures === 0 ? 0 : (2 ** failures) - 1;
  output.textContent = chinese
    ? `${lab.dataset.success}：第 ${successfulAttempt} 次尝试返回页面；此前 backoff 共 ${backoffTicks} ticks。`
    : `${lab.dataset.success}: attempt ${successfulAttempt} returns the page after ${backoffTicks} backoff ticks.`;
}

document.addEventListener("DOMContentLoaded", () => {
  renderTimeline();
  wireQuizzes();
  wireCodeStudio();
  wireSourceBrowser();
  wireLessonLinks();
  wireStateLab();
  renderResilienceLab();
  const slider = document.querySelector("#concurrency");
  if (slider) {
    slider.addEventListener("input", renderTimeline);
  }
  ["#timeout-budget", "#page-latency", "#temporary-failures"].forEach((selector) => {
    const control = document.querySelector(selector);
    if (control) {
      control.addEventListener("input", renderResilienceLab);
    }
  });
});
