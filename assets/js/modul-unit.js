import { showToast } from './utils.js';

const MODULE_ROOTS = {
  textbook1: 'assets/modules/textbook1',
  textbook2: 'assets/modules/textbook2',
};
const PROGRESS_KEY = 'lk_module_progress_v2';

const BASE_TABS = [
  { id: 'source', label: 'HALAMAN ASLI' },
  { id: 'flow', label: 'ALUR BELAJAR' },
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
    activeTab = getInitialTab(currentTabs);
    activePractice = getInitialPractice();
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
    if (tab.id === 'flow') return (sections.lesson_flow || []).length;
    if (tab.id === 'practice') return (sections.reading || []).length || (sections.listening || []).length;
    return (sections[tab.id] || []).length;
  });
}

function clampUnit(unit) {
  const n = Number(unit);
  if (!Number.isFinite(n)) return 31;
  return Math.min(60, Math.max(1, n));
}

function getInitialTab(tabs) {
  const requested = new URLSearchParams(location.search).get('tab');
  return tabs.some(tab => tab.id === requested) ? requested : (tabs[0]?.id || 'source');
}

function getInitialPractice() {
  const requested = new URLSearchParams(location.search).get('practice');
  return requested === 'listening' ? 'listening' : 'reading';
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
  const flowCount = (moduleData.sections.lesson_flow || []).length;
  container.innerHTML = `
    <section class="module-hero">
      <div>
        <div class="module-kicker">${bookLabel} · Unit ${moduleData.unit}</div>
        <h1 class="module-title">${escapeHtml(moduleData.title_ko)}</h1>
        <p class="module-subtitle">${escapeHtml(moduleData.title_en || moduleData.title_id || '')}</p>
        ${moduleData.title_id ? `<p class="module-subtitle module-subtitle-id">${escapeHtml(moduleData.title_id)}</p>` : ''}
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
      ${flowCount ? `<div><strong>${flowCount}</strong><span>alur halaman</span></div>` : ''}
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
  renderFlow();
  renderAudio();
  renderCards('vocab', 'Kosakata', moduleData.sections.vocab || []);
  renderCards('grammar', 'Grammar', moduleData.sections.grammar || []);
  renderConversation();
  renderCards('culture', 'Budaya', moduleData.sections.culture || []);
  renderPractice();
}

function showSection(tabId) {
  if (activeTab && activeTab !== tabId) stopAudio();
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

function renderFlow() {
  const el = document.getElementById('section_flow');
  if (!el) return;
  const blocks = moduleData.sections.lesson_flow || [];
  if (!blocks.length) {
    el.innerHTML = `<div class="module-empty"><p>Belum ada alur belajar untuk unit ini.</p></div>`;
    return;
  }
  el.innerHTML = `
    <div class="learning-map">
      ${blocks.map((block, idx) => `
        <button class="learning-step" type="button" data-flow-page="${block.page}">
          <span>${String(idx + 1).padStart(2, '0')}</span>
          <strong>${escapeHtml(block.title_id || block.title_ko || 'Materi')}</strong>
        </button>
      `).join('')}
    </div>
    <div class="flow-list">
      ${blocks.map(block => `
        <article class="flow-card" id="flow_page_${block.page}">
          <div class="flow-thumb">
            ${block.image ? `<img src="${escapeAttr(block.image)}" alt="Halaman ${block.page}" loading="lazy" />` : ''}
          </div>
          <div class="flow-body">
            <div class="flow-meta">
              <span>Halaman ${block.page}${block.book_page ? ` · buku ${block.book_page}` : ''}</span>
              <span>${escapeHtml(verificationLabel(block.verification))}</span>
            </div>
            <h2>${escapeHtml(block.title_id || block.title_ko || 'Materi')}</h2>
            <p class="flow-subtitle">${escapeHtml(block.title_ko || '')}${block.title_en ? ` · ${escapeHtml(block.title_en)}` : ''}</p>
            <div class="flow-tags">
              ${(block.sections || []).map(section => `<span>${escapeHtml(sectionLabel(section))}</span>`).join('')}
            </div>
            ${renderFlowHighlights(block)}
            <details class="flow-detail">
              <summary>Teks resmi hasil ekstraksi</summary>
              <p>${textToHtml(block.body || '')}</p>
            </details>
            <div class="flow-actions">
              ${renderFlowAction(block)}
              <button class="btn btn-outline" type="button" data-source-page="${block.page}">Halaman asli</button>
            </div>
          </div>
        </article>
      `).join('')}
    </div>
  `;
  el.querySelectorAll('[data-flow-page]').forEach(button => {
    button.addEventListener('click', () => {
      document.getElementById(`flow_page_${button.dataset.flowPage}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  el.querySelectorAll('[data-source-page]').forEach(button => {
    button.addEventListener('click', () => {
      showSection('source');
      document.getElementById(`page_${button.dataset.sourcePage}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  el.querySelectorAll('[data-open-tab]').forEach(button => {
    button.addEventListener('click', () => showSection(button.dataset.openTab));
  });
}

function renderFlowHighlights(block) {
  const page = Number(block.page);
  const sections = block.sections || [];
  if (sections.includes('vocab')) {
    const cards = (moduleData.sections.vocab || []).filter(card => Number(card.source_page) === page).slice(0, 10);
    if (cards.length) {
      return `<div class="flow-mini-grid">${cards.map(card => `
        <div class="flow-mini-term">
          <strong>${textToHtml(card.front)}</strong>
          <span>${textToHtml(cardBackText(card))}</span>
        </div>
      `).join('')}</div>`;
    }
  }
  if (sections.includes('grammar')) {
    const cards = (moduleData.sections.grammar || []).filter(card => Number(card.source_page) === page).slice(0, 2);
    if (cards.length) {
      return `<div class="flow-focus-list">${cards.map(card => `
        <article>
          <strong>${textToHtml(card.front)}</strong>
          <p>${textToHtml(truncateText(cardBackText(card), 220))}</p>
        </article>
      `).join('')}</div>`;
    }
  }
  if (sections.includes('conversation')) {
    const cards = (moduleData.sections.conversation || []).filter(card => Number(card.source_page) === page).slice(0, 4);
    if (cards.length) {
      return `<div class="flow-dialog-preview">${cards.map((card, idx) => `
        <div class="dialog-bubble ${idx % 2 === 0 ? 'speaker-a' : 'speaker-b'}">
          <div class="dialog-label">${escapeHtml(card.speaker || (idx % 2 === 0 ? 'A' : 'B'))}</div>
          <p class="korean-text">${textToHtml(card.front)}</p>
          ${card.back ? `<p class="indo-text">${textToHtml(card.back)}</p>` : ''}
        </div>
      `).join('')}</div>`;
    }
  }
  if (sections.includes('culture') || sections.includes('self_assessment')) {
    const card = (moduleData.sections.culture || []).find(item => Number(item.source_page) === page);
    if (card) {
      return `<div class="flow-focus-list"><article><strong>${textToHtml(card.front)}</strong><p>${textToHtml(truncateText(card.body || card.back, 340))}</p></article></div>`;
    }
  }
  if (sections.includes('reading') || sections.includes('listening')) {
    const kind = sections.includes('reading') ? 'reading' : 'listening';
    const questions = moduleData.sections[kind] || [];
    return `<div class="flow-practice-preview">
      <strong>${questions.length} soal ${kind === 'reading' ? 'reading' : 'listening'} resmi</strong>
      <span>${questions.filter(question => question.jawaban).length} jawaban appendix tersambung</span>
    </div>`;
  }
  return `<div class="flow-focus-list"><article><strong>${escapeHtml(block.title_id || block.title_ko || 'Materi')}</strong><p>${textToHtml(truncateText(block.body, 260))}</p></article></div>`;
}

function renderFlowAction(block) {
  const sections = block.sections || [];
  if (sections.includes('vocab')) return `<button class="btn btn-primary" type="button" data-open-tab="vocab">Latih kosakata</button>`;
  if (sections.includes('grammar')) return `<button class="btn btn-primary" type="button" data-open-tab="grammar">Buka grammar</button>`;
  if (sections.includes('conversation')) return `<button class="btn btn-primary" type="button" data-open-tab="conversation">Latih dialog</button>`;
  if (sections.includes('culture') || sections.includes('self_assessment')) return `<button class="btn btn-primary" type="button" data-open-tab="culture">Baca budaya</button>`;
  if (sections.includes('reading') || sections.includes('listening')) return `<button class="btn btn-primary" type="button" data-open-tab="practice">Kerjakan latihan</button>`;
  return '';
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
            ${cardSourceLabel(card)}
          </span>
          <span class="study-card-face back">
            <span class="answer-label">${escapeHtml(cardBackLabel(card))}</span>
            <span class="indo-text">${textToHtml(cardBackText(card) || card.front || '-')}</span>
            ${card.korean_note ? `<span class="hint-text">${textToHtml(card.korean_note)}</span>` : ''}
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
    const filtered = cards.filter(c => `${c.front} ${c.back} ${c.translation_id || ''} ${c.speaker || ''}`.toLowerCase().includes(query)).slice(0, 120);
    el.querySelector(`[data-term-list="${sectionId}"]`).innerHTML = renderTermList(filtered, sectionId);
    bindTermRows(el, sectionId, title, cards);
  });
  bindTermRows(el, sectionId, title, cards);
}

function renderTermList(cards, sectionId) {
  return cards.map(card => `
    <button class="term-row" type="button" data-jump-card="${sectionId}:${escapeAttr(card.id)}">
      <span class="korean-text">${textToHtml(card.front || '-')}</span>
      <span class="indo-text">${textToHtml(cardBackText(card) || '')}</span>
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
          <div class="dialog-label">${escapeHtml(card.speaker || (idx % 2 === 0 ? 'A' : 'B'))}</div>
          <p class="korean-text">${textToHtml(card.front)}</p>
          ${card.back ? `<p class="indo-text">${textToHtml(card.back)}</p>` : ''}
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
  area.querySelectorAll('[data-source-page]').forEach(button => {
    button.addEventListener('click', () => {
      showSection('source');
      document.getElementById(`page_${button.dataset.sourcePage}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

function renderQuestion(question) {
  const key = questionKey(question);
  const chosen = answers[key];
  const isDone = !!chosen;
  const hasImageOptions = (question.pilihan || []).some(option => option.image);
  return `
    <article class="quiz-card ${isDone ? 'answered' : ''} ${hasImageOptions ? 'image-quiz' : ''}">
      <div class="quiz-head">
        <span>${question.tipe === 'mendengarkan' ? 'Listening' : 'Reading'} ${question.nomor}</span>
        ${question.audio_url ? `<button class="audio-btn" type="button" data-audio="${escapeAttr(question.audio_url)}">Putar audio</button>` : ''}
      </div>
      ${question.source_page_image ? `
        <div class="question-source">
          <img src="${escapeAttr(question.source_page_image)}" alt="Halaman asli soal ${question.nomor}" loading="lazy" />
          <button class="btn btn-outline" type="button" data-source-page="${escapeAttr(question.source_page || '')}">Halaman asli</button>
        </div>
      ` : ''}
      ${question.instruksi ? `<p class="quiz-instruction">${textToHtml(question.instruksi)}</p>` : ''}
      ${question.teks_soal ? `<p class="korean-text">${textToHtml(question.teks_soal)}</p>` : ''}
      <div class="mc-options ${hasImageOptions ? 'image-options' : ''}">
        ${question.pilihan.map(option => renderOption(question, option, chosen)).join('')}
      </div>
      ${isDone ? renderFeedback(question, chosen) : ''}
      ${question.audio_teks ? `<details class="script-detail"><summary>Naskah listening</summary><p>${textToHtml(question.audio_teks)}</p></details>` : ''}
    </article>
  `;
}

function renderOption(question, option, chosen) {
  const selected = chosen === option.key;
  const correct = chosen && question.jawaban === option.key;
  const wrong = selected && chosen !== question.jawaban;
  return `
    <button class="mc-opt ${option.image ? 'has-image' : ''} ${selected ? 'selected' : ''} ${correct ? 'correct' : ''} ${wrong ? 'wrong' : ''}" type="button" data-answer="${questionKey(question)}:${option.key}">
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
  if (!question.jawaban) {
    showToast('Jawaban tersimpan.', 'success');
  } else if (chosen === question.jawaban) {
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
  stopAudio();
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

function stopAudio() {
  if (audio) {
    audio.pause();
    audio.currentTime = 0;
  }
  if (audioButton) audioButton.classList.remove('playing');
  audio = null;
  audioButton = null;
}

function renderFeedback(question, chosen) {
  if (!question.jawaban) {
    return `<div class="mc-feedback show correct">Jawabanmu tersimpan. Cek halaman asli atau pembahasan bersama tutor.</div>`;
  }
  const ok = chosen === question.jawaban;
  return `<div class="mc-feedback show ${ok ? 'correct' : 'wrong'}">${ok ? 'Benar' : `Jawaban benar: ${question.jawaban.toUpperCase()}`}</div>`;
}

function cardBackText(card) {
  return card.translation_id || card.back || '';
}

function cardBackLabel(card) {
  if (card.translation_id) return 'ID terkurasi';
  if (card.back_lang === 'ko_en_official') return 'Catatan resmi';
  if (card.back) return 'EN resmi dari textbook';
  return 'Materi';
}

function cardSourceLabel(card) {
  if (!card.source_page) return '';
  return `<span class="source-pill">Halaman ${escapeHtml(card.source_page)}</span>`;
}

function sectionLabel(section) {
  const labels = {
    overview: 'Ringkasan',
    vocab: 'Kosakata',
    grammar: 'Tata bahasa',
    pronunciation: 'Pelafalan',
    conversation: 'Percakapan',
    useful_expression: 'Ungkapan',
    culture: 'Budaya',
    self_assessment: 'Cek diri',
    reading: 'Reading',
    listening: 'Listening',
    preview: 'Preview',
  };
  return labels[section] || section;
}

function verificationLabel(value) {
  return value ? 'PDF resmi' : '';
}

function truncateText(value, limit = 420) {
  const text = String(value || '').trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit).trim()}...`;
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
