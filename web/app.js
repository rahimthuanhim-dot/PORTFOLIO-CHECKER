const tabButtons = [...document.querySelectorAll('[data-tab]')];
const panels = [...document.querySelectorAll('[data-panel]')];
const form = document.querySelector('#match-form');
const profileInput = document.querySelector('#profile-text');
const resumeInput = document.querySelector('#resume-file');
const characterCount = document.querySelector('#character-count');
const matchButton = document.querySelector('#match-button');
const matchError = document.querySelector('#match-error');
const metricsStatus = document.querySelector('#metrics-status');
const metricsContent = document.querySelector('#metrics-content');

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

async function readApiJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.toLowerCase().includes('application/json')) {
    try {
      return await response.json();
    } catch {
      throw new Error('The API returned invalid JSON. Restart or redeploy the FastAPI service and try again.');
    }
  }
  const body = await response.text();
  if (response.status === 413) {
    throw new Error('The server rejected this upload as too large. Try a smaller PDF.');
  }
  if (response.status === 404 || response.status === 405 || /<!doctype html|<html/i.test(body.slice(0, 500))) {
    throw new Error('The page server returned HTML instead of an API response. Deploy or run the FastAPI web service (not a static-only site) so /match/upload and /metrics are available on this same site.');
  }
  throw new Error(`The API returned an unexpected response (HTTP ${response.status}).`);
}

function setTab(name, focus = false) {
  for (const button of tabButtons) {
    const active = button.dataset.tab === name;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
    if (active && focus) button.focus();
  }
  for (const panel of panels) panel.hidden = panel.dataset.panel !== name;
  if (name === 'results') loadMetrics();
}

tabButtons.forEach((button) => button.addEventListener('click', () => setTab(button.dataset.tab)));
document.querySelector('.tab-list').addEventListener('keydown', (event) => {
  if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  const current = tabButtons.findIndex((button) => button.getAttribute('aria-selected') === 'true');
  const next = (current + (event.key === 'ArrowRight' ? 1 : -1) + tabButtons.length) % tabButtons.length;
  setTab(tabButtons[next].dataset.tab, true);
});

profileInput.addEventListener('input', () => {
  characterCount.textContent = `${profileInput.value.length.toLocaleString()} characters`;
});

resumeInput.addEventListener('change', () => {
  const file = resumeInput.files?.[0];
  const selectedFile = document.querySelector('#selected-file');
  if (!file) {
    selectedFile.hidden = true;
    selectedFile.textContent = '';
    return;
  }
  selectedFile.textContent = `Selected resume: ${file.name}`;
  selectedFile.hidden = false;
});

function renderSkills(skills) {
  const container = document.querySelector('#skill-chips');
  document.querySelector('#skill-count').textContent = `${skills.length} ${skills.length === 1 ? 'skill' : 'skills'}`;
  if (!skills.length) {
    container.innerHTML = '<span class="muted">No skills crossed the current matching threshold.</span>';
    return;
  }
  container.innerHTML = skills.map((item) => `
    <span class="skill-chip"><span>${escapeHtml(item.skill)}</span><span class="confidence">${Number(item.confidence).toFixed(2)}</span></span>
  `).join('');
}

function renderInternships(target, internships) {
  const container = document.querySelector(target);
  if (!internships.length) {
    container.innerHTML = '<p class="muted">No internship records were returned.</p>';
    return;
  }
  container.innerHTML = internships.map((item, index) => `
    <details class="internship-card" ${index === 0 ? 'open' : ''}>
      <summary>
        <span class="rank-number">${String(index + 1).padStart(2, '0')}</span>
        <span class="card-main"><span class="card-title">${escapeHtml(item.title)}</span><span class="card-company">${escapeHtml(item.company)}</span></span>
        <span class="score-pill">${Number(item.score).toFixed(3)}</span>
      </summary>
      <div class="card-detail">
        <p class="card-description">${escapeHtml(item.description)}</p>
        <div class="gap-report"><strong>Skill-gap report</strong>${escapeHtml(item.gap_report)}</div>
      </div>
    </details>
  `).join('');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  matchError.hidden = true;
  matchError.textContent = '';
  const profileText = profileInput.value.trim();
  const resumeFile = resumeInput.files?.[0];
  if (!profileText && !resumeFile) {
    matchError.textContent = 'Paste profile text or choose a PDF resume to see matches.';
    matchError.hidden = false;
    profileInput.focus();
    return;
  }
  if (resumeFile && !resumeFile.name.toLocaleLowerCase().endsWith('.pdf')) {
    matchError.textContent = 'Choose a PDF file to scan.';
    matchError.hidden = false;
    resumeInput.focus();
    return;
  }
  if (resumeFile && resumeFile.size > 4 * 1024 * 1024) {
    matchError.textContent = 'This deployment accepts PDF files up to 4 MB. Try a smaller resume or paste the resume text.';
    matchError.hidden = false;
    resumeInput.focus();
    return;
  }
  matchButton.disabled = true;
  matchButton.innerHTML = 'Finding matches <span aria-hidden="true">…</span>';
  document.querySelector('#empty-state').hidden = true;
  document.querySelector('#match-output').hidden = true;
  const output = document.querySelector('#demo-results');
  const loader = document.createElement('div');
  loader.className = 'loading-state';
  loader.id = 'match-loading';
  loader.textContent = resumeFile ? 'Reading your resume and ranking internships…' : 'Mapping skills and ranking internships…';
  output.append(loader);
  try {
    let response;
    if (resumeFile) {
      const formData = new FormData();
      formData.append('resume', resumeFile);
      response = await fetch('/match/upload', { method: 'POST', body: formData });
    } else {
      response = await fetch('/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_text: profileText })
      });
    }
    const result = await readApiJson(response);
    if (!response.ok) throw new Error(result.detail || `Request failed (${response.status})`);
    renderSkills(result.extracted_skills || []);
    const sourceNote = document.querySelector('#source-note');
    if (result.input_source === 'pdf_resume') {
      sourceNote.textContent = `Scanned resume: ${result.filename}. Text was extracted in memory and was not saved.`;
      sourceNote.hidden = false;
    } else {
      sourceNote.hidden = true;
      sourceNote.textContent = '';
    }
    renderInternships('#matcher-list', result.matcher || []);
    renderInternships('#baseline-list', result.baseline || []);
    document.querySelector('#match-output').hidden = false;
  } catch (error) {
    document.querySelector('#empty-state').hidden = false;
    matchError.textContent = error.message || 'Could not load matches. Check that the API is running and try again.';
    matchError.hidden = false;
  } finally {
    loader.remove();
    matchButton.disabled = false;
    matchButton.innerHTML = 'Find my matches <span aria-hidden="true">↗</span>';
  }
});

function finiteValue(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function renderBarRow(label, matcherValue, baselineValue, { scale = 1, percent = true, single = false } = {}) {
  const matcherWidth = Math.min(100, Math.max(0, matcherValue / scale * 100));
  const baselineWidth = baselineValue === null ? 0 : Math.min(100, Math.max(0, baselineValue / scale * 100));
  const matcherLabel = percent ? formatPercent(matcherValue) : `${matcherValue.toFixed(2)} / ${scale}`;
  const baselineLabel = baselineValue === null ? '' : (percent ? formatPercent(baselineValue) : `${baselineValue.toFixed(2)} / ${scale}`);
  return `<div class="chart-row">
    <div class="chart-label">${escapeHtml(label)}</div>
    <div class="bar-stack">
      <div class="bar-line"><div class="bar-track"><div class="bar-fill" style="width:${matcherWidth}%"></div></div><span class="bar-value">${matcherLabel}</span></div>
      ${single ? '' : `<div class="bar-line"><div class="bar-track"><div class="bar-fill baseline" style="width:${baselineWidth}%"></div></div><span class="bar-value">${baselineLabel}</span></div>`}
    </div>
  </div>`;
}

function renderMetrics(metrics) {
  const p5Matcher = finiteValue(metrics?.precision_at_5?.matcher);
  const p5Baseline = finiteValue(metrics?.precision_at_5?.baseline);
  const matcherExtraction = metrics?.skill_extraction?.hybrid;
  const baselineExtraction = metrics?.skill_extraction?.dictionary;
  const matcherF1 = finiteValue(matcherExtraction?.f1);
  const baselineF1 = finiteValue(baselineExtraction?.f1);
  const gapMean = finiteValue(metrics?.mean_gap_usefulness_rating);
  if ([p5Matcher, p5Baseline, matcherF1, baselineF1, gapMean].some((value) => value === null)) {
    throw new Error('The metrics file is missing one or more computed values expected by this view.');
  }

  metricsStatus.hidden = true;
  metricsContent.hidden = false;
  const precisionMatcher = finiteValue(matcherExtraction.precision);
  const precisionBaseline = finiteValue(baselineExtraction.precision);
  const recallMatcher = finiteValue(matcherExtraction.recall);
  const recallBaseline = finiteValue(baselineExtraction.recall);
  if ([precisionMatcher, precisionBaseline, recallMatcher, recallBaseline].some((value) => value === null)) {
    throw new Error('The metrics file is missing computed extraction precision or recall.');
  }

  document.querySelector('#metric-summary').innerHTML = `
    <article class="metric-summary"><p class="eyebrow">Matcher precision at five</p><strong>${formatPercent(p5Matcher)}</strong><p class="metric-sub">${escapeHtml(metrics.human_labeled_counts?.students_rated_for_relevance ?? '')} human-rated student rankings</p></article>
    <article class="metric-summary"><p class="eyebrow">Hybrid extraction F1</p><strong>${formatPercent(matcherF1)}</strong><p class="metric-sub">Dictionary baseline: ${formatPercent(baselineF1)}</p></article>
    <article class="metric-summary"><p class="eyebrow">Gap report usefulness</p><strong>${gapMean.toFixed(2)} <small>/ 5</small></strong><p class="metric-sub">Mean human rating for matcher reports</p></article>
  `;
  document.querySelector('#metrics-chart').innerHTML = [
    renderBarRow('Precision@5', p5Matcher, p5Baseline),
    renderBarRow('Skill extraction F1', matcherF1, baselineF1),
    renderBarRow('Gap report usefulness', gapMean, null, { scale: 5, percent: false, single: true })
  ].join('');
  document.querySelector('#metrics-table').innerHTML = `
    <tr><td>Precision@5</td><td>${formatPercent(p5Matcher)}</td><td>${formatPercent(p5Baseline)}</td></tr>
    <tr><td>Skill extraction precision</td><td>${formatPercent(precisionMatcher)}</td><td>${formatPercent(precisionBaseline)}</td></tr>
    <tr><td>Skill extraction recall</td><td>${formatPercent(recallMatcher)}</td><td>${formatPercent(recallBaseline)}</td></tr>
    <tr><td>Skill extraction F1</td><td>${formatPercent(matcherF1)}</td><td>${formatPercent(baselineF1)}</td></tr>
    <tr><td>Mean gap report usefulness</td><td>${gapMean.toFixed(2)} / 5</td><td>Not rated</td></tr>
  `;
  const counts = metrics.human_labeled_counts || {};
  document.querySelector('#evaluation-counts').textContent = [
    counts.relevance_candidates !== undefined ? `${counts.relevance_candidates} relevance judgments` : '',
    counts.extraction_documents !== undefined ? `${counts.extraction_documents} extraction documents` : '',
    counts.gap_reports_rated !== undefined ? `${counts.gap_reports_rated} gap ratings` : ''
  ].filter(Boolean).join(' · ');
  document.querySelector('#metrics-footnote').textContent = `Extraction compares ${metrics.configuration?.embedding_model || 'configured embeddings'} hybrid extraction with dictionary extraction. Similarity threshold: ${metrics.configuration?.similarity_threshold ?? 'not recorded'}.`;
}

async function loadMetrics() {
  metricsContent.hidden = true;
  metricsStatus.hidden = false;
  metricsStatus.classList.remove('is-error');
  metricsStatus.textContent = 'Loading evaluation…';
  try {
    const response = await fetch('/metrics', { headers: { Accept: 'application/json' } });
    const payload = await readApiJson(response);
    if (response.status === 404 && payload.detail === 'Evaluation not run yet') {
      metricsStatus.textContent = 'Evaluation not run yet';
      return;
    }
    if (!response.ok) throw new Error(payload.detail || 'Could not load evaluation metrics.');
    renderMetrics(payload);
  } catch (error) {
    metricsStatus.classList.add('is-error');
    metricsStatus.textContent = error.message || 'Could not load evaluation metrics.';
  }
}

document.querySelector('#refresh-metrics').addEventListener('click', loadMetrics);
