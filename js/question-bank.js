/**
 * Question Bank Generator for Langit Korea
 * Source: G2G Korea (https://g2gkorea.com/)
 *
 * HOW TO USE:
 * 1. Copy questions from G2G Korea website
 * 2. Paste them below in the format shown
 * 3. Run the converter (or manually format them)
 */

// ====================
// READING QUESTIONS (Tebakan Bacaan)
// ====================
const readingQuestionBank = [
  // ===== ADD YOUR QUESTIONS BELOW =====
  // Just copy-paste from G2G Korea and format like above!

  // Question 1
  {
    passage:
      "저는 한국에서 3년 동안 일했습니다. 공장에서 기계를 다루는 일을 했습니다. 처음에는 힘들었지만, 지금은 적응해서 즐겁게 일하고 있습니다. 한국 음식 중에서 김치찌개를 가장 좋아합니다.",
    question: "이 사람은 한국에서 무엇을 했습니까?",
    options: [
      "식당에서 요리했습니다",
      "공장에서 기계를 다루는 일을 했습니다",
      "학교에서 한국어를 가르쳤습니다",
      "병원에서 일했습니다",
    ],
    correct: 1,
    translation: {
      passage:
        "Saya telah bekerja di Korea selama 3 tahun. Saya bekerja menangani mesin di pabrik. Awalnya sulit, tetapi sekarang saya sudah beradaptasi dan bekerja dengan senang. Dari makanan Korea, saya paling suka kimchi jjigae.",
      question: "Apa yang dilakukan orang ini di Korea?",
      options: [
        "Memasak di restoran",
        "Bekerja menangani mesin di pabrik",
        "Mengajar bahasa Korea di sekolah",
        "Bekerja di rumah sakit",
      ],
    },
  },

  // Question 2
  {
    passage:
      "내일은 일요일입니다. 나는 친구들과 같이 영화를 보러 갈 것입니다. 우리는 액션 영화를 좋아합니다. 영화를 보고 나서 맛있는 저녁을 먹을 것입니다.",
    question: "내일 무엇을 할 것입니까?",
    options: [
      "친구들과 영화를 보러 갈 것입니다",
      "집에서 쉴 것입니다",
      "회사에 갈 것입니다",
      "한국어를 공부할 것입니다",
    ],
    correct: 0,
    translation: {
      passage:
        "Besok adalah hari Minggu. Saya akan pergi menonton film bersama teman-teman. Kami suka film aksi. Setelah menonton film, kami akan makan malam yang enak.",
      question: "Apa yang akan dilakukan besok?",
      options: [
        "Akan pergi menonton film bersama teman",
        "Akan istirahat di rumah",
        "Akan pergi ke kantor",
        "Akan belajar bahasa Korea",
      ],
    },
  },

  // Question 3
  {
    passage:
      "한국의 대중교통은 매우 편리합니다. 지하철과 버스가 정확하게 운행됩니다. 아침 출근 시간에는 사람이 많지만, 전반적으로 이용하기 쉽습니다.",
    question: "한국의 대중교통에 대한 설명으로 맞는 것은 무엇입니까?",
    options: [
      "버스만 운행됩니다",
      "항상 사람이 적습니다",
      "정확하게 운행되어 편리합니다",
      "이용하기 어렵습니다",
    ],
    correct: 2,
    translation: {
      passage:
        "Transportasi umum Korea sangat nyaman. Kereta bawah tanah dan bus beroperasi dengan tepat waktu. Meskipun jam berangkat pagi banyak orang, secara keseluruhan mudah digunakan.",
      question:
        "Manakah penjelasan yang benar tentang transportasi umum Korea?",
      options: [
        "Hanya bus yang beroperasi",
        "Selalu sedikit orang",
        "Beroperasi tepat waktu sehingga nyaman",
        "Sulit digunakan",
      ],
    },
  },

  // Question 4
  {
    passage:
      "저는 매일 아침 6시에 일어납니다. 세수하고 간단한 아침을 먹습니다. 그 다음 한국어 단어를 30개씩 외웁니다. 매일 꾸준히 하면 실력이 늘 것입니다.",
    question: "이 사람은 매일 아침 무엇을 합니까?",
    options: [
      "운동을 합니다",
      "한국어 단어를 30개씩 외웁니다",
      "영화를 봅니다",
      "늦잠을 잡니다",
    ],
    correct: 1,
    translation: {
      passage:
        "Saya bangun setiap pagi jam 6. Cuci muka dan makan sarapan sederhana. Lalu menghafal 30 kosakata bahasa Korea setiap hari. Jika dilakukan setiap hari dengan konsisten, kemampuan akan meningkat.",
      question: "Apa yang dilakukan orang ini setiap pagi?",
      options: [
        "Berolahraga",
        "Menghafal 30 kosakata bahasa Korea",
        "Menonton film",
        "Tidur telat",
      ],
    },
  },

  // Question 5
  {
    passage:
      "한국 사람들은 김치를 매우 좋아합니다. 매일 식사할 때 김치를 먹습니다. 김치는 배추로 만들고 고추장을 넣어서 맵습니다. 건강에도 아주 좋습니다.",
    question: "김치에 대한 설명으로 틀린 것은 무엇입니까?",
    options: [
      "한국 사람들이 매우 좋아합니다",
      "매일 식사할 때 먹습니다",
      "단맛이 있습니다",
      "건강에 좋습니다",
    ],
    correct: 2,
    translation: {
      passage:
        "Orang Korea sangat suka kimchi. Setiap kali makan, mereka makan kimchi. Kimchi dibuat dari kubis dan ditambah pasta cabai sehingga pedas. Sangat baik untuk kesehatan.",
      question: "Manakah penjelasan tentang kimchi yang SALAH?",
      options: [
        "Orang Korea sangat menyukainya",
        "Dimakan setiap kali makan",
        "Memiliki rasa manis",
        "Baik untuk kesehatan",
      ],
    },
  },
];

// ====================
// LISTENING QUESTIONS (Tebakan Mendengarkan)
// ====================
const listeningQuestionBank = [
  // Question 1 - Track 001
  {
    id: 1,
    type: "listening",
    questionText: "다음을 듣고 내용과 관계있는 그림을 고르십시오.",
    options: [
      {
        text: "Gambar A - Perpustakaan",
        image: "assets/images/listening1a.jpg",
      },
      { text: "Gambar B - Sekolah", image: "assets/images/listening1b.jpg" },
      { text: "Gambar C - Taman", image: "assets/images/listening1c.jpg" },
      { text: "Gambar D - Pasar", image: "assets/images/listening1d.jpg" },
    ],
    correctAnswer: 0, // 0-3 (A=0, B=1, C=2, D=3)
    explanation: "Audio menyebutkan tentang '도서관' (perpustakaan).",
    audioUrl: "assets/audio/listening1.mp3",
  },

  // Question 2 - Track 002
  {
    id: 2,
    type: "listening",
    questionText: "다음을 듣고 이어지는 말로 알맞은 것을 고르십시오.",
    options: [
      { text: "네, 알겠습니다." },
      { text: "죄송합니다." },
      { text: "감사합니다." },
      { text: "네, 괜찮습니다." },
    ],
    correctAnswer: 0,
    explanation:
      "Jika audio adalah instruksi, jawaban '네, 알겠습니다.' adalah respons yang paling tepat.",
    audioUrl: "assets/audio/listening2.mp3",
  },

  // Question 3 - Track 003
  {
    id: 3,
    type: "listening",
    questionText: "이야기를 듣고 질문에 알맞은 대답을 고르십시오.",
    options: [
      { text: "공항에 갑니다." },
      { text: "버스를 기다립니다." },
      { text: "지하철을 탑니다." },
      { text: "친구를 만납니다." },
    ],
    correctAnswer: 2,
    explanation: "Dari cerita, dijelaskan mereka naik kereta bawah tanah.",
    audioUrl: "assets/audio/listening3.mp3",
  },
];

// ====================
// EXPORT FOR USE IN OTHER FILES
// ====================
// In reading.js, replace: const readingData = readingQuestionBank;
// In listening.html, question bank is loaded via <script src="js/question-bank.js"></script>

console.log("Question Bank Ready!");
console.log("Reading questions:", readingQuestionBank.length);
console.log("Listening questions:", listeningQuestionBank.length);
