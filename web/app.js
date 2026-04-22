const messageInput = document.getElementById("messageInput");
const filePathInput = document.getElementById("filePathInput");
const fileContentInput = document.getElementById("fileContentInput");
const fileScanButton = document.getElementById("fileScanButton");
const stagedScanButton = document.getElementById("stagedScanButton");

function debounce(fn, delay) {
  let timerId;
  return (...args) => {
    window.clearTimeout(timerId);
    timerId = window.setTimeout(() => fn(...args), delay);
  };
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

function setStatusBadge(elementId, state, label) {
  const badge = document.getElementById(elementId);
  badge.className = `status-pill ${state}`;
  badge.textContent = label;
}

function renderList(elementId, items, tone, emptyText) {
  const list = document.getElementById(elementId);
  list.innerHTML = "";

  if (!items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = emptyText;
    list.appendChild(li);
    return;
  }

  for (const item of items) {
    const li = document.createElement("li");
    li.className = tone;
    li.textContent = item;
    list.appendChild(li);
  }
}

function renderCheckList(elementId, checks) {
  const list = document.getElementById(elementId);
  list.innerHTML = "";

  for (const check of checks) {
    const li = document.createElement("li");
    li.className = check.passed ? "ok" : "bad";
    li.textContent = `${check.passed ? "Pass" : "Fail"} - ${check.label}`;
    list.appendChild(li);
  }
}

async function refreshMessageValidation() {
  const data = await postJson("/api/validate-message", {
    message: messageInput.value,
  });

  setStatusBadge(
    "messageBadge",
    data.is_valid ? "valid" : "invalid",
    data.is_valid ? "Valid" : "Invalid",
  );

  document.getElementById("subjectLength").textContent = `${data.subject_length} chars`;
  document.getElementById("commitType").textContent = data.parsed.type || "-";
  document.getElementById("commitScope").textContent = data.parsed.scope || "-";
  document.getElementById("breakingFlag").textContent = data.parsed.breaking ? "Yes" : "No";

  renderCheckList("messageChecks", data.checks);
  renderList("messageErrors", data.errors, "bad", "No blocking errors.");
}

async function refreshFileScan() {
  const data = await postJson("/api/scan-content", {
    path: filePathInput.value,
    content: fileContentInput.value,
  });

  setStatusBadge(
    "fileBadge",
    data.is_valid ? "valid" : "invalid",
    data.is_valid ? "Clean" : "Blocked",
  );

  document.getElementById("fileLines").textContent = String(data.line_count);
  document.getElementById("fileSize").textContent = `${data.size_kb} KB`;

  renderList("fileErrors", data.errors, "bad", "No blocking issues.");
  renderList("fileWarnings", data.warnings, "warn", "No warnings.");
}

async function refreshStagedReport() {
  const data = await getJson("/api/staged-report");
  const fileCount = data.files.length;
  const summary = fileCount
    ? `${fileCount} staged file${fileCount === 1 ? "" : "s"} checked`
    : "No staged files found right now.";

  document.getElementById("stagedSummary").textContent = summary;
  renderList("stagedFiles", data.files, "ok", "Nothing is currently staged.");
  renderList("stagedErrors", data.errors, "bad", "No blocking issues.");
  renderList("stagedWarnings", data.warnings, "warn", "No warnings.");
}

const debouncedMessageRefresh = debounce(() => {
  refreshMessageValidation().catch((error) => {
    setStatusBadge("messageBadge", "invalid", "Error");
    renderList("messageErrors", [error.message], "bad", "No blocking errors.");
  });
}, 220);

const debouncedFileRefresh = debounce(() => {
  refreshFileScan().catch((error) => {
    setStatusBadge("fileBadge", "invalid", "Error");
    renderList("fileErrors", [error.message], "bad", "No blocking issues.");
  });
}, 220);

messageInput.addEventListener("input", debouncedMessageRefresh);
filePathInput.addEventListener("input", debouncedFileRefresh);
fileContentInput.addEventListener("input", debouncedFileRefresh);
fileScanButton.addEventListener("click", () => refreshFileScan());
stagedScanButton.addEventListener("click", () => refreshStagedReport());

refreshMessageValidation();
refreshFileScan();
refreshStagedReport();
