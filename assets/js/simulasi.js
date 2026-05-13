import { supabase } from './supabase.js';
import { navigateTo, showToast } from './utils.js';

const STORAGE_KEY = 'langitkorea_simulasi_state';

export const Simulasi = {
  questions: [],
  state: null,
  timer: null,
  currentAudio: null,
  letters: ['A','B','C','D'],

  async init() {
    const params = new URLSearchParams(location.search);
    const year = parseInt(params.get('year')) || 2023;
    
    document.getElementById('yearSelect').value = year;
    document.getElementById('yearSelect').addEventListener('change', () => this.loadQuestions());

    await this.loadQuestions();
  },

  async loadQuestions() {
    const year = parseInt(document.getElementById('yearSelect').value);
    const loading = document.getElementById('loadingDiv');
    const errorDiv = document.getElementById('errorDiv');

    loading.style.display = 'block';
    errorDiv.style.display = 'none';

    try {
      const { data, error } = await supabase
        .from('soal_eps')
        .select('*')
        .eq('sumber', 'open_test')
        .eq('tahun_soal', year)
        .order('nomor_asli', { ascending: true });

      if (error) throw error;
      if (!data || data.length === 0) throw new Error('No questions found');

      this.questions = data;

      // Check for saved state
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.year === year && !parsed.submitted) {
          if (confirm('Ada sesi simulasi sebelumnya. Lanjutkan?')) {
            this.restoreState(parsed);
            loading.style.display = 'none';
            return;
          } else {
            localStorage.removeItem(STORAGE_KEY);
          }
        }
      }

      this.startNewSession(year);
      loading.style.display = 'none';
    } catch (e) {
      console.error('Load error:', e);
      loading.style.display = 'none';
      errorDiv.style.display = 'block';
    }
  },

  startNewSession(year) {
    const questions = [...this.questions];
    // Shuffle reading (1-20) but keep listening (21-40) sequential
    const reading = questions.filter(q => q.nomor_asli <= 20);
    const listening = questions.filter(q => q.nomor_asli > 20);
    this.shuffleArray(reading);
    reading.sort((a, b) => a.nomor_asli - b.nomor_asli); // Keep reading sequential too for realism
    listening.sort((a, b) => a.nomor_asli - b.nomor_asli);

    this.state = {
      year,
      answers: {},
      currentIndex: 0,
      submitted: false,
      readingCount: reading.length,
      listeningCount: listening.length,
      timeRemaining: 50 * 60, // 50 minutes
      startTime: Date.now(),
    };

    this.saveState();
    this.render();
    this.startTimer();
  },

  restoreState(saved) {
    this.state = saved;
    this.render();
    if (!saved.submitted && saved.timeRemaining > 0) {
      this.startTimer();
    }
    if (saved.submitted) {
      this.showResults();
    }
  },

  saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
  },

  render() {
    const container = document.getElementById('questionArea');
    const nav = document.getElementById('simNav');
    const timerBar = document.getElementById('timerBar');
    const navBtns = document.getElementById('navButtons');
    const submitBtn = document.getElementById('submitBtn');

    timerBar.style.display = 'block';
    nav.style.display = 'flex';

    // Render nav dots
    nav.innerHTML = this.questions.map((q, i) => `
      <button class="sim-nav-btn ${this.state.answers[q.nomor_asli] ? 'answered' : ''} ${i === this.state.currentIndex ? 'active' : ''}" 
        onclick="Simulasi.goTo(${i})" ${this.state.submitted ? 'disabled' : ''}>
        ${q.nomor_asli}
      </button>
    `).join('');

    // Render current question
    const q = this.questions[this.state.currentIndex];
    const idx = this.state.currentIndex;
    const isListening = q.tipe === 'mendengarkan';
    const selected = this.state.answers[q.nomor_asli] || '';
    const letters = this.letters;

    container.innerHTML = `
      <div class="question-card active fade-in">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:6px">
          <span class="section-badge ${q.tipe}">${isListening ? '🔊 Mendengarkan' : '📖 Membaca'}</span>
          <span style="font-size:0.85rem;color:var(--teks-sekunder)">Soal ${q.nomor_asli}</span>
        </div>

        ${isListening && q.audio_url ? `
          <button class="audio-btn" onclick="Simulasi.playAudio('${q.audio_url}', this)">
            🔊 Putar Audio
          </button>
        ` : ''}

        ${q.gambar_url ? this.renderImage(q.gambar_url) : ''}

        ${q.audio_teks ? `<details style="margin-bottom:12px"><summary style="cursor:pointer;color:var(--teks-sekunder);font-size:0.85rem">Lihat teks dialog</summary><p class="q-text">${q.audio_teks}</p></details>` : ''}

        <p class="q-text">${q.teks_soal || 'Soal tidak tersedia'}</p>

        <div class="mc-options">
          ${[
            { label: 'A', text: q.pilihan_a },
            { label: 'B', text: q.pilihan_b },
            { label: 'C', text: q.pilihan_c },
            { label: 'D', text: q.pilihan_d }
          ].filter(o => o.text).map(o => `
            <div class="mc-option ${selected === o.label.toLowerCase() ? 'selected' : ''}" 
              onclick="Simulasi.selectAnswer(${q.nomor_asli}, '${o.label.toLowerCase()}')"
              ${this.state.submitted ? 'style="pointer-events:none"' : ''}>
              <span class="mc-letter">${o.label}</span>
              <span>${o.text}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Update progress
    const answered = Object.keys(this.state.answers).length;
    document.getElementById('progressText').textContent = `Soal ${idx + 1}/${this.questions.length}`;
    document.getElementById('simProgress').style.width = `${(answered / this.questions.length) * 100}%`;

    // Update badge for reading/listening phase
    const badge = document.getElementById('sectionBadge');
    if (idx < this.state.readingCount) {
      badge.textContent = 'Membaca';
      badge.className = 'section-badge membaca';
    } else {
      badge.textContent = 'Mendengarkan';
      badge.className = 'section-badge mendengarkan';
    }

    // Nav buttons
    document.getElementById('prevBtn').style.display = idx > 0 ? '' : 'none';
    document.getElementById('nextBtn').textContent = idx < this.questions.length - 1 ? 'Berikutnya →' : 'Lihat Hasil';
    document.getElementById('nextBtn').style.display = '';
    submitBtn.style.display = idx === this.questions.length - 1 && !this.state.submitted ? '' : 'none';
  },

  renderImage(gambarUrl) {
    try {
      const urls = JSON.parse(gambarUrl);
      return urls.map(u => `<img src="${u}" class="q-image" alt="Gambar soal" onerror="this.style.display='none'">`).join('');
    } catch {
      return `<img src="${gambarUrl}" class="q-image" alt="Gambar soal" onerror="this.style.display='none'">`;
    }
  },

  selectAnswer(nomor, answer) {
    if (this.state.submitted) return;
    this.state.answers[nomor] = answer;
    this.saveState();
    this.render();
    // Auto-play audio for listening after answer
    const q = this.questions.find(q => q.nomor_asli === nomor);
    if (q && q.tipe === 'mendengarkan' && q.audio_url) {
      this.playAudio(q.audio_url);
    }
  },

  goTo(index) {
    if (this.state.submitted) return;
    this.state.currentIndex = index;
    this.saveState();
    this.render();
  },

  prev() {
    if (this.state.currentIndex > 0) {
      this.state.currentIndex--;
      this.saveState();
      this.render();
    }
  },

  next() {
    if (this.state.currentIndex < this.questions.length - 1) {
      this.state.currentIndex++;
      this.saveState();
      this.render();
    } else if (!this.state.submitted) {
      this.submit();
    }
  },

  async submit() {
    if (this.state.submitted) return;
    if (!confirm('Submit simulasi? Jawaban tidak bisa diubah lagi.')) return;

    this.stopTimer();
    this.state.submitted = true;
    this.state.endTime = Date.now();
    this.saveState();

    await this.saveProgress();
    this.showResults();
  },

  showResults() {
    const container = document.getElementById('questionArea');
    const nav = document.getElementById('simNav');
    const timerBar = document.getElementById('timerBar');
    const navBtns = document.getElementById('navButtons');

    const answers = this.state.answers;
    let correct = 0;
    let readingCorrect = 0;
    let listeningCorrect = 0;
    const reviewItems = [];

    this.questions.forEach(q => {
      const userAns = answers[q.nomor_asli] || '-';
      const isCorrect = userAns === q.jawaban;
      if (isCorrect) {
        correct++;
        if (q.tipe === 'membaca') readingCorrect++;
        else listeningCorrect++;
      }
      reviewItems.push({ q, userAns, isCorrect });
    });

    const total = this.questions.length;
    const pct = Math.round((correct / total) * 100);
    const passed = pct >= 60;
    const elapsed = this.state.startTime ? Math.round((Date.now() - this.state.startTime) / 60000) : 50;

    document.getElementById('navButtons').style.display = 'none';

    container.innerHTML = `
      <div class="result-screen fade-in">
        <div style="font-size:4rem;margin-bottom:8px">${passed ? '🎉' : '💪'}</div>
        <h2>${passed ? 'Selamat!' : 'Terus Semangat!'}</h2>
        <div class="result-score" style="color:${passed ? 'var(--hijau-berhasil)' : 'var(--merah-salah)'}">${pct}%</div>
        <p style="color:var(--teks-sekunder)">${correct}/${total} benar (${passed ? '✅ LULUS' : '❌ TIDAK LULUS'})</p>
        <p style="color:var(--teks-sekunder);font-size:0.85rem">Waktu: ${elapsed} menit</p>

        <div class="result-detail">
          <div class="result-stat">
            <div class="result-stat-value" style="color:var(--langit-biru)">${readingCorrect}/${this.state.readingCount}</div>
            <div style="font-size:0.8rem;color:var(--teks-sekunder)">Membaca</div>
          </div>
          <div class="result-stat">
            <div class="result-stat-value" style="color:var(--langit-fajar)">${listeningCorrect}/${this.state.listeningCount}</div>
            <div style="font-size:0.8rem;color:var(--teks-sekunder)">Mendengarkan</div>
          </div>
        </div>

        <button class="btn btn-outline" onclick="document.getElementById('reviewSection').style.display='block'">📋 Lihat Review</button>
        <button class="btn btn-primary" onclick="location.reload()" style="margin-left:8px">🔄 Ulangi</button>
        <button class="btn btn-secondary" onclick="Simulasi.goToDashboard()" style="margin-left:8px">🏠 Dashboard</button>
      </div>

      <div id="reviewSection" style="display:none;margin-top:24px">
        <h3 style="margin-bottom:12px">📋 Review Jawaban</h3>
        <div class="review-list">
          ${reviewItems.map(({ q, userAns, isCorrect }) => `
            <div style="background:white;border-radius:10px;padding:14px;margin-bottom:8px;border-left:4px solid ${isCorrect ? 'var(--hijau-berhasil)' : 'var(--merah-salah)'}">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                <strong>Soal ${q.nomor_asli}</strong>
                <span class="section-badge ${q.tipe}">${q.tipe === 'membaca' ? '📖' : '🔊'} ${q.tipe}</span>
              </div>
              <p style="font-size:0.85rem;margin:6px 0;font-family:var(--font-korea)">${(q.teks_soal || '').slice(0,120)}</p>
              <div style="font-size:0.85rem">
                <span>Jawabanmu: <strong style="color:${isCorrect ? 'var(--hijau-berhasil)' : 'var(--merah-salah)'}">${userAns.toUpperCase()}</strong></span>
                ${!isCorrect ? ` | <span>Jawaban benar: <strong style="color:var(--hijau-berhasil)">${(q.jawaban || '-').toUpperCase()}</strong></span>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  },

  async saveProgress() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const answers = this.state.answers;
      let correct = 0;
      this.questions.forEach(q => {
        if (answers[q.nomor_asli] === q.jawaban) correct++;
      });

      await supabase.from('progress_unit').upsert({
        user_id: user.id,
        unit_id: 0,
        seksi: 'simulasi',
        skor: correct,
        completed: true,
        completed_at: new Date().toISOString(),
      }, { onConflict: 'user_id,unit_id,seksi' });
    } catch (e) {
      console.warn('Save progress failed:', e);
    }
  },

  startTimer() {
    this.stopTimer();
    this.timer = setInterval(() => {
      this.state.timeRemaining--;
      this.saveState();

      const display = document.getElementById('timerDisplay');
      const mins = Math.floor(this.state.timeRemaining / 60);
      const secs = this.state.timeRemaining % 60;
      display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

      display.className = 'timer-display' + (mins < 5 ? ' warning' : mins < 10 ? ' caution' : '');

      if (this.state.timeRemaining <= 0) {
        this.stopTimer();
        alert('Waktu habis!');
        this.submit();
      }
    }, 1000);
  },

  stopTimer() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  },

  playAudio(url, btn) {
    if (!url) return;
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    const audio = new Audio(url);
    this.currentAudio = audio;
    audio.play().catch(e => console.warn('Audio play failed:', e));
    if (btn) {
      btn.classList.add('playing');
      audio.onended = () => btn.classList.remove('playing');
    }
  },

  shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  },

  goToDashboard() {
    localStorage.removeItem(STORAGE_KEY);
    navigateTo('dashboard.html');
  },
};

// Assign to window for onclick handlers
window.Simulasi = Simulasi;

// Init
(async function() {
  try {
    await Simulasi.init();
  } catch (e) {
    console.error('Simulasi init error:', e);
    document.getElementById('loadingDiv').style.display = 'none';
    document.getElementById('errorDiv').style.display = 'block';
  }
})();
