import { showToast } from './utils.js';

const MODULE_ROOTS = {
  textbook1: 'assets/modules/textbook1',
  textbook2: 'assets/modules/textbook2',
};
const PROGRESS_KEY = 'lk_module_progress_v2';

const BASE_TABS = [
  { id: 'source', label: 'HALAMAN ASLI' },
  { id: 'audio', label: 'AUDIO' },
  { id: 'vocab', label: 'KOSAKATA' },
  { id: 'grammar', label: 'GRAMMAR' },
  { id: 'conversation', label: 'PERCAKAPAN' },
  { id: 'culture', label: 'BUDAYA' },
  { id: 'practice', label: 'LATIHAN' },
];

let bookIndexes = {};
let allUnits = [];
let currentTabs = [];
let moduleData = null;
let currentUnit = 31;
let activeTab = 'source';
let activePractice = 'reading';
let cardState = {};
let answers = {};
let audio = null;
let audioButton = null;

export async function renderModule(unit) {
  currentUnit = clampUnit(unit || 31);
  const loading = document.getElementById('loadingDiv');
  const errorDiv = document.getElementById('errorDiv');
  const content = document.getElementById('contentArea');
  const nav = document.getElementById('seksiNav');

  if (loading) loading.style.display = 'block';
  if (errorDiv) errorDiv.style.display = 'none';
  if (content) content.innerHTML = '';

  try {
    await loadIndexes();
    const book = getBookForUnit(currentUnit);
    moduleData = await fetchJson(`${MODULE_ROOTS[book]}/unit_${currentUnit}/module.json`);
    currentTabs = buildTabs(moduleData);
    activeTab = currentTabs[0]?.id || 'source';
    activePractice = 'reading';
    cardState = {};
    answers = loadProgress(currentUnit).answers || {};

    renderNav(nav);
    renderShell(content);
    showSection(activeTab);
    updateProgress();
  } catch (error) {
    console.error('renderModule error:', error);
    if (errorDiv) {
      errorDiv.style.display = 'block';
      errorDiv.innerHTML = `<p>Gagal memuat modul lokal unit ${currentUnit}.</p><p class="hint-text">${escapeHtml(error.message)}</p>`;
    }
  } finally {
    if (loading) loading.style.display = 'none';
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${url} HTTP ${response.status}`);
  return response.json();
}

async function loadIndexes() {
  if (allUnits.length) return;
  const entries = await Promise.all(Object.entries(MODULE_ROOTS).map(async ([book, root]) => {
    const index = await fetchJson(`${root}/index.json`);
    return [book, index];
  }));
  bookIndexes = Object.fromEntries(entries);
  allUnits = Object.values(bookIndexes)
    .flatMap(index => index.units || [])
    .sort((a, b) => a.unit - b.unit);
}

function getBookForUnit(unit) {
  return Number(unit) <= 30 ? 'textbook1' : 'textbook2';
}

function buildTabs(data) {
  const sections = data.sections || {};
  return BASE_TABS.filter(tab => {
    if (tab.id === 'source') return true;
    if (tab.id === 'practice') return (sections.reading || []).length || (sections.listening || []).length;
    return (sections[tab.id] || []).length;
  });
}

function clampUnit(unit) {
  const n = Number(unit);
  if (!Number.isFinite(n)) return 31;
  return Math.min(60, Math.max(1, n));
}

function renderNav(navEl) {
  if (!navEl) return;
  navEl.innerHTML = currentTabs.map(tab => `
    <button class="seksi-nav-btn" data-tab="${tab.id}" type="button">${tab.label}</button>
  `).join('');
  navEl.querySelectorAll('[data-tab]').forEach(button => {
    button.addEventListener('click', () => showSection(button.dataset.tab));
  });
}

function renderShell(container) {
  if (!container || !moduleData) return;
  const bookLabel = moduleData.book === 'textbook1' ? 'Textbook 1' : 'Textbook 2';
  const audioCount = (moduleData.sections.audio || []).length || moduleData.integrity.lesson_audio || 0;
  const readingCount = (moduleData.sections.reading || []).length;
  const listeningCount = (moduleData.sections.listening || []).length;
  container.innerHTML = `
    <section class="module-hero">
      <div>
        <div class="module-kicker">${bookLabel} · Unit ${moduleData.unit}</div>
        <h1 class="module-title">${escapeHtml(moduleData.title_ko)}</h1>
        <p class="module-subtitle">${escapeHtml(moduleData.title_en || moduleData.title_id || '')}</p>
      </div>
      <div class="module-actions">
        <button class="btn btn-outline" type="button" data-unit-prev>Unit ${Math.max(1, currentUnit - 1)}</button>
        <select class="unit-select" aria-label="Pilih unit" data-unit-select>
          ${allUnits.map(u => `<option value="${u.unit}" ${u.unit === currentUnit ? 'selected' : ''}>Unit ${u.unit} · ${escapeHtml(u.title_ko)}</option>`).join('')}
        </select>
        <button class="btn btn-outline" type="button" data-unit-next>Unit ${Math.min(60, currentUnit + 1)}</button>
      </div>
    </section>

    <section class="source-summary">
      <div><strong>${moduleData.integrity.pdf_pages}</strong><span>halaman asli</span></div>
      ${audioCount ? `<div><strong>${audioCount}</strong><span>audio unit</span></div>` : ''}
      ${(moduleData.sections.vocab || []).length ? `<div><strong>${moduleData.sections.vocab.length}</strong><span>kartu kosakata</span></div>` : ''}
      ${readingCount ? `<div><strong>${readingCount}</strong><span>reading</span></div>` : ''}
      ${listeningCount ? `<div><strong>${listeningCount}</strong><span>listening</span></div>` : ''}
    </section>

    ${currentTabs.map(tab => `<section class="seksi-section module-section" data-section="${tab.id}" id="section_${tab.id}"></section>`).join('')}
  `;

  container.querySelector('[data-unit-select]').addEventListener('change', event => {
    location.href = `modul-unit.html?unit=${event.target.value}`;
  });
  container.querySelector('[data-unit-prev]').addEventListener('click', () => {
    location.href = `modul-unit.html?unit=${Math.max(1, currentUnit - 1)}`;
  });
  container.querySelector('[data-unit-next]').addEventListener('click', () => {
    location.href = `modul-unit.html?unit=${Math.min(60, currentUnit + 1)}`;
  });

  renderSource();
  renderAudio();
  renderCards('vocab', 'Kosakata', moduleData.sections.vocab || []);
  renderCards('grammar', 'Grammar', moduleData.sections.grammar || []);
  renderConversation();
  renderCards('culture', 'Budaya', moduleData.sections.culture || []);
  renderPractice();
}

function showSection(tabId) {
  activeTab = tabId;
  document.querySelectorAll('.seksi-nav-btn').forEach(button => {
    button.classList.toggle('active', button.dataset.tab === tabId);
  });
  document.querySelectorAll('.module-section').forEach(section => {
    section.classList.toggle('active', section.dataset.section === tabId);
  });
  markSeen(tabId);
  updateProgress();
}

function renderSource() {
  const el = document.getElementById('section_source');
  if (!el) return;
  el.innerHTML = `
    <div class="source-toolbar">
      <a class="btn btn-outline" href="${escapeAttr(moduleData.source_pdf)}" target="_blank" rel="noopener">Buka PDF</a>
      <button class="btn btn-primary" type="button" data-mark-source>Beri tanda sudah dibaca</button>
    </div>
    <div class="page-grid">
      ${moduleData.pages.map(page => `
        <figure class="page-frame" id="page_${page.number}">
          <img src="${escapeAttr(page.image)}" alt="Unit ${moduleData.unit} halaman ${page.number}" loading="lazy" />
          <figcaption>Halaman ${page.number}${moduleData.page_start ? ` · buku ${moduleData.page_start + page.number - 1}` : ''}</figcaption>
        </figure>
      `).join('')}
    </div>
  `;
  el.querySelector('[data-mark-source]').addEventListener('click', () => {
    markSeen('source_done');
    showToast('Halaman asli ditandai selesai.', 'success');
    updateProgress();
  });
}

function renderAudio() {
  const el = document.getElementById('section_audio');
  if (!el) return;
  const tracks = moduleData.sections.audio || [];
  if (!tracks.length) {
    el.innerHTML = `<div class="module-empty"><p>Belum ada audio unit untuk modul ini.</p></div>`;
    return;
  }

  el.innerHTML = `
    <div class="audio-list">
      ${tracks.map(track => `
        <article class="audio-row">
          <div>
            <strong>Track ${String(track.track).padStart(3, '0')}</strong>
            <span>${escapeHtml(track.label || 'Audio')}</span>
          </div>
          <button class="audio-btn" type="button" data-audio="${escapeAttr(track.audio_url)}">Putar audio</button>
        </article>
      `).join('')}
    </div>
  `;
  el.querySelectorAll('[data-audio]').forEach(button => {
    button.addEventListener('click', () => playAudio(button.dataset.audio, button));
  });
}

function renderCards(sectionId, title, cards) {
  const el = document.getElementById(`section_${sectionId}`);
  if (!el) return;
  if (!cards.length) {
    el.innerHTML = `<div class="module-empty"><p>Belum ada data ${escapeHtml(title.toLowerCase())} yang bersih untuk unit ini.</p></div>`;
    return;
  }

  const state = cardState[sectionId] || { idx: 0, flipped: false };
  cardState[sectionId] = state;
  const card = cards[state.idx] || cards[0];
  const list = cards.slice(0, 80);

  el.innerHTML = `
    <div class="study-layout">
      <div class="deck-panel">
        <div class="deck-meta">
          <span>${escapeHtml(title)}</span>
          <span>${state.idx + 1}/${cards.length}</span>
        </div>
        <button class="study-card ${state.flipped ? 'flipped' : ''}" type="button" data-flip="${sectionId}">
          <span class="study-card-face front">
            <span class="korean-text">${textToHtml(card.front || '-')}</span>
            ${sectionId.startsWith('conversation') && card.back ? `<span class="hint-text">${escapeHtml(card.back)}</span>` : ''}
          </span>
          <span class="study-card-face back">
            <span class="indo-text">${textToHtml(card.back || card.front || '-')}</span>
          </span>
        </button>
        <div class="deck-actions">
          <button class="btn btn-outline" type="button" data-card-prev="${sectionId}">Sebelumnya</button>
          <button class="btn btn-primary" type="button" data-card-known="${sectionId}">Saya ingat</button>
          <button class="btn btn-outline" type="button" data-card-next="${sectionId}">Berikutnya</button>
        </div>
      </div>
      <div class="list-panel">
        <input class="module-search" type="search" placeholder="Cari..." data-search="${sectionId}" />
        <div class="term-list" data-term-list="${sectionId}">
          ${renderTermList(list, sectionId)}
        </div>
      </div>
    </div>
  `;

  el.querySelector(`[data-flip="${sectionId}"]`).addEventListener('click', () => {
    cardState[sectionId].flipped = !cardState[sectionId].flipped;
    renderCards(sectionId, title, cards);
  });
  el.querySelector(`[data-card-prev="${sectionId}"]`).addEventListener('click', () => moveCard(sectionId, title, cards, -1));
  el.querySelector(`[data-card-next="${sectionId}"]`).addEventListener('click', () => moveCard(sectionId, title, cards, 1));
  el.querySelector(`[data-card-known="${sectionId}"]`).addEventListener('click', () => {
    markKnown(sectionId, card.id);
    moveCard(sectionId, title, cards, 1);
  });
  el.querySelector(`[data-search="${sectionId}"]`).addEventListener('input', event => {
    const query = event.target.value.trim().toLowerCase();
    const filtered = cards.filter(c => `${c.front} ${c.back}`.toLowerCase().includes(query)).slice(0, 120);
    el.querySelector(`[data-term-list="${sectionId}"]`).innerHTML = renderTermList(filtered, sectionId);
    bindTermRows(el, sectionId, title, cards);
  });
  bindTermRows(el, sectionId, title, cards);
}

function renderTermList(cards, sectionId) {
  return cards.map(card => `
    <button class="term-row" type="button" data-jump-card="${sectionId}:${escapeAttr(card.id)}">
      <span class="korean-text">${textToHtml(card.front || '-')}</span>
      <span class="indo-text">${textToHtml(card.back || '')}</span>
    </button>
  `).join('');
}

function bindTermRows(container, sectionId, title, cards) {
  container.querySelectorAll(`[data-jump-card^="${sectionId}:"]`).forEach(button => {
    button.addEventListener('click', () => {
      const id = button.dataset.jumpCard.slice(sectionId.length + 1);
      const idx = cards.findIndex(card => card.id === id);
      if (idx < 0) return;
      cardState[sectionId] = { idx, flipped: false };
      renderCards(sectionId, title, cards);
    });
  });
}

function moveCard(sectionId, title, cards, delta) {
  const state = cardState[sectionId];
  state.idx = (state.idx + delta + cards.length) % cards.length;
  state.flipped = false;
  renderCards(sectionId, title, cards);
}

function renderConversation() {
  const cards = moduleData.sections.conversation || [];
  const el = document.getElementById('section_conversation');
  if (!el) return;
  if (!cards.length) {
    renderCards('conversation', 'Percakapan', cards);
    return;
  }
  el.innerHTML = `
    <div class="conversation-panel">
      ${cards.map((card, idx) => `
        <div class="dialog-bubble ${idx % 2 === 0 ? 'speaker-a' : 'speaker-b'}">
          <div class="dialog-label">${escapeHtml(card.back || (idx % 2 === 0 ? 'A' : 'B'))}</div>
          <p class="korean-text">${textToHtml(card.front)}</p>
        </div>
      `).join('')}
    </div>
    <div class="section-divider"></div>
    <div id="section_conversation_cards"></div>
  `;
  if (!cardState.conversation_cards) cardState.conversation_cards = { idx: 0, flipped: false };
  renderCards('conversation_cards', 'Percakapan', cards);
}

function renderPractice() {
  const el = document.getElementById('section_practice');
  if (!el) return;
  const hasReading = (moduleData.sections.reading || []).length > 0;
  const hasListening = (moduleData.sections.listening || []).length > 0;
  if (!hasReading && !hasListening) {
    el.innerHTML = `<div class="module-empty"><p>Belum ada latihan untuk unit ini.</p></div>`;
    return;
  }
  if (activePractice === 'reading' && !hasReading) activePractice = 'listening';
  if (activePractice === 'listening' && !hasListening) activePractice = 'reading';
  el.innerHTML = `
    <div class="practice-tabs">
      ${hasReading ? `<button class="mode-btn ${activePractice === 'reading' ? 'active' : ''}" type="button" data-practice="reading">Reading</button>` : ''}
      ${hasListening ? `<button class="mode-btn ${activePractice === 'listening' ? 'active' : ''}" type="button" data-practice="listening">Listening</button>` : ''}
    </div>
    <div class="practice-area" id="practiceArea"></div>
  `;
  el.querySelectorAll('[data-practice]').forEach(button => {
    button.addEventListener('click', () => {
      activePractice = button.dataset.practice;
      renderPractice();
    });
  });
  renderQuestionList(activePractice);
}

function renderQuestionList(kind) {
  const area = document.getElementById('practiceArea');
  if (!area) return;
  const questions = moduleData.sections[kind] || [];
  if (!questions.length) {
    area.innerHTML = `<div class="module-empty"><p>Belum ada soal ${kind}.</p></div>`;
    return;
  }
  area.innerHTML = questions.map(question => renderQuestion(question)).join('');
  area.querySelectorAll('[data-answer]').forEach(button => {
    button.addEventListener('click', () => answerQuestion(button));
  });
  area.querySelectorAll('[data-audio]').forEach(button => {
    button.addEventListener('click', () => playAudio(button.dataset.audio, button));
  });
}

function renderQuestion(question) {
  const key = questionKey(question);
  const chosen = answers[key];
  const isDone = !!chosen;
  return `
    <article class="quiz-card ${isDone ? 'answered' : ''}">
      <div class="quiz-head">
        <span>${question.tipe === 'mendengarkan' ? 'Listening' : 'Reading'} ${question.nomor}</span>
        ${question.audio_url ? `<button class="audio-btn" type="button" data-audio="${escapeAttr(question.audio_url)}">Putar audio</button>` : ''}
      </div>
      ${question.instruksi ? `<p class="quiz-instruction">${textToHtml(question.instruksi)}</p>` : ''}
      ${question.teks_soal ? `<p class="korean-text">${textToHtml(question.teks_soal)}</p>` : ''}
      <div class="mc-options">
        ${question.pilihan.map(option => renderOption(question, option, chosen)).join('')}
      </div>
      ${isDone ? `<div class="mc-feedback show ${chosen === question.jawaban ? 'correct' : 'wrong'}">${chosen === question.jawaban ? 'Benar' : `Jawaban benar: ${question.jawaban.toUpperCase()}`}</div>` : ''}
    </article>
  `;
}

function renderOption(question, option, chosen) {
  const selected = chosen === option.key;
  const correct = chosen && question.jawaban === option.key;
  const wrong = selected && chosen !== question.jawaban;
  return `
    <button class="mc-opt ${selected ? 'selected' : ''} ${correct ? 'correct' : ''} ${wrong ? 'wrong' : ''}" type="button" data-answer="${questionKey(question)}:${option.key}">
      <span class="mc-letter">${option.label}</span>
      <span class="option-body">
        ${option.image ? `<img class="option-image" src="${escapeAttr(option.image)}" alt="Pilihan ${option.label}" loading="lazy" />` : ''}
        ${option.text ? `<span>${textToHtml(option.text)}</span>` : ''}
      </span>
    </button>
  `;
}

function answerQuestion(button) {
  const [key, chosen] = button.dataset.answer.split(':');
  if (answers[key]) return;
  const question = findQuestionByKey(key);
  if (!question) return;
  answers[key] = chosen;
  saveProgress();
  renderQuestionList(activePractice);
  if (chosen === question.jawaban) {
    showToast('Benar.', 'success');
  } else {
    showToast(`Jawaban benar: ${question.jawaban.toUpperCase()}`, 'error');
  }
  updateProgress();
}

function findQuestionByKey(key) {
  return [...(moduleData.sections.reading || []), ...(moduleData.sections.listening || [])].find(q => questionKey(q) === key);
}

function questionKey(question) {
  return `${question.tipe}_${question.nomor}`;
}

function playAudio(url, button) {
  if (!url) return;
  if (audio) audio.pause();
  if (audioButton) audioButton.classList.remove('playing');
  audio = new Audio(url);
  audioButton = button;
  button.classList.add('playing');
  audio.onended = () => {
    button.classList.remove('playing');
    audioButton = null;
  };
  audio.play().catch(error => {
    console.warn(error);
    button.classList.remove('playing');
    audioButton = null;
  });
}

function loadProgress(unit) {
  try {
    return JSON.parse(localStorage.getItem(`${PROGRESS_KEY}_${unit}`)) || { seen: {}, known: {}, answers: {} };
  } catch (_) {
    return { seen: {}, known: {}, answers: {} };
  }
}

function saveProgress() {
  const current = loadProgress(currentUnit);
  current.answers = answers;
  localStorage.setItem(`${PROGRESS_KEY}_${currentUnit}`, JSON.stringify(current));
}

function markSeen(tabId) {
  const current = loadProgress(currentUnit);
  current.seen[tabId] = true;
  localStorage.setItem(`${PROGRESS_KEY}_${currentUnit}`, JSON.stringify(current));
}

function markKnown(sectionId, cardId) {
  const current = loadProgress(currentUnit);
  current.known[sectionId] = current.known[sectionId] || {};
  current.known[sectionId][cardId] = true;
  localStorage.setItem(`${PROGRESS_KEY}_${currentUnit}`, JSON.stringify(current));
}

function updateProgress() {
  const progress = loadProgress(currentUnit);
  const readingTotal = moduleData?.sections.reading?.length || 0;
  const listeningTotal = moduleData?.sections.listening?.length || 0;
  const answered = Object.keys(progress.answers || {}).length;
  const seenCount = Object.keys(progress.seen || {}).filter(k => k !== 'source').length;
  const knownCount = Object.values(progress.known || {}).reduce((sum, group) => sum + Object.keys(group || {}).length, 0);
  const total = currentTabs.length + readingTotal + listeningTotal + Math.min(60, moduleData?.sections.vocab?.length || 0);
  const done = seenCount + answered + Math.min(60, knownCount);
  const pct = total ? Math.min(100, Math.round(done / total * 100)) : 0;
  const fill = document.getElementById('progressFill');
  const label = document.getElementById('progressLabel');
  if (fill) fill.style.width = `${pct}%`;
  if (label) label.textContent = `Unit ${currentUnit} — ${pct}% selesai`;
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, '&#96;');
}

function textToHtml(value) {
  return escapeHtml(value).replace(/\n/g, '<br>');
}
