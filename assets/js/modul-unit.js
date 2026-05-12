import { supabase } from './supabase.js';
import { showToast } from './utils.js';

// ── Navigation & state ──
const NAV = [
  { id: 'kosakata', label: 'KOSAKATA', seksi: ['vocab1','vocab2'] },
  { id: 'grammar', label: 'GRAMMAR', seksi: ['grammar1','grammar2'] },
  { id: 'percakapan', label: 'PERCAKAPAN', seksi: ['conversation1','conversation2'] },
  { id: 'budaya', label: 'BUDAYA', seksi: ['budaya'] },
  { id: 'mini_test', label: 'MINI TEST', seksi: ['mini_test'] },
];

let unitData = [];            // all records from DB
let groupedBySeksi = {};      // { seksi: [records] }
let completedSeksi = {};      // { seksi: true }
let currentUnit = 31;
let currentMode = {};         // { navId: 'belajar'|'serius' }
let flashcardState = {};      // { cardIdx, flipped }
let matchState = {};          // { left, right, selected, pairs }
let wordState = {};           // { words, slots }
let dialogState = {};         // { blanks, options, answers }
let quizState = {};           // { idx, answered, correct }

// ── Public render function ──
export async function renderModule(unit) {
  currentUnit = unit;
  const loading = document.getElementById('loadingDiv');
  const errorDiv = document.getElementById('errorDiv');
  const content = document.getElementById('contentArea');
  const nav = document.getElementById('seksiNav');
  const label = document.getElementById('progressLabel');

  if (loading) loading.style.display = 'block';
  if (errorDiv) errorDiv.style.display = 'none';
  if (content) content.innerHTML = '';
  if (label) label.textContent = `Unit ${unit} — 0% selesai`;

  try {
    unitData = await fetchData(unit);
    if (!unitData.length) throw new Error('No data');

    groupedBySeksi = groupBySeksi(unitData);
    completedSeksi = {};
    currentMode = {};
    NAV.forEach(t => { currentMode[t.id] = 'belajar'; });

    renderNav(nav);
    renderSections(content);
    updateProgress();
    if (loading) loading.style.display = 'none';
    showSection(NAV[0].id);
  } catch (e) {
    console.error('renderModule error:', e);
    if (loading) loading.style.display = 'none';
    if (errorDiv) errorDiv.style.display = 'block';
  }
}

// ── Data fetching ──
async function fetchData(unit) {
  const { data, error } = await supabase
    .from('latihan_interaktif')
    .select('*')
    .eq('unit', unit)
    .order('seksi', { ascending: true })
    .order('urutan', { ascending: true });
  if (error) throw error;
  return data || [];
}

function groupBySeksi(data) {
  const g = {};
  for (const r of data) {
    if (!g[r.seksi]) g[r.seksi] = [];
    g[r.seksi].push(r);
  }
  return g;
}

// ── Navigation ──
function renderNav(navEl) {
  navEl.innerHTML = NAV.map(t => `
    <button class="seksi-nav-btn" data-nav="${t.id}">${t.label}</button>
  `).join('');
  navEl.querySelectorAll('.seksi-nav-btn').forEach(btn => {
    btn.addEventListener('click', () => showSection(btn.dataset.nav));
  });
}

function showSection(navId) {
  document.querySelectorAll('.seksi-nav-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.nav === navId);
  });
  document.querySelectorAll('.seksi-section').forEach(s => {
    s.classList.toggle('active', s.dataset.nav === navId);
  });
}

// ── Render sections ──
function renderSections(container) {
  container.innerHTML = NAV.map(t => {
    const records = t.seksi.flatMap(s => groupedBySeksi[s] || []);
    return `
      <div class="seksi-section" data-nav="${t.id}">
        <div class="seksi-header">
          <div class="seksi-title">${t.label}</div>
          <div class="mode-toggle">
            <button class="mode-btn active" data-mode="belajar" data-nav="${t.id}">Belajar</button>
            <button class="mode-btn serious" data-mode="serius" data-nav="${t.id}">Serius</button>
          </div>
        </div>
        <div id="content_${t.id}" class="seksi-content"></div>
      </div>
    `;
  }).join('');

  // Mode toggle
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const navId = btn.dataset.nav;
      const mode = btn.dataset.mode;
      currentMode[navId] = mode;
      const parent = btn.closest('.mode-toggle');
      parent.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderContent(navId);
    });
  });

  // Initial renders
  NAV.forEach(t => renderContent(t.id));
}

// ── Render content per nav section ──
function renderContent(navId) {
  const tab = NAV.find(t => t.id === navId);
  if (!tab) return;
  const el = document.getElementById(`content_${navId}`);
  if (!el) return;

  const mode = currentMode[navId] || 'belajar';
  const records = tab.seksi.flatMap(s => groupedBySeksi[s] || []);

  if (!records.length) {
    el.innerHTML = `<div class="module-empty"><p>Belum ada materi untuk bagian ini.</p></div>`;
    return;
  }

  if (mode === 'belajar') {
    renderBelajar(el, records, navId);
  } else {
    renderSerius(el, records, navId);
  }
}

// ── BELAJAR mode ──
function renderBelajar(el, records, navId) {
  const belajarRecords = records.filter(r =>
    ['flashcard','cocokkan','pilih_kata','lengkapi_dialog'].includes(r.tipe_latihan)
  );
  if (!belajarRecords.length) {
    el.innerHTML = `<div class="module-empty"><p>Semua materi sudah dipelajari! Coba mode Serius.</p></div>`;
    return;
  }

  const html = belajarRecords.map((r, i) => {
    switch (r.tipe_latihan) {
      case 'flashcard': return renderFlashcardHTML(r, i);
      case 'cocokkan': return renderCocokkanHTML(r, i);
      case 'pilih_kata': return renderPilihKataHTML(r, i);
      case 'lengkapi_dialog': return renderDialogHTML(r, i);
      default: return '';
    }
  }).join('');
  el.innerHTML = html;

  // Attach events
  belajarRecords.forEach((r, i) => {
    switch (r.tipe_latihan) {
      case 'flashcard': initFlashcard(r, i); break;
      case 'cocokkan': initCocokkan(r, i); break;
      case 'pilih_kata': initPilihKata(r, i); break;
      case 'lengkapi_dialog': initDialog(r, i); break;
    }
  });
}

// ── SERIUS mode ──
function renderSerius(el, records, navId) {
  const seriusRecords = records.filter(r =>
    ['pilihan_ganda','pemahaman_dialog'].includes(r.tipe_latihan)
  );
  if (!seriusRecords.length) {
    // Generate from belajar records
    const mc = generateMCFromRecords(records);
    if (!mc.length) {
      el.innerHTML = `<div class="module-empty"><p>Belum ada soal untuk mode ini.</p></div>`;
      return;
    }
    renderQuiz(el, mc, navId);
    return;
  }

  const mc = seriusRecords.map(r => ({
    question: r.teks_korea || r.soal || '',
    options: parseOptions(r),
    answer: r.jawaban || '',
    explanation: r.teks_indo || '',
    audio: r.audio_url || '',
  })).filter(q => q.question && q.options.length > 1);
  renderQuiz(el, mc, navId);
}

function parseOptions(r) {
  if (r.opsi && Array.isArray(r.opsi)) return r.opsi;
  if (r.pilihan_a) {
    return [r.pilihan_a, r.pilihan_b, r.pilihan_c, r.pilihan_d].filter(Boolean);
  }
  return [];
}

function generateMCFromRecords(records) {
  const qs = records.filter(r => r.teks_korea && r.teks_indo).map(r => {
    const opts = shuffleArray([
      r.teks_indo || r.teks_korea.slice(0, 40),
      'Tidak tahu',
      'A, B, C salah',
      'Semua benar',
    ]);
    return {
      question: `Apa arti dari "${r.teks_korea.slice(0, 60)}..."?`,
      options: opts,
      answer: 'A',
      explanation: r.teks_indo || '',
      audio: r.audio_url || '',
    };
  });
  return qs;
}

function renderQuiz(el, questions, navId) {
  quizState[navId] = { idx: 0, answered: false, correct: 0, total: questions.length };
  renderQuestion(el, questions, navId, 0);
  
  // Expose for event handlers
  window.__quizQuestions = window.__quizQuestions || {};
  window.__quizQuestions[navId] = questions;
}

function renderQuestion(el, questions, navId, idx) {
  if (idx >= questions.length) {
    showQuizResult(el, navId);
    return;
  }
  const q = questions[idx];
  const letters = ['A','B','C','D'];
  
  el.innerHTML = `
    <div class="mini-test-card fade-in">
      <div class="mini-test-progress">
        ${questions.map((_, i) => `<div class="mini-test-dot ${i < idx ? 'answered' : ''}"></div>`).join('')}
      </div>
      ${q.audio ? `<button class="audio-btn" onclick="playAudio('${q.audio}', this)">🔊 Dengarkan</button>` : ''}
      <p class="korean-text">${q.question}</p>
      <div class="mc-options">
        ${q.options.map((opt, i) => `
          <div class="mc-opt" data-q="${navId}" data-ans="${letters[i]}" data-correct="${letters[i] === q.answer}" data-answer="${q.answer}" onclick="answerMC(this)">
            <span class="mc-letter">${letters[i]}</span>
            <span>${opt}</span>
          </div>
        `).join('')}
      </div>
      <div class="mc-feedback" id="mcFeedback_${navId}"></div>
      <button class="btn btn-primary" id="mcNext_${navId}" style="display:none;margin-top:12px" onclick="nextMC('${navId}')">
        ${idx < questions.length - 1 ? 'Soal Berikutnya →' : 'Lihat Hasil'}
      </button>
    </div>
  `;
}

// ── Flashcard ──
function renderFlashcardHTML(r, i) {
  return `
    <div class="ex-card fade-in">
      ${r.audio_url ? `<button class="audio-btn" onclick="playAudio('${r.audio_url}', this)">🔊 Dengarkan</button>` : ''}
      <div class="flashcard" id="fc_${i}">
        <div class="flashcard-inner">
          <div class="flashcard-front">
            <p class="korean-text">${r.teks_korea || 'Klik untuk lihat arti'}</p>
            ${r.teks_inggris ? `<p class="hint-text">${r.teks_inggris}</p>` : ''}
            <p style="font-size:0.8rem;color:var(--teks-sekunder);margin-top:8px">Tap untuk balik</p>
          </div>
          <div class="flashcard-back">
            <p>Arti:</p>
            <p class="korean-text">${r.teks_indo || r.teks_korea || ''}</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

function initFlashcard(r, i) {
  const el = document.getElementById(`fc_${i}`);
  if (!el) return;
  el.addEventListener('click', () => el.classList.toggle('flipped'));
}

// ── Cocokkan ──
function renderCocokkanHTML(r, i) {
  return `
    <div class="ex-card fade-in">
      <p style="font-weight:600;margin-bottom:12px">🔗 Cocokkan pasangan berikut</p>
      ${r.audio_url ? `<button class="audio-btn" onclick="playAudio('${r.audio_url}', this)">🔊 Dengarkan</button>` : ''}
      <div class="match-grid" id="match_${i}"></div>
      <p id="matchStatus_${i}" class="hint-text" style="margin-top:8px">Tap item kiri, lalu tap pasangannya di kanan</p>
    </div>
  `;
}

function initCocokkan(r, i) {
  const grid = document.getElementById(`match_${i}`);
  if (!grid) return;

  let pairs = [];
  if (r.pasangan && typeof r.pasangan === 'object') {
    pairs = Object.entries(r.pasangan);
  } else if (r.teks_korea && r.teks_indo) {
    // Try to parse korea/indo from text
    const korean = (r.teks_korea || '').split('\n').filter(Boolean);
    const indo = (r.teks_indo || '').split('\n').filter(Boolean);
    const len = Math.min(korean.length, indo.length);
    if (len > 0) {
      pairs = korean.slice(0, len).map((k, j) => [k, indo[j]]);
    } else {
      pairs = [['Kosong (Kiri)', 'Kosong (Kanan)']];
    }
  } else {
    pairs = [['Contoh kata', 'Contoh arti']];
  }

  // Create shuffled left and right columns
  const leftItems = pairs.map((p, j) => ({ id: `l${j}`, text: p[0], pairId: j }));
  const rightItems = shuffleArray(pairs.map((p, j) => ({ id: `r${j}`, text: p[1], pairId: j })));

  let selected = null;
  let matched = new Set();

  function renderGrid() {
    grid.innerHTML = `
      <div>
        ${leftItems.map(item => `
          <div class="match-item ${matched.has(item.id) ? 'matched' : ''}" data-id="${item.id}" data-pair="${item.pairId}" data-side="left">${item.text}</div>
        `).join('')}
      </div>
      <div>
        ${rightItems.map(item => `
          <div class="match-item ${matched.has(item.id) ? 'matched' : ''}" data-id="${item.id}" data-pair="${item.pairId}" data-side="right">${item.text}</div>
        `).join('')}
      </div>
    `;

    grid.querySelectorAll('.match-item:not(.matched)').forEach(el => {
      el.addEventListener('click', () => handleClick(el));
    });
  }

  function handleClick(el) {
    if (matched.has(el.dataset.id)) return;
    const pairId = parseInt(el.dataset.pair);

    if (!selected) {
      selected = el;
      el.classList.add('selected');
      return;
    }

    // Already selected something
    if (selected.dataset.id === el.dataset.id) {
      selected.classList.remove('selected');
      selected = null;
      return;
    }

    const sPair = parseInt(selected.dataset.pair);
    const sSide = selected.dataset.side;
    const eSide = el.dataset.side;

    if (sSide === eSide) {
      // Same side - switch selection
      selected.classList.remove('selected');
      selected = el;
      el.classList.add('selected');
      return;
    }

    // Different sides - check match
    if (sPair === pairId) {
      matched.add(selected.dataset.id);
      matched.add(el.dataset.id);
      selected.classList.remove('selected');
      selected.classList.add('matched');
      el.classList.add('matched');
      selected = null;

      // Check completion
      if (matched.size === leftItems.length + rightItems.length) {
        document.getElementById(`matchStatus_${i}`).textContent = '✅ Semua benar!';
        markSeksiComplete(r.seksi);
      }
    } else {
      selected.classList.remove('selected');
      selected.classList.add('wrong');
      el.classList.add('wrong');
      setTimeout(() => {
        selected.classList.remove('wrong');
        el.classList.remove('wrong');
        selected = null;
      }, 400);
    }
  }

  renderGrid();
}

// ── Pilih Kata ──
function renderPilihKataHTML(r, i) {
  if (!r.teks_korea) return '';
  return `
    <div class="ex-card fade-in">
      <p style="font-weight:600;margin-bottom:12px">📝 Lengkapi kalimat</p>
      ${r.audio_url ? `<button class="audio-btn" onclick="playAudio('${r.audio_url}', this)">🔊 Dengarkan</button>` : ''}
      <div id="pilihKata_${i}">
        <div class="slot-row" id="slotRow_${i}"></div>
        <div class="word-grid" id="wordGrid_${i}"></div>
      </div>
      <button class="btn btn-outline" id="pilihCheck_${i}" style="display:none;margin-top:12px" onclick="checkPilihKata(${i})">Cek Jawaban</button>
    </div>
  `;
}

function initPilihKata(r, i) {
  const slotRow = document.getElementById(`slotRow_${i}`);
  const wordGrid = document.getElementById(`wordGrid_${i}`);
  if (!slotRow || !wordGrid) return;

  // Extract potential words from text
  const words = extractWords(r.teks_korea);
  const selectedWords = words.slice(0, Math.min(5, words.length));
  const blanks = selectedWords.slice(0, Math.min(3, selectedWords.length));
  const remaining = shuffleArray(selectedWords.concat(generateDistractors(selectedWords, 3)));

  wordState[i] = { blanks, words: remaining, filled: [], seksi: r.seksi };

  // Render slots
  const segments = segmentText(r.teks_korea, blanks);
  slotRow.innerHTML = segments.map(s => {
    if (s.blank) {
      return `<span class="word-slot" data-idx="${s.idx}" onclick="fillSlot(${i}, ${s.idx})"></span>`;
    }
    return s.text;
  }).join('');

  // Render word chips
  wordGrid.innerHTML = remaining.map((w, j) => `
    <span class="word-chip" data-word="${w}" data-idx="${j}" onclick="pickWord(${i}, this)">${w}</span>
  `).join('');

  // Show check button
  document.getElementById(`pilihCheck_${i}`).style.display = '';
}

function fillSlot(i, idx) {
  const slot = document.querySelector(`#slotRow_${i} .word-slot[data-idx="${idx}"]`);
  if (!slot || !slot.classList.contains('filled')) {
    // If slot is empty, do nothing (wait for word selection)
  }
}

window.pickWord = function(i, el) {
  const word = el.dataset.word;
  const state = wordState[i];
  if (!state) return;

  // Find first empty slot
  const slots = document.querySelectorAll(`#slotRow_${i} .word-slot:not(.filled)`);
  if (!slots.length) return;

  const slot = slots[0];
  const idx = slot.dataset.idx;
  slot.textContent = word;
  slot.classList.add('filled');
  slot.dataset.word = word;
  el.classList.add('used');

  state.filled.push(word);

  // Check if all filled
  const remainingEmpty = document.querySelectorAll(`#slotRow_${i} .word-slot:not(.filled)`).length;
  if (remainingEmpty === 0) {
    document.getElementById(`pilihCheck_${i}`).disabled = false;
  }
};

window.checkPilihKata = function(i) {
  const state = wordState[i];
  if (!state) return;
  markSeksiComplete(state.seksi || '');
  showToast('✅ Bagus! Lanjut ke materi berikutnya.', 'success');
};

// ── Dialog ──
function renderDialogHTML(r, i) {
  return `
    <div class="ex-card fade-in">
      <p style="font-weight:600;margin-bottom:12px">💬 Lengkapi percakapan</p>
      ${r.audio_url ? `<button class="audio-btn" onclick="playAudio('${r.audio_url}', this)">🔊 Dengarkan</button>` : ''}
      <div id="dialog_${i}"></div>
    </div>
  `;
}

function initDialog(r, i) {
  const el = document.getElementById(`dialog_${i}`);
  if (!el) return;

  let dialogData = [];
  if (r.dialog && Array.isArray(r.dialog)) {
    dialogData = r.dialog;
  } else {
    // Parse from text
    const lines = (r.teks_korea || '').split('\n').filter(Boolean);
    dialogData = lines.slice(0, 6).map((line, j) => ({
      speaker: j % 2 === 0 ? 'A' : 'B',
      text: line,
    }));
  }

  const blanks = dialogData.filter(d => d.text && d.text.includes('___'));
  const options = shuffleArray(blanks.map(b => {
    const parts = b.text.split('___');
    return parts[1] ? parts[1].trim() : '...';
  }));

  el.innerHTML = dialogData.map((d, j) => {
    const hasBlank = d.text && d.text.includes('___');
    return `
      <div class="dialog-bubble speaker-${d.speaker.toLowerCase()}">
        <div class="dialog-label">${d.speaker === 'A' ? 'A :' : 'B :'}</div>
        <p>${hasBlank ? d.text.replace('___', `<span class="blank-btn" data-idx="${j}" onclick="fillDialog(${i}, ${j})">??</span>`) : d.text}</p>
      </div>
    `;
  }).join('');

  el.innerHTML += `
    <div class="blank-options" id="dialogOpts_${i}">
      ${options.map((opt, j) => `<span class="blank-opt" data-opt="${opt}" onclick="pickDialogOpt(${i}, this)">${opt}</span>`).join('')}
    </div>
  `;
}

window.fillDialog = function(i, idx) {
  const btn = document.querySelector(`#dialog_${i} .blank-btn[data-idx="${idx}"]`);
  if (!btn || btn.classList.contains('filled')) return;

  // Show options - they're already visible
  const opts = document.querySelectorAll(`#dialogOpts_${i} .blank-opt:not(.used)`);
  if (!opts.length) return;

  btn.dataset.highlight = 'true';
};

window.pickDialogOpt = function(i, el) {
  const opt = el.dataset.opt;
  // Find highlighted blank
  const blanks = document.querySelectorAll(`#dialog_${i} .blank-btn:not(.filled)`);
  const highlighted = Array.from(blanks).find(b => b.dataset.highlight === 'true');

  // Fallback: fill first empty
  const target = highlighted || blanks[0];
  if (!target) return;

  target.textContent = opt;
  target.classList.add('filled');
  target.style.borderColor = '';
  target.dataset.highlight = '';
  el.classList.add('used');
};

// ── Answer MC (global handler) ──
window.answerMC = function(el) {
  const navId = el.dataset.q;
  const ans = el.dataset.ans;
  const correct = el.dataset.correct === 'true';
  const answer = el.dataset.answer;
  const state = quizState[navId];
  if (!state || state.answered) return;

  state.answered = true;
  const feedback = document.getElementById(`mcFeedback_${navId}`);
  const nextBtn = document.getElementById(`mcNext_${navId}`);

  // Disable all options
  el.closest('.mc-options').querySelectorAll('.mc-opt').forEach(o => {
    o.style.pointerEvents = 'none';
  });

  if (correct) {
    el.classList.add('correct');
    state.correct++;
    if (feedback) {
      feedback.className = 'mc-feedback show correct';
      feedback.textContent = '✅ Benar!';
    }
  } else {
    el.classList.add('wrong');
    // Highlight correct answer
    el.closest('.mc-options').querySelectorAll('.mc-opt').forEach(o => {
      if (o.dataset.ans === answer && !o.classList.contains('wrong')) {
        o.classList.add('correct');
      }
    });
    if (feedback) {
      feedback.className = 'mc-feedback show wrong';
      feedback.textContent = `❌ Jawaban benar: ${answer}`;
    }
  }

  if (nextBtn) nextBtn.style.display = '';
};

window.nextMC = function(navId) {
  const state = quizState[navId];
  const questions = window.__quizQuestions ? window.__quizQuestions[navId] : null;
  if (!state || !questions) return;

  state.idx++;
  state.answered = false;

  const el = document.getElementById(`content_${navId}`);
  if (!el) return;

  if (state.idx >= questions.length) {
    showQuizResult(el, navId);
    return;
  }

  renderQuestion(el, questions, navId, state.idx);
};

function showQuizResult(el, navId) {
  const state = quizState[navId];
  if (!state) return;
  const pct = state.total > 0 ? Math.round((state.correct / state.total) * 100) : 0;

  el.innerHTML = `
    <div class="mini-test-score fade-in">
      <h3>${pct >= 70 ? '🎉 Selamat!' : pct >= 40 ? '💪 Terus Semangat!' : '📚 Ayo Belajar Lagi!'}</h3>
      <div style="font-size:3rem;font-weight:700;color:${pct >= 70 ? 'var(--hijau-berhasil)' : pct >= 40 ? 'var(--kuning-sedang)' : 'var(--merah-salah)'}">${state.correct}/${state.total}</div>
      <p>(${pct}% benar)</p>
      <button class="btn btn-primary" style="margin-top:16px" onclick="location.reload()">Ulangi</button>
    </div>
  `;

  if (pct >= 70) {
    // Mark relevant seksi as complete
    const tab = NAV.find(t => t.id === navId);
    if (tab) tab.seksi.forEach(s => markSeksiComplete(s));
  }
}

// ── Audio ──
window.playAudio = function(url, btn) {
  if (!url) return;
  let audio = document.querySelector(`audio[data-src="${url}"]`);
  if (!audio) {
    audio = document.createElement('audio');
    audio.dataset.src = url;
    audio.src = url;
    document.body.appendChild(audio);
  }
  // Stop others
  document.querySelectorAll('audio').forEach(a => { if (a !== audio) a.pause(); });
  audio.currentTime = 0;
  audio.play().catch(e => console.warn('Audio play failed:', e));

  if (btn) {
    btn.classList.add('playing');
    audio.onended = () => btn.classList.remove('playing');
  }
};

// ── Progress ──
function markSeksiComplete(seksi) {
  if (!seksi || completedSeksi[seksi]) return;
  completedSeksi[seksi] = true;
  updateProgress();
  saveProgress();
}

function updateProgress() {
  const totalSeksi = new Set();
  NAV.forEach(t => t.seksi.forEach(s => totalSeksi.add(s)));
  const total = totalSeksi.size;
  const done = Object.keys(completedSeksi).filter(s => completedSeksi[s]).length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  const fill = document.getElementById('progressFill');
  const label = document.getElementById('progressLabel');
  if (fill) fill.style.width = pct + '%';
  if (label) label.textContent = `Unit ${currentUnit} — ${pct}% selesai`;
}

async function saveProgress() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    for (const [seksi, done] of Object.entries(completedSeksi)) {
      if (done) {
        await supabase.from('progress_unit').upsert({
          user_id: user.id,
          unit_id: currentUnit,
          seksi: seksi,
          completed: true,
          updated_at: new Date().toISOString(),
        }, { onConflict: 'user_id,unit_id,seksi' });
      }
    }
  } catch (e) {
    console.warn('Progress save failed:', e);
  }
}

// ── Utils ──
function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function extractWords(text) {
  // Extract Korean/words from text
  if (!text) return [];
  const lines = text.split('\n').filter(Boolean);
  // Use first few lines or words
  return lines.slice(0, 8);
}

function generateDistractors(words, count) {
  const distractors = ['???', '???', '???', '???', '???', '???'];
  return distractors.slice(0, count);
}

function segmentText(text, blanks) {
  // Split text and mark blank segments
  if (!blanks || !blanks.length) return [{ text: text || '' }];
  const result = [];
  let remaining = text || '';
  blanks.forEach((blank, idx) => {
    const pos = remaining.indexOf(blank);
    if (pos >= 0) {
      if (pos > 0) result.push({ text: remaining.slice(0, pos) });
      result.push({ blank: true, idx });
      remaining = remaining.slice(pos + blank.length);
    }
  });
  if (remaining) result.push({ text: remaining });
  return result;
}
