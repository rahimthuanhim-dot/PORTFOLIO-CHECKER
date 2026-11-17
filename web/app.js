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
const REQUIRED_WEIGHT = 0.7;
const PREFERRED_WEIGHT = 0.3;
const PROJECT_STOP_WORDS = new Set(
  'synthetic posting profile intern internship student team teams work worked working project projects experience hands skill skills built build help learn learning used using'.split(' ')
);
const ENGLISH_STOP_WORDS = new Set(
  'a about above across after afterwards again against all almost alone along already also although always am among amongst amount an and another any anyhow anyone anything anyway anywhere are around as at back be became because become becomes becoming been before beforehand behind being below beside between beyond both bottom but by call can cannot could did do does doing done down due during each eg eight either eleven else elsewhere empty enough etc even ever every everyone everything everywhere except few fifteen fifty first five for former formerly forty four from front full further get give go had has have he hence her here hereafter hereby herein hereupon hers herself him himself his how however hundred i ie if in indeed interest into is it its itself keep last latter latterly least less ltd made many may me meanwhile might mine more moreover most mostly move much must my myself name namely neither never nevertheless next nine no nobody none noone nor not nothing now nowhere of off often on once one only onto or other others otherwise our ours ourselves out over own part per perhaps please put rather re same see seem seemed seeming seems serious several she should show side since sincere six sixty so some somehow someone something sometime sometimes somewhere still such system take ten than that the their them themselves then thence there thereafter thereby therefore therein thereupon these they third this those though three through throughout thru thus to together too top toward towards twelve twenty two un under until up upon us very via was we well were what whatever when whence whenever where whereafter whereas whereby wherein whereupon wherever whether which while who whoever whole whom whose why will with within without would yet you your yours yourself yourselves'.split(' ')
);
const STOP_WORDS = new Set([...ENGLISH_STOP_WORDS, ...PROJECT_STOP_WORDS]);
let taxonomy = [];
let internships = [];
let postingSkillSets = [];

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

async function loadStaticJson(path) {
  const response = await fetch(path, { headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status}).`);
  return response.json();
}

const appReady = Promise.all([
  loadStaticJson('/data/skills.json'),
  loadStaticJson('/data/internships.json')
]).then(([skills, postings]) => {
  taxonomy = skills;
  internships = postings;
  postingSkillSets = internships.map(extractPostingSkills);
}).catch((error) => {
  matchButton.disabled = true;
  matchError.textContent = `The demo data could not be loaded: ${error.message}`;
  matchError.hidden = false;
});
characterCount.textContent = `${profileInput.value.length.toLocaleString()} characters`;

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
  selectedFile.hidden = !file;
  selectedFile.textContent = file ? `Selected resume: ${file.name} (read locally)` : '';
});

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function hasWordBoundary(text, start, end) {
  const isWord = (character) => character !== undefined && /[\p{L}\p{N}_]/u.test(character);
  return !isWord(text[start - 1]) && !isWord(text[end]);
}

function extractSkills(text) {
  const matches = [];
  for (const entry of taxonomy) {
    const terms = [entry.canonical_name, ...(entry.aliases || [])];
    for (const term of terms) {
      if (typeof term !== 'string' || !term.trim()) continue;
      const phrasePattern = escapeRegExp(term.trim()).replace(/\s+/g, '\\s+');
      const pattern = new RegExp(phrasePattern, 'giu');
      for (const found of text.matchAll(pattern)) {
        const start = found.index;
        const end = start + found[0].length;
        if (hasWordBoundary(text, start, end)) {
          matches.push({ start, end, length: end - start, skill: entry.canonical_name });
        }
      }
    }
  }

  const accepted = [];
  const skills = new Set();
  matches.sort((left, right) => right.length - left.length || left.start - right.start || left.skill.localeCompare(right.skill));
  for (const match of matches) {
    if (accepted.some((item) => match.start < item.end && item.start < match.end)) continue;
    accepted.push(match);
    skills.add(match.skill);
  }
  return [...skills].sort().map((skill) => ({ skill, confidence: 1 }));
}

function parseSkillField(value) {
  return new Set((value || '').split('|').map((skill) => skill.trim()).filter(Boolean));
}

function extractPostingSkills(posting) {
  return new Set(extractSkills(posting.description || '').map((item) => item.skill));
}

function missingSkillGroups(studentSkills, posting, postingSkills) {
  const required = [...parseSkillField(posting.required_skills)]
    .filter((skill) => postingSkills.has(skill) && !studentSkills.has(skill)).sort();
  const preferred = [...parseSkillField(posting.preferred_skills)]
    .filter((skill) => postingSkills.has(skill) && !studentSkills.has(skill)).sort();
  return { required, preferred };
}

function matchScore(studentSkills, posting, postingSkills) {
  const required = [...parseSkillField(posting.required_skills)].filter((skill) => postingSkills.has(skill));
  const preferred = [...parseSkillField(posting.preferred_skills)].filter((skill) => postingSkills.has(skill));
  const parts = [];
  if (required.length) parts.push([REQUIRED_WEIGHT, required.filter((skill) => studentSkills.has(skill)).length / required.length]);
  if (preferred.length) parts.push([PREFERRED_WEIGHT, preferred.filter((skill) => studentSkills.has(skill)).length / preferred.length]);
  const totalWeight = parts.reduce((sum, [weight]) => sum + weight, 0);
  return totalWeight ? parts.reduce((sum, [weight, score]) => sum + weight * score, 0) / totalWeight : 0;
}

function rankMatcher(studentSkills, postings, postingSkillSets) {
  return postings.map((posting, index) => ({
    posting,
    index,
    score: matchScore(studentSkills, posting, postingSkillSets[index]),
    postingSkills: postingSkillSets[index]
  })).sort((left, right) => right.score - left.score || left.index - right.index).slice(0, 5);
}

function tokenize(text) {
  return (text.match(/[a-zA-Z0-9][a-zA-Z0-9_+#.]*/g) || [])
    .map((token) => token.toLocaleLowerCase())
    .filter((token) => !STOP_WORDS.has(token) && (token.length > 1 || token === 'c' || token === 'r'));
}

function tfidfCosine(queryTokens, documents) {
  const queryCounts = new Map();
  for (const token of queryTokens) queryCounts.set(token, (queryCounts.get(token) || 0) + 1);
  const docTokens = documents.map((doc) => tokenize(doc));
  const docFreq = new Map();
  for (const token of new Set(queryTokens)) docFreq.set(token, 1);
  for (const tokens of docTokens) {
    for (const token of new Set(tokens)) docFreq.set(token, (docFreq.get(token) || 0) + 1);
  }
  const documentCount = docTokens.length + 1;
  const idf = (token) => Math.log((1 + documentCount) / (1 + (docFreq.get(token) || 0))) + 1;
  const queryVector = new Map([...queryCounts].map(([token, count]) => [token, count * idf(token)]));
  const queryNorm = Math.sqrt([...queryVector.values()].reduce((sum, value) => sum + value * value, 0));

  return docTokens.map((tokens) => {
    const counts = new Map();
    for (const token of tokens) counts.set(token, (counts.get(token) || 0) + 1);
    let dot = 0;
    let normSquared = 0;
    for (const [token, count] of counts) {
      const weight = count * idf(token);
      normSquared += weight * weight;
      dot += weight * (queryVector.get(token) || 0);
    }
    const norm = Math.sqrt(normSquared) * queryNorm;
    return norm ? dot / norm : 0;
  });
}

function rankBaseline(profileText, postings, profileSkills, postingSkillSets) {
  const scores = tfidfCosine(profileText ? tokenize(profileText) : [], postings.map((posting) => `${posting.title || ''} ${posting.description || ''}`));
  return postings.map((posting, index) => ({
    posting,
    index,
    score: scores[index],
    postingSkills: postingSkillSets[index]
  })).sort((left, right) => right.score - left.score || left.index - right.index).slice(0, 5);
}

function formatGaps(profileSkills, posting, postingSkills) {
  const gaps = missingSkillGroups(profileSkills, posting, postingSkills);
  const required = gaps.required.length ? gaps.required.join(', ') : 'None detected';
  const preferred = gaps.preferred.length ? gaps.preferred.join(', ') : 'None detected';
  return {
    ...gaps,
    message: `Skills extracted from the posting but not evidenced in the profile — required: ${required}; preferred: ${preferred}.`
  };
}

function renderSkills(skills) {
  const container = document.querySelector('#skill-chips');
  document.querySelector('#skill-count').textContent = `${skills.length} ${skills.length === 1 ? 'skill' : 'skills'}`;
  container.innerHTML = skills.length
    ? skills.map((item) => `<span class="skill-chip">${escapeHtml(item.skill)}</span>`).join('')
    : '<span class="muted">No taxonomy aliases were detected in the profile.</span>';
}

function renderInternships(target, ranked, profileSkills) {
  const container = document.querySelector(target);
  if (!ranked.length) {
    container.innerHTML = '<p class="muted">No internship records were returned.</p>';
    return;
  }
  container.innerHTML = ranked.map((item, index) => {
    const gaps = formatGaps(profileSkills, item.posting, item.postingSkills);
    return `<details class="internship-card" ${index === 0 ? 'open' : ''}>
      <summary>
        <span class="rank-number">${String(index + 1).padStart(2, '0')}</span>
        <span class="card-main"><span class="card-title">${escapeHtml(item.posting.title)}</span><span class="card-company">${escapeHtml(item.posting.company)}</span></span>
        <span class="score-pill">${Number(item.score).toFixed(3)}</span>
      </summary>
      <div class="card-detail">
        <p class="card-description">${escapeHtml(item.posting.description)}</p>
        <div class="gap-report"><strong>Skill-gap report</strong>${escapeHtml(gaps.message)}</div>
      </div>
    </details>`;
  }).join('');
}

async function readPdfText(file) {
  const pdfjs = await import('https://cdn.jsdelivr.net/npm/pdfjs-dist@6.5.438/build/pdf.min.mjs');
  pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@6.5.438/build/pdf.worker.min.mjs';
  const documentTask = pdfjs.getDocument({ data: await file.arrayBuffer() });
  const document = await documentTask.promise;
  const pages = [];
  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
    const page = await document.getPage(pageNumber);
    const content = await page.getTextContent();
    pages.push(content.items.map((item) => item.str || '').join(' '));
  }
  await document.destroy();
  return pages.join('\n').trim();
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  matchError.hidden = true;
  matchError.textContent = '';
  const resumeFile = resumeInput.files?.[0];
  let profileText = profileInput.value.trim();
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

  matchButton.disabled = true;
  matchButton.innerHTML = 'Finding matches <span aria-hidden="true">…</span>';
  document.querySelector('#empty-state').hidden = true;
  document.querySelector('#match-output').hidden = true;
  const loader = document.createElement('div');
  loader.className = 'loading-state';
  loader.id = 'match-loading';
  loader.textContent = resumeFile ? 'Reading your resume on this device…' : 'Mapping skills and ranking internships…';
  document.querySelector('#demo-results').append(loader);

  try {
    await appReady;
    let inputSource = 'profile_text';
    if (resumeFile) {
      profileText = await readPdfText(resumeFile);
      if (!profileText) throw new Error('No selectable text was found in this PDF. Scanned image PDFs need OCR.');
      inputSource = 'pdf_resume';
    }
    const extracted = extractSkills(profileText);
    const profileSkills = new Set(extracted.map((item) => item.skill));
    const matcher = rankMatcher(profileSkills, internships, postingSkillSets);
    const baseline = rankBaseline(profileText, internships, profileSkills, postingSkillSets);
    renderSkills(extracted);
    const sourceNote = document.querySelector('#source-note');
    sourceNote.textContent = inputSource === 'pdf_resume'
      ? `Scanned resume: ${resumeFile.name}. Text was extracted in your browser and not uploaded.`
      : '';
    sourceNote.hidden = inputSource !== 'pdf_resume';
    renderInternships('#matcher-list', matcher, profileSkills);
    renderInternships('#baseline-list', baseline, profileSkills);
    document.querySelector('#match-output').hidden = false;
  } catch (error) {
    document.querySelector('#empty-state').hidden = false;
    matchError.textContent = error.message || 'Could not process this profile.';
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
  const precisionMatcher = finiteValue(matcherExtraction.precision);
  const precisionBaseline = finiteValue(baselineExtraction.precision);
  const recallMatcher = finiteValue(matcherExtraction.recall);
  const recallBaseline = finiteValue(baselineExtraction.recall);
  if ([precisionMatcher, precisionBaseline, recallMatcher, recallBaseline].some((value) => value === null)) {
    throw new Error('The metrics file is missing computed extraction precision or recall.');
  }

  metricsStatus.hidden = true;
  metricsContent.hidden = false;
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
  document.querySelector('#metrics-footnote').textContent = `Metrics were computed by the research evaluator using ${metrics.configuration?.embedding_model || 'the recorded extractor configuration'}; threshold: ${metrics.configuration?.similarity_threshold ?? 'not recorded'}.`;
}

async function loadMetrics() {
  metricsContent.hidden = true;
  metricsStatus.hidden = false;
  metricsStatus.classList.remove('is-error');
  metricsStatus.textContent = 'Loading evaluation…';
  try {
    const response = await fetch('/metrics.json', { headers: { Accept: 'application/json' } });
    if (response.status === 404) {
      metricsStatus.textContent = 'Evaluation not run yet';
      return;
    }
    if (!response.ok) throw new Error(`Could not load evaluation metrics (HTTP ${response.status}).`);
    renderMetrics(await response.json());
  } catch (error) {
    metricsStatus.classList.add('is-error');
    metricsStatus.textContent = error.message || 'Could not load evaluation metrics.';
  }
}

document.querySelector('#refresh-metrics').addEventListener('click', loadMetrics);
