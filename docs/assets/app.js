const durations = [4, 3, 5, 2, 4];
const crawlStates = [
  { queued: ["/"], running: [], fetched: [] },
  { queued: [], running: ["/"], fetched: [] },
  { queued: ["/tutorial", "/reference"], running: [], fetched: ["/"] },
  { queued: [], running: ["/tutorial", "/reference"], fetched: ["/"] },
  {
    queued: ["/examples/basic", "/examples/concurrent"],
    running: ["/tutorial"],
    fetched: ["/", "/reference"],
  },
  {
    queued: ["/examples/concurrent"],
    running: ["/tutorial", "/examples/basic"],
    fetched: ["/", "/reference"],
  },
  {
    queued: ["/examples/concurrent"],
    running: [],
    fetched: ["/", "/reference", "/tutorial", "/examples/basic"],
  },
  {
    queued: [],
    running: ["/examples/concurrent"],
    fetched: ["/", "/reference", "/tutorial", "/examples/basic"],
  },
  {
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
