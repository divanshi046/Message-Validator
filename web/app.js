const ALLOWED_TYPES = [
  "feat",
  "fix",
  "docs",
  "style",
  "refactor",
  "test",
  "chore",
  "perf",
  "ci",
  "build",
  "revert",
];

const AUTO_ALLOWED_PREFIXES = ["Merge ", "Revert ", "fixup! ", "squash! "];
const HEADER_PATTERN =
  /^(?<type>[a-z]+)(?:\((?<scope>[a-z0-9._/-]+)\))?(?<breaking>!)?: (?<description>.+)$/;
const DEBUG_PATTERNS = [
  /\bprint\s*\(/,
  /\bconsole\.log\s*\(/,
  /\bdebugger\b/,
  /\bpdb\.set_trace\s*\(/,
];
const CONFLICT_MARKERS = ["<<<<<<<", "=======", ">>>>>>>"];
const MAX_SUBJECT_LENGTH = 72;
const MIN_DESCRIPTION_LENGTH = 10;
const LARGE_FILE_LIMIT_BYTES = 500 * 1024;

const messageInput = document.getElementById("messageInput");
const filePathInput = document.getElementById("filePathInput");
const fileContentInput = document.getElementById("fileContentInput");
const fileScanButton = document.getElementById("fileScanButton");

function debounce(fn, delay) {
  let timerId;
  return (...args) => {
    window.clearTimeout(timerId);
    timerId = window.setTimeout(() => fn(...args), delay);
  };
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

function validateCommitMessage(message) {
  const strippedMessage = message.replace(/\n+$/g, "");
  if (!strippedMessage.trim()) {
    return {
      is_valid: false,
      errors: ["Commit message cannot be empty."],
      subject: "",
      subject_length: 0,
      line_count: 0,
      auto_allowed: false,
      allowed_types: [...ALLOWED_TYPES],
      parsed: { type: null, scope: null, description: null, breaking: false },
      checks: [],
    };
  }

  const lines = strippedMessage.split("\n");
  const subject = lines[0].trim();
  const autoAllowed = AUTO_ALLOWED_PREFIXES.some((prefix) => subject.startsWith(prefix));
  const match = subject.match(HEADER_PATTERN);
  const groups = match?.groups ?? {};
  const commitType = groups.type ?? null;
  const scope = groups.scope ?? null;
  const description = groups.description ?? "";
  const breaking = Boolean(groups.breaking);
  const errors = [];

  if (!autoAllowed && !match) {
    errors.push("Use Conventional Commits format: <type>(<scope>): <description>.");
    errors.push("Example: feat(auth): add JWT login support");
  } else if (!autoAllowed) {
    if (!ALLOWED_TYPES.includes(commitType)) {
      errors.push(
        `Unknown commit type '${commitType}'. Allowed types: ${ALLOWED_TYPES.join(", ")}.`,
      );
    }

    if (subject.length > MAX_SUBJECT_LENGTH) {
      errors.push(
        `Subject line is too long (${subject.length} characters). Keep it within 72 characters.`,
      );
    }

    if (description.length < MIN_DESCRIPTION_LENGTH) {
      errors.push(
        `Description is too short. Use at least ${MIN_DESCRIPTION_LENGTH} characters.`,
      );
    }

    if (description && description[0] !== description[0].toLowerCase()) {
      errors.push("Description must start with a lowercase letter.");
    }

    if (description.endsWith(".")) {
      errors.push("Description must not end with a period.");
    }
  }

  if (lines.length > 1 && lines[1].trim()) {
    errors.push("Add a blank line between the subject and the body.");
  }

  const checks = [
    {
      label: "Matches Conventional Commits header format",
      passed: autoAllowed || Boolean(match),
    },
    {
      label: "Uses an allowed commit type",
      passed: autoAllowed || (commitType ? ALLOWED_TYPES.includes(commitType) : false),
    },
    {
      label: `Subject stays within ${MAX_SUBJECT_LENGTH} characters`,
      passed: subject.length <= MAX_SUBJECT_LENGTH,
    },
    {
      label: `Description is at least ${MIN_DESCRIPTION_LENGTH} characters`,
      passed: autoAllowed || description.length >= MIN_DESCRIPTION_LENGTH,
    },
    {
      label: "Description starts with lowercase",
      passed: autoAllowed || (description ? description[0] === description[0].toLowerCase() : false),
    },
    {
      label: "Description does not end with a period",
      passed: autoAllowed || (description ? !description.endsWith(".") : false),
    },
    {
      label: "Body is separated from the subject by a blank line",
      passed: lines.length <= 1 || !lines[1].trim(),
    },
  ];

  return {
    is_valid: errors.length === 0,
    errors,
    subject,
    subject_length: subject.length,
    line_count: lines.length,
    auto_allowed: autoAllowed,
    allowed_types: [...ALLOWED_TYPES],
    parsed: {
      type: commitType,
      scope,
      description: description || null,
      breaking,
    },
    checks,
  };
}

function scanContent(path, content) {
  const normalizedPath = path.trim() || "demo.txt";
  const errors = [];
  const warnings = [];
  const lines = content.split(/\r?\n/);
  const bytes = new TextEncoder().encode(content);

  if (bytes.length > LARGE_FILE_LIMIT_BYTES) {
    warnings.push(
      `${normalizedPath} is large (${(bytes.length / 1024).toFixed(
        1,
      )} KB). Consider avoiding large files in commits.`,
    );
  }

  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    const stripped = line.trim();

    if (CONFLICT_MARKERS.some((marker) => line.startsWith(marker))) {
      errors.push(`${normalizedPath}:${lineNumber} contains a merge conflict marker.`);
    }

    if (/[ \t]+$/.test(line)) {
      errors.push(`${normalizedPath}:${lineNumber} contains trailing whitespace.`);
    }

    if (DEBUG_PATTERNS.some((pattern) => pattern.test(line))) {
      warnings.push(`${normalizedPath}:${lineNumber} contains a debug statement: ${stripped}`);
    }
  });

  return {
    is_valid: errors.length === 0,
    errors,
    warnings,
    path: normalizedPath,
    line_count: content ? lines.length : 0,
    size_bytes: bytes.length,
    size_kb: (bytes.length / 1024).toFixed(2),
  };
}

function refreshMessageValidation() {
  const data = validateCommitMessage(messageInput.value);

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

function refreshFileScan() {
  const data = scanContent(filePathInput.value, fileContentInput.value);

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

function renderHostedModeCard() {
  renderList(
    "hostedCapabilities",
    [
      "Commit message rules run entirely in your browser.",
      "File content scanning for conflict markers, trailing whitespace, and debug statements works on GitHub Pages.",
      "The hosted site cannot inspect your local staged files or your Git index.",
    ],
    "ok",
    "No hosted capabilities listed.",
  );
  renderList(
    "hostedNotes",
    [
      "Use the Git hooks in this repository when you want real staged-file validation during commits.",
      "Use the local Python preview only if you want the repository-aware staged scan.",
    ],
    "warn",
    "No notes available.",
  );
}

const debouncedMessageRefresh = debounce(refreshMessageValidation, 180);
const debouncedFileRefresh = debounce(refreshFileScan, 180);

messageInput.addEventListener("input", debouncedMessageRefresh);
filePathInput.addEventListener("input", debouncedFileRefresh);
fileContentInput.addEventListener("input", debouncedFileRefresh);
fileScanButton.addEventListener("click", refreshFileScan);

refreshMessageValidation();
refreshFileScan();
renderHostedModeCard();
