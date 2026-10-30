// Recruiter-Bot Frontend Client Logic

let jobsData = [];
let candidatesData = [];
let selectedJobId = null;
let selectedCandId = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchStats();
  loadJobs();
  loadCandidates();

  document.getElementById("reseedBtn").addEventListener("click", handleReseed);
  document.getElementById("minScoreFilter").addEventListener("change", () => {
    if (selectedJobId) loadJobMatches(selectedJobId);
  });
  document.getElementById("candMinScoreFilter").addEventListener("change", () => {
    if (selectedCandId) loadCandidateMatches(selectedCandId);
  });

  document.getElementById("jobSearchInput").addEventListener("input", filterJobs);
  document.getElementById("candSearchInput").addEventListener("input", filterCandidates);
});

// Tab Switcher
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });
}

// Fetch System Stats
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    if (!res.ok) return;
    const stats = await res.json();
    document.getElementById("candCount").textContent = stats.candidate_count;
    document.getElementById("jobCount").textContent = stats.job_count;
    document.getElementById("matchCount").textContent = stats.match_count;
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

// Reseed Action
async function handleReseed() {
  const btn = document.getElementById("reseedBtn");
  btn.disabled = true;
  btn.innerHTML = `<span class="btn-icon">⏳</span> Reseeding...`;
  try {
    const res = await fetch("/api/seed", { method: "POST" });
    if (res.ok) {
      await fetchStats();
      await loadJobs();
      await loadCandidates();
      if (selectedJobId) loadJobMatches(selectedJobId);
    }
  } catch (err) {
    alert("Reseed failed: " + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-icon">🔄</span> Reseed Data`;
  }
}

// Load Jobs
async function loadJobs() {
  try {
    const res = await fetch("/jobs");
    jobsData = await res.json();
    document.getElementById("jobListCount").textContent = jobsData.length;
    renderJobList(jobsData);
    if (jobsData.length > 0 && !selectedJobId) {
      selectJob(jobsData[0].id);
    }
  } catch (err) {
    console.error("Error loading jobs:", err);
  }
}

function filterJobs(e) {
  const q = e.target.value.toLowerCase();
  const filtered = jobsData.filter(
    (j) => j.title.toLowerCase().includes(q) || j.required_skills.some((s) => s.toLowerCase().includes(q))
  );
  renderJobList(filtered);
}

function renderJobList(jobs) {
  const container = document.getElementById("jobListContainer");
  container.innerHTML = "";
  jobs.forEach((job) => {
    const card = document.createElement("div");
    card.className = `item-card ${job.id === selectedJobId ? "active" : ""}`;
    card.id = `job-card-${job.id}`;
    card.innerHTML = `
      <div class="item-card-title">${escapeHtml(job.title)}</div>
      <div class="item-card-sub">Min Exp: ${job.min_experience_years} yrs • ${job.required_skills.length} skills</div>
    `;
    card.addEventListener("click", () => selectJob(job.id));
    container.appendChild(card);
  });
}

function selectJob(jobId) {
  selectedJobId = jobId;
  document.querySelectorAll("#jobListContainer .item-card").forEach((c) => c.classList.remove("active"));
  const activeCard = document.getElementById(`job-card-${jobId}`);
  if (activeCard) activeCard.classList.add("active");

  const job = jobsData.find((j) => j.id === jobId);
  if (job) renderJobHeader(job);
  loadJobMatches(jobId);
}

function renderJobHeader(job) {
  const header = document.getElementById("jobDetailHeader");
  header.innerHTML = `
    <div class="entity-header-top">
      <div>
        <h2 class="entity-title">${escapeHtml(job.title)}</h2>
        <div class="entity-tagline">“${escapeHtml(job.tagline)}”</div>
      </div>
      <div class="badge">Min Exp: ${job.min_experience_years} Years</div>
    </div>
    <div class="chips-row">
      <span class="chip-label">Required Skills:</span>
      ${job.required_skills.map((s) => `<span class="chip chip-primary">${escapeHtml(s)}</span>`).join("")}
      <span class="chip-label" style="margin-left: 0.75rem;">Culture:</span>
      ${job.culture_keywords.map((k) => `<span class="chip chip-culture">${escapeHtml(k)}</span>`).join("")}
    </div>
  `;
}

async function loadJobMatches(jobId) {
  const listContainer = document.getElementById("jobMatchesList");
  const minScore = document.getElementById("minScoreFilter").value;
  listContainer.innerHTML = `<div class="loading-state">Evaluating candidate matches via Raw SQL...</div>`;

  try {
    const res = await fetch(`/jobs/${jobId}/matches?min_score=${minScore}`);
    const data = await res.json();
    renderCandidateMatches(data.matches);
    fetchStats();
  } catch (err) {
    listContainer.innerHTML = `<div class="loading-state">Failed to load matches: ${err}</div>`;
  }
}

function renderCandidateMatches(matches) {
  const container = document.getElementById("jobMatchesList");
  if (!matches || matches.length === 0) {
    container.innerHTML = `<div class="loading-state">No candidates meet the score filter.</div>`;
    return;
  }
  container.innerHTML = "";

  matches.forEach((item, index) => {
    const rank = index + 1;
    const cand = item.candidate;
    const score = item.score;
    const bd = item.breakdown;

    let tierClass = "tier-top";
    if (score < 50) tierClass = "tier-weak";
    else if (score < 70) tierClass = "tier-low";
    else if (score < 85) tierClass = "tier-mid";

    const availClass =
      cand.availability.toLowerCase().includes("immediate")
        ? "chip-avail-immediate"
        : cand.availability.toLowerCase().includes("2 week")
        ? "chip-avail-notice"
        : "chip-avail-passive";

    const card = document.createElement("div");
    card.className = "match-card";
    card.innerHTML = `
      <div class="match-card-top">
        <div class="match-candidate-info">
          <div class="rank-badge ${rank <= 3 ? "rank-" + rank : ""}">#${rank}</div>
          <div>
            <div class="match-name">${escapeHtml(cand.name)}</div>
            <div class="match-meta-line">
              <span>${cand.experience_years} yrs exp</span>
              <span>•</span>
              <span class="chip ${availClass}" style="padding: 0.1rem 0.4rem; font-size: 0.72rem;">${escapeHtml(cand.availability)}</span>
            </div>
          </div>
        </div>
        <div class="score-pill">
          <span class="score-num ${tierClass}">${score.toFixed(1)}</span>
          <span class="score-label">Overall Match</span>
        </div>
      </div>

      <div class="score-breakdown-bar">
        <div class="breakdown-col">
          <span class="breakdown-label">Skill (50)</span>
          <span class="breakdown-val">${bd.skill_score.toFixed(1)}</span>
        </div>
        <div class="breakdown-col">
          <span class="breakdown-label">Experience (25)</span>
          <span class="breakdown-val">${bd.experience_score.toFixed(1)}</span>
        </div>
        <div class="breakdown-col">
          <span class="breakdown-label">Availability (15)</span>
          <span class="breakdown-val">${bd.availability_score.toFixed(1)}</span>
        </div>
        <div class="breakdown-col">
          <span class="breakdown-label">Culture (10)</span>
          <span class="breakdown-val">${bd.culture_score.toFixed(1)}</span>
        </div>
      </div>

      <div class="match-reason-box">
        <strong>Recruiter Assessment:</strong> ${escapeHtml(item.reason)}
      </div>
    `;
    container.appendChild(card);
  });
}

// Load Candidates (Tab 2)
async function loadCandidates() {
  try {
    const res = await fetch("/candidates");
    candidatesData = await res.json();
    document.getElementById("candListCount").textContent = candidatesData.length;
    renderCandList(candidatesData);
    if (candidatesData.length > 0 && !selectedCandId) {
      selectCandidate(candidatesData[0].id);
    }
  } catch (err) {
    console.error("Error loading candidates:", err);
  }
}

function filterCandidates(e) {
  const q = e.target.value.toLowerCase();
  const filtered = candidatesData.filter(
    (c) => c.name.toLowerCase().includes(q) || c.skills.some((s) => s.toLowerCase().includes(q))
  );
  renderCandList(filtered);
}

function renderCandList(cands) {
  const container = document.getElementById("candListContainer");
  container.innerHTML = "";
  cands.forEach((cand) => {
    const card = document.createElement("div");
    card.className = `item-card ${cand.id === selectedCandId ? "active" : ""}`;
    card.id = `cand-card-${cand.id}`;
    card.innerHTML = `
      <div class="item-card-title">${escapeHtml(cand.name)}</div>
      <div class="item-card-sub">${cand.experience_years} yrs • ${escapeHtml(cand.availability)}</div>
    `;
    card.addEventListener("click", () => selectCandidate(cand.id));
    container.appendChild(card);
  });
}

function selectCandidate(candId) {
  selectedCandId = candId;
  document.querySelectorAll("#candListContainer .item-card").forEach((c) => c.classList.remove("active"));
  const activeCard = document.getElementById(`cand-card-${candId}`);
  if (activeCard) activeCard.classList.add("active");

  const cand = candidatesData.find((c) => c.id === candId);
  if (cand) renderCandidateHeader(cand);
  loadCandidateMatches(candId);
}

function renderCandidateHeader(cand) {
  const header = document.getElementById("candDetailHeader");
  header.innerHTML = `
    <div class="entity-header-top">
      <div>
        <h2 class="entity-title">${escapeHtml(cand.name)}</h2>
        <div class="entity-tagline">“${escapeHtml(cand.quirk)}”</div>
      </div>
      <div class="badge">${cand.experience_years} Years Experience</div>
    </div>
    <div class="chips-row">
      <span class="chip-label">Skills:</span>
      ${cand.skills.map((s) => `<span class="chip chip-primary">${escapeHtml(s)}</span>`).join("")}
      <span class="chip-label" style="margin-left: 0.75rem;">Traits:</span>
      ${cand.traits.map((t) => `<span class="chip chip-culture">${escapeHtml(t)}</span>`).join("")}
      <span class="chip-label" style="margin-left: 0.75rem;">Status:</span>
      <span class="chip">${escapeHtml(cand.availability)}</span>
    </div>
  `;
}

async function loadCandidateMatches(candId) {
  const listContainer = document.getElementById("candMatchesList");
  const minScore = document.getElementById("candMinScoreFilter").value;
  listContainer.innerHTML = `<div class="loading-state">Matching candidate against open jobs...</div>`;

  try {
    const res = await fetch(`/candidates/${candId}/matches?min_score=${minScore}`);
    const data = await res.json();
    renderJobMatchItems(data.matches);
  } catch (err) {
    listContainer.innerHTML = `<div class="loading-state">Failed to load matches: ${err}</div>`;
  }
}

function renderJobMatchItems(matches) {
  const container = document.getElementById("candMatchesList");
  if (!matches || matches.length === 0) {
    container.innerHTML = `<div class="loading-state">No matching roles found above threshold.</div>`;
    return;
  }
  container.innerHTML = "";

  matches.forEach((item, index) => {
    const rank = index + 1;
    const job = item.job;
    const score = item.score;
    const bd = item.breakdown;

    let tierClass = "tier-top";
    if (score < 50) tierClass = "tier-weak";
    else if (score < 70) tierClass = "tier-low";
    else if (score < 85) tierClass = "tier-mid";

    const card = document.createElement("div");
    card.className = "match-card";
    card.innerHTML = `
      <div class="match-card-top">
        <div class="match-candidate-info">
          <div class="rank-badge ${rank <= 3 ? "rank-" + rank : ""}">#${rank}</div>
          <div>
            <div class="match-name">${escapeHtml(job.title)}</div>
            <div class="match-meta-line">
              <span>Min ${job.min_experience_years} yrs exp</span>
              <span>•</span>
              <span>“${escapeHtml(job.tagline)}”</span>
            </div>
          </div>
        </div>
        <div class="score-pill">
          <span class="score-num ${tierClass}">${score.toFixed(1)}</span>
          <span class="score-label">Job Fit</span>
        </div>
      </div>

      <div class="score-breakdown-bar">
        <div class="breakdown-col">
          <span class="breakdown-label">Skill (50)</span>
          <span class="breakdown-val">${bd.skill_score.toFixed(1)}</span>
        </div>
        <div class="breakdown-col">
          <span class="breakdown-label">Experience (25)</span>
          <span class="breakdown-val">${bd.experience_score.toFixed(1)}</span>
        </div>
        <div class="breakdown-col">
          <span class="breakdown-label">Availability (15)</span>
          <span class="breakdown-val">${bd.availability_score.toFixed(1)}</span>
        </div>
        <div class="breakdown-col">
          <span class="breakdown-label">Culture (10)</span>
          <span class="breakdown-val">${bd.culture_score.toFixed(1)}</span>
        </div>
      </div>

      <div class="match-reason-box">
        <strong>Recruiter Assessment:</strong> ${escapeHtml(item.reason)}
      </div>
    `;
    container.appendChild(card);
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
