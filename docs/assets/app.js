const durations = [4, 3, 5, 2, 4];

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

document.addEventListener("DOMContentLoaded", () => {
  renderTimeline();
  wireQuizzes();
  const slider = document.querySelector("#concurrency");
  if (slider) {
    slider.addEventListener("input", renderTimeline);
  }
});
