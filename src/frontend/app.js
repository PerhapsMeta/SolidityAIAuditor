// ── Line number sync ──
const codeInput = document.getElementById('code-input');
const lineNums  = document.getElementById('line-nums');
const lineCount = document.getElementById('line-count');
const fileInput = document.getElementById('file-input');
const fileLabel = document.getElementById('file-label');
const uploadHint = document.getElementById('upload-hint');
const API_URL = 'http://127.0.0.1:8000/api/audit';
const MAX_CODE_LENGTH = 200000;
const SOLIDITY_PRAGMA_PATTERN = /\bpragma\s+solidity\s+[^;]+;/i;

function updateLineNums() {
  const lines = codeInput.value.split('\n').length;
  lineCount.textContent = lines + (lines === 1 ? ' line' : ' lines');
  let html = '';
  for (let i = 1; i <= lines; i++) html += i + '<br>';
  lineNums.innerHTML = html;
}

codeInput.addEventListener('scroll', () => { lineNums.scrollTop = codeInput.scrollTop; });
updateLineNums();
fileInput.addEventListener('change', handleFileSelection);

function triggerFilePicker() {
  // Clear the input so selecting the same file again still triggers `change`.
  fileInput.value = '';
  fileInput.click();
}

function resetAnalysisState() {
  resetPanels();
  document.getElementById('empty-state').style.display = 'flex';
  document.getElementById('result-dot').style.background = 'var(--border2)';
  document.getElementById('scan-badge').textContent = '';
  document.getElementById('prog-fill').style.width = '0';
  document.getElementById('prog-label').textContent = 'Initializing scanner...';
  document.getElementById('score-headline').textContent = '—';
  document.getElementById('score-sub').textContent = '—';
  document.getElementById('cnt-high').textContent = '0';
  document.getElementById('cnt-med').textContent = '0';
  document.getElementById('cnt-low').textContent = '0';
  document.getElementById('vuln-list').innerHTML = '';
}

async function handleFileSelection(event) {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }

  if (!file.name.toLowerCase().endsWith('.sol')) {
    clearAll();
    showErrorState(
      'The submitted content could not be analyzed as a Solidity contract. Please check the source code and try again.',
      [{ field: 'file', code: 'invalid_file_type', message: 'Upload a file with the .sol extension.' }],
      'Invalid contract input'
    );
    return;
  }

  try {
    codeInput.value = '';
    updateLineNums();
    const text = await file.text();
    resetAnalysisState();
    codeInput.value = text;
    fileLabel.textContent = file.name;
    uploadHint.textContent = `${file.name} loaded successfully`;
    updateLineNums();
  } catch (_err) {
    clearAll();
    showErrorState(
      'The submitted content could not be analyzed as a Solidity contract. Please check the source code and try again.',
      [{ field: 'file', code: 'file_read_failed', message: 'The selected file could not be read.' }],
      'Invalid contract input'
    );
  }
}

function resetPanels() {
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('loading-state').classList.remove('show');
  document.getElementById('result-state').classList.remove('show');
  document.getElementById('error-state').classList.remove('show');
}

function renderErrorDetails(details = []) {
  const container = document.getElementById('error-details');
  container.innerHTML = '';

  if (!details.length) {
    return;
  }

  details.forEach(detail => {
    const item = document.createElement('div');
    item.className = 'error-detail-item';
    item.innerHTML = `
      <span class="error-detail-field">${escHtml(detail.field || 'detail')}</span>
      <div class="error-detail-text">${escHtml(detail.message || 'Unknown error')}</div>
    `;
    container.appendChild(item);
  });
}

function buildUnifiedError(details = [], overrides = {}) {
  return {
    title: overrides.title || 'Invalid contract input',
    message: overrides.message || 'The submitted content could not be analyzed as a Solidity contract. Please check the source code and try again.',
    details,
  };
}

function showErrorState(message, details = [], title = 'Analysis failed') {
  resetPanels();
  document.getElementById('analyze-btn').disabled = false;
  document.getElementById('result-dot').style.background = 'var(--red)';
  document.getElementById('scan-badge').textContent = 'Request failed';
  document.getElementById('error-title').textContent = title;
  document.getElementById('error-message').textContent = message;
  renderErrorDetails(details);
  document.getElementById('error-state').classList.add('show');
}

function localValidationMessage(code) {
  if (!code) {
    return buildUnifiedError([
      { field: 'code', code: 'empty_contract_code', message: 'The contract source is required.' }
    ]);
  }

  if (code.length > MAX_CODE_LENGTH) {
    return buildUnifiedError([
      { field: 'code', code: 'contract_code_too_long', message: `Contract code must be ${MAX_CODE_LENGTH.toLocaleString()} characters or fewer.` }
    ]);
  }

  const trimmed = code.trim();
  const lower = trimmed.toLowerCase();

  const obviousNonSolidityPatterns = [
    {
      match: lower.includes('<!doctype html') || lower.includes('<html') || lower.includes('<body'),
      message: 'Paste a .sol contract source instead of a web page or HTML template.'
    },
    {
      match: lower.includes('function startanalysis()') || lower.includes('document.getelementbyid(') || lower.includes('const api_url'),
      message: 'Paste Solidity source code instead of JavaScript frontend code.'
    },
    {
      match: lower.includes('def ') || lower.includes('import os') || lower.includes('from fastapi import') || lower.includes('print('),
      message: 'Paste Solidity source code instead of Python code.'
    },
    {
      match: lower.includes('{') && lower.includes('"') && !lower.includes('pragma solidity') && !lower.includes('contract '),
      message: 'Paste Solidity source code instead of JSON or configuration content.'
    },
    {
      match: lower.includes('#include') || lower.includes('int main(') || lower.includes('std::'),
      message: 'Paste Solidity source code instead of C or C++ source.'
    }
  ];

  const detectedNonSolidity = obviousNonSolidityPatterns.find(pattern => pattern.match);
  if (detectedNonSolidity) {
    return buildUnifiedError([
      { field: 'code', code: 'invalid_solidity_source', message: detectedNonSolidity.message }
    ]);
  }

  if (!SOLIDITY_PRAGMA_PATTERN.test(trimmed)) {
    return buildUnifiedError([
      { field: 'code', code: 'invalid_solidity_source', message: "Include a Solidity pragma with a version, such as 'pragma solidity ^0.8.20;'." }
    ]);
  }

  return null;
}

function normalizeApiError(status, payload) {
  if (payload?.error) {
    if (status === 422) {
      return buildUnifiedError(payload.error.details || []);
    }

    return {
      title: 'Analysis failed',
      message: payload.error.message || `Request failed with status ${status}.`,
      details: payload.error.details || [],
    };
  }

  if (status === 422) {
    const details = (payload?.detail || []).map(item => ({
      field: Array.isArray(item.loc) ? item.loc.join(' -> ') : 'body',
      message: item.msg || 'Invalid request.',
    }));

    return buildUnifiedError(details);
  }

  return {
    title: 'Analysis failed',
    message: `Request failed with status ${status}.`,
    details: [],
  };
}

// ── Analysis flow ──
async function startAnalysis() {
  const code = codeInput.value.trim();
  const localError = localValidationMessage(code);
  if (localError) {
    codeInput.focus();
    showErrorState(localError.message, localError.details, localError.title);
    return;
  }

  // Switch to loading state
  resetPanels();
  document.getElementById('loading-state').classList.add('show');
  document.getElementById('analyze-btn').disabled = true;
  document.getElementById('result-dot').style.background = 'var(--amber)';
  document.getElementById('scan-badge').textContent = 'Scanning...';

  // Progress animation
  const steps = 
  [
    { pct: 15,  label: 'Parsing AST...' },
    { pct: 35,  label: 'Scanning reentrancy patterns...' },
    { pct: 55,  label: 'Checking access controls...' },
    { pct: 75,  label: 'Analyzing data flows...' },
    { pct: 90,  label: 'Computing risk score...' },
    { pct: 100, label: 'Done.' }
  ];

  let i = 0;
  const fill  = document.getElementById('prog-fill');
  const label = document.getElementById('prog-label');

  const tick = setInterval(() => {
    if (i < steps.length) {
      fill.style.width  = steps[i].pct + '%';
      label.textContent = steps[i].label;
      i++;
    } else {
      clearInterval(tick);
    }
  }, 280);

  try
  {
    const response = await fetch(API_URL,
    {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({code})
    });

    let data = null;
    try {
      data = await response.json();
    } catch (_err) {
      data = null;
    }

    if (!response.ok) {
      const apiError = normalizeApiError(response.status, data);
      throw apiError;
    }

    clearInterval(tick);
    fill.style.width = '100%';
    label.textContent = 'Done.';

    setTimeout(()=>showResults(data), 300);
  }
  catch(err)
  {
    clearInterval(tick);
    const isNetworkError = err instanceof TypeError;
    const title = err.title || (isNetworkError ? 'Backend unavailable' : 'Analysis failed');
    const message = err.message || 'Unexpected error.';
    const details = err.details || (
      isNetworkError
        ? [{ field: 'network', message: 'Could not reach http://127.0.0.1:8000. Make sure the backend server is running.' }]
        : []
    );

    label.textContent = isNetworkError ? 'Backend unreachable.' : message;
    showErrorState(message, details, title);
  }
}

// ── Render results ──
function showResults(data) {
  document.getElementById('loading-state').classList.remove('show');
  document.getElementById('result-state').classList.add('show');
  document.getElementById('analyze-btn').disabled = false;

  const vulns = (data.issues || []).map(issue => ({
    severity: issue.severity.toLowerCase(), 
    name:     issue.title,
    line:     issue.affected_part,
    explain:  issue.description,
    fix:      issue.fix_recommendation,
  }));

  // Color + copy
  const highCnt  = vulns.filter(v => v.severity === 'high').length;
  const medCnt   = vulns.filter(v => v.severity === 'medium').length;
  const lowCnt   = vulns.filter(v => v.severity === 'low').length;
  const color    = highCnt > 0 ? 'var(--red)' : medCnt > 0 ? 'var(--amber)' : 'var(--green)';
  const headline = highCnt > 0 ? 'High-risk issues detected'
                 : medCnt > 0 ? 'Medium-risk issues detected'
                 : vulns.length > 0 ? 'Low-risk issues detected'
                                  : 'No issues detected';

  // Summary text
  document.getElementById('score-headline').textContent = headline;
  document.getElementById('score-sub').textContent =
    data.summary || `${vulns.length} vulnerabilities detected.`;

  // Counts
  document.getElementById('cnt-high').textContent = highCnt;
  document.getElementById('cnt-med').textContent  = medCnt;
  document.getElementById('cnt-low').textContent  = lowCnt;

  // Status dot
  document.getElementById('result-dot').style.background = color;
  document.getElementById('scan-badge').textContent = data.meta?.ai_succeeded
    ? 'AI + rules completed'
    : data.meta?.ai_enabled
      ? 'Rule-based fallback used'
      : 'AI not configured';

  // Vulnerability list
  const list = document.getElementById('vuln-list');
  list.innerHTML = '';

  vulns.forEach((v, idx) => {
    const item = document.createElement('div');
    item.className = 'vuln-item';
    item.innerHTML = `
      <div class="vuln-row" onclick="toggleDetail(${idx})">
        <div class="sev-bar ${v.severity}"></div>
        <div class="vuln-meta">
          <div class="vuln-name">${v.name}</div>
          <div class="vuln-line">${v.line}</div>
        </div>
        <span class="sev-badge ${v.severity}">${v.severity}</span>
        <svg class="chevron-icon" id="chev-${idx}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m9 18 6-6-6-6"/>
        </svg>
      </div>
      <div class="vuln-detail" id="detail-${idx}">
        <div class="detail-tabs">
          <button class="dtab active" onclick="switchTab(event,${idx},'explain')">Explanation</button>
          <button class="dtab"        onclick="switchTab(event,${idx},'fix')">Fix suggestion</button>
        </div>
        <div class="dtab-pane active" id="pane-explain-${idx}">
          <p class="explain-text">${v.explain}</p>
        </div>
        <div class="dtab-pane" id="pane-fix-${idx}">
          <div class="code-block">${escHtml(v.fix)}</div>
        </div>
      </div>`;
    list.appendChild(item);
  });
}

// ── Toggle vulnerability detail drawer ──
function toggleDetail(idx) {
  const detail = document.getElementById(`detail-${idx}`);
  const chev   = document.getElementById(`chev-${idx}`);
  const isOpen = detail.classList.contains('open');

  // Close all others
  document.querySelectorAll('.vuln-detail').forEach(d => d.classList.remove('open'));
  document.querySelectorAll('.chevron-icon').forEach(c => c.classList.remove('open'));

  if (!isOpen) {
    detail.classList.add('open');
    chev.classList.add('open');
  }
}

// ── Switch detail tab ──
function switchTab(e, idx, tab) {
  e.stopPropagation();
  document.querySelectorAll(`#detail-${idx} .dtab`).forEach(t => t.classList.remove('active'));
  document.querySelectorAll(`#detail-${idx} .dtab-pane`).forEach(p => p.classList.remove('active'));
  e.target.classList.add('active');
  document.getElementById(`pane-${tab}-${idx}`).classList.add('active');
}

// ── Clear all ──
function clearAll() {
  codeInput.value = '';
  fileInput.value = '';
  fileLabel.textContent = 'No file selected';
  uploadHint.textContent = 'Select a Solidity source file to preview and analyze';
  updateLineNums();
  resetAnalysisState();
  document.getElementById('analyze-btn').disabled = false;
}

// ── Utility ──
function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
