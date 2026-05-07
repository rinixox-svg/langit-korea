// ============================================
// Langit Korea - Practice Page Integration
// Disesuaikan dengan struktur latihan-eps.html & listening.html
// ============================================

document.addEventListener("DOMContentLoaded", async function () {
  console.log("Practice page loaded, initializing...");

  if (!window.LangitDB) {
    console.error("LangitDB belum siap!");
    return;
  }

  const db = window.LangitDB;

  // ==========================================
  // 1. AMBIL PARAMETER URL
  // ==========================================
  const urlParams = new URLSearchParams(window.location.search);
  const unit = parseInt(urlParams.get("unit")) || 31;
  const tipe = urlParams.get("tipe") || "membaca";

  // Update UI
  const pageTitle = document.querySelector("h1");
  if (pageTitle) {
    pageTitle.innerHTML = `<i class="fas fa-language"></i> Latihan ${tipe === "membaca" ? "Membaca" : "Mendengarkan"}`;
  }

  // ==========================================
  // 2. CEK LOGIN
  // ==========================================
  const isLoggedIn = await db.cekUserLogin();
  if (!isLoggedIn) {
    const shouldRedirect = confirm(
      "Kamu belum login. Login untuk menyimpan progress?",
    );
    if (shouldRedirect) {
      window.location.href =
        "login.html?redirect=" + encodeURIComponent(window.location.href);
      return;
    }
  }

  // ==========================================
  // 3. AMBIL ELEMEN HTML
  // ==========================================
  const loadingEl = document.getElementById("loadingSpinner");
  const errorEl = document.getElementById("errorMessage");
  const cardEl = document.getElementById("questionCard");
  const questionTextEl = document.getElementById("questionText");
  const translationBtn = document.getElementById("toggleTranslationBtn");
  const translationEl = document.getElementById("questionTranslation");
  const questionImageEl = document.getElementById("questionImage");
  const optionsGridEl = document.getElementById("optionsGrid");
  const feedbackEl = document.getElementById("feedbackMessage");
  const explanationEl = document.getElementById("explanationText");
  const checkBtn = document.getElementById("checkAnswerBtn");
  const nextBtn = document.getElementById("nextQuestionBtn");
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  const scoreDisplay = document.getElementById("scoreDisplay");
  const completionEl = document.getElementById("completionMessage");
  const finalScoreEl = document.getElementById("finalScore");

  // ==========================================
  // 4. AMBIL SOAL DARI SUPABASE
  // ==========================================
  if (loadingEl) loadingEl.style.display = "block";
  if (cardEl) cardEl.style.display = "none";
  if (errorEl) errorEl.style.display = "none";
  if (completionEl) completionEl.style.display = "none";

  // Ambil 10 soal dari Supabase
  const soalList = await db.ambilSoalEPS(unit, tipe, 10);

  if (loadingEl) loadingEl.style.display = "none";

  if (!soalList || soalList.length === 0) {
    if (errorEl) {
      errorEl.innerHTML =
        '<i class="fas fa-exclamation-circle"></i> <span>Soal belum tersedia untuk unit ini.</span>';
      errorEl.style.display = "block";
    }
    return;
  }

  if (cardEl) cardEl.style.display = "block";

  // ==========================================
  // 5. STATE & VARIABEL
  // ==========================================
  let currentIndex = 0;
  let score = 0;
  let selectedOption = null;
  let canCheck = true;

  // ==========================================
  // 6. FUNGSI TAMPILKAN SOAL
  // ==========================================
  function tampilkanSoal(index) {
    if (index < 0 || index >= soalList.length) return;

    const soal = soalList[index];

    // Reset state
    selectedOption = null;
    canCheck = true;

    // Update progress
    const progress = ((index + 1) / soalList.length) * 100;
    if (progressBar) progressBar.style.width = progress + "%";
    if (progressText)
      progressText.textContent = `Soal ${index + 1}/${soalList.length}`;

    // Tampilkan teks soal
    if (questionTextEl) questionTextEl.textContent = soal.teks_soal;

    // Tampilkan terjemahan (jika ada)
    if (translationBtn && translationEl) {
      if (soal.teks_soal_id) {
        translationBtn.style.display = "block";
        translationEl.textContent = soal.teks_soal_id;
        translationEl.style.display = "none"; // Sembunyikan dulu
      } else {
        translationBtn.style.display = "none";
        translationEl.style.display = "none";
      }
    }

    // Tampilkan gambar (jika ada)
    if (questionImageEl) {
      if (soal.gambar_url) {
        questionImageEl.src = soal.gambar_url;
        questionImageEl.style.display = "block";
      } else {
        questionImageEl.style.display = "none";
      }
    }

    // Tampilkan pilihan
    if (optionsGridEl) {
      optionsGridEl.innerHTML = "";

      const pilihan = [
        { key: "a", text: soal.pilihan_a, img: soal.pilihan_a_gambar_url },
        { key: "b", text: soal.pilihan_b, img: soal.pilihan_b_gambar_url },
        { key: "c", text: soal.pilihan_c, img: soal.pilihan_c_gambar_url },
        { key: "d", text: soal.pilihan_d, img: soal.pilihan_d_gambar_url },
      ];

      pilihan.forEach((p) => {
        const btn = document.createElement("button");
        btn.className = "option-button";
        btn.setAttribute("data-jawaban", p.key);

        let content = "";
        if (p.img) {
          content += `<img src="${p.img}" alt="Gambar pilihan" style="max-width: 100px; max-height: 60px; margin-right: 10px;">`;
        }
        content += `<span>${p.key.toUpperCase()}. ${p.text}</span>`;
        btn.innerHTML = content;

        btn.addEventListener("click", function () {
          if (!canCheck) return;

          // Reset semua pilihan
          optionsGridEl.querySelectorAll(".option-button").forEach((b) => {
            b.classList.remove("selected");
          });

          // Pilih ini
          this.classList.add("selected");
          selectedOption = p.key;
        });

        optionsGridEl.appendChild(btn);
      });
    }

    // Sembunyikan feedback & penjelasan
    if (feedbackEl) {
      feedbackEl.style.display = "none";
      feedbackEl.className = "feedback-message";
    }
    if (explanationEl) explanationEl.style.display = "none";

    // Tombol
    if (checkBtn) {
      checkBtn.style.display = "flex";
      checkBtn.disabled = false;
    }
    if (nextBtn) nextBtn.style.display = "none";
  }

  // ==========================================
  // 7. EVENT LISTENER TOMBOL
  // ==========================================

  // Toggle Terjemahan
  if (translationBtn && translationEl) {
    translationBtn.addEventListener("click", function () {
      if (translationEl.style.display === "none") {
        translationEl.style.display = "block";
        this.innerHTML =
          '<i class="fas fa-language"></i> Sembunyikan Terjemahan';
      } else {
        translationEl.style.display = "none";
        this.innerHTML = '<i class="fas fa-language"></i> Tampilkan Terjemahan';
      }
    });
  }

  // Cek Jawaban
  if (checkBtn) {
    checkBtn.addEventListener("click", function () {
      if (!selectedOption || !canCheck) return;

      const soal = soalList[currentIndex];
      const benar = selectedOption === soal.jawaban;

      canCheck = false;
      this.disabled = true;

      // Tampilkan feedback
      if (feedbackEl) {
        feedbackEl.style.display = "block";
        if (benar) {
          feedbackEl.innerHTML =
            '<i class="fas fa-check-circle"></i> Benar! 🎉';
          feedbackEl.classList.add("correct");
          score++;
          if (scoreDisplay)
            scoreDisplay.innerHTML = `<i class="fas fa-star"></i> Skor: ${score}`;
        } else {
          feedbackEl.innerHTML = `<i class="fas fa-times-circle"></i> Salah. Jawaban benar: ${soal.jawaban.toUpperCase()}`;
          feedbackEl.classList.add("incorrect");
        }
      }

      // Tampilkan penjelasan
      if (explanationEl && soal.penjelasan) {
        explanationEl.textContent = soal.penjelasan;
        explanationEl.style.display = "block";
      }

      // Simpan progress ke DB
      if (isLoggedIn) {
        db.simpanProgress(soal.id, "eps", selectedOption, benar);
      }

      // Tampilkan tombol next atau selesai
      if (currentIndex < soalList.length - 1) {
        if (nextBtn) nextBtn.style.display = "flex";
      } else {
        // Selesai
        if (cardEl) cardEl.style.display = "none";
        if (completionEl) {
          completionEl.style.display = "block";
          if (finalScoreEl) finalScoreEl.textContent = score;
        }
      }
    });
  }

  // Soal Berikutnya
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      currentIndex++;
      tampilkanSoal(currentIndex);
    });
  }

  // ==========================================
  // 8. TAMPILKAN SOAL PERTAMA
  // ==========================================
  tampilkanSoal(currentIndex);

  console.log("Practice page initialization complete!");
});
