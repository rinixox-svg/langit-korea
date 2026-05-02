// Reading Practice - Now using Question Bank!
// Import question bank (if using Node.js) or copy-paste directly

// Use Question Bank from question-bank.js
const readingData = readingQuestionBank;

// Game State
let currentQuestion = 0;
let score = 0;
let userAnswers = new Array(readingData.length).fill(null);
let passageTranslated = false;
let questionTranslated = false;

// DOM Elements
const passageContent = document.getElementById("passageContent");
const passageTranslation = document.getElementById("passageTranslation");
const translatePassageBtn = document.getElementById("translatePassageBtn");
const questionText = document.getElementById("questionText");
const questionTranslation = document.getElementById("questionTranslation");
const translateQuestionBtn = document.getElementById("translateQuestionBtn");
const optionsContainer = document.getElementById("optionsContainer");
const questionNumber = document.getElementById("questionNumber");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const scoreDisplay = document.getElementById("scoreDisplay");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const resultModal = document.getElementById("resultModal");
const finalScore = document.getElementById("finalScore");
const resultMessage = document.getElementById("resultMessage");
const retryBtn = document.getElementById("retryBtn");
const homeBtn = document.getElementById("homeBtn");

// Initialize
function init() {
  loadQuestion();
  updateProgress();
  updateScore();
}

// Load Question
function loadQuestion() {
  const data = readingData[currentQuestion];

  // Reset translations
  passageTranslated = false;
  questionTranslated = false;
  passageTranslation.style.display = "none";
  questionTranslation.style.display = "none";
  translatePassageBtn.innerHTML = '<i class="fas fa-language"></i> Translate';
  translateQuestionBtn.innerHTML =
    '<i class="fas fa-language"></i> Translate Question';

  // Load passage
  passageContent.textContent = data.passage;

  // Show/hide image if available (positioned after passage)
  const imageContainer = document.getElementById("imageContainer");
  const questionImage = document.getElementById("questionImage");
  if (data.image && data.image.trim() !== "") {
    questionImage.src = data.image;
    imageContainer.style.display = "block";
  } else {
    imageContainer.style.display = "none";
  }

  // Load question
  questionText.textContent = data.question;
  questionNumber.textContent = `Question ${currentQuestion + 1}`;

  // Load options
  optionsContainer.innerHTML = "";
  data.options.forEach((option, index) => {
    const button = document.createElement("button");
    button.className = "option-btn";
    if (userAnswers[currentQuestion] === index) {
      button.classList.add("selected");
      if (index === data.correct) {
        button.classList.add("correct");
      } else {
        button.classList.add("incorrect");
      }
    }
    button.textContent = `${index + 1}. ${option}`;
    button.onclick = () => selectOption(index);
    optionsContainer.appendChild(button);
  });

  // Update navigation buttons
  prevBtn.disabled = currentQuestion === 0;
  nextBtn.innerHTML =
    currentQuestion === readingData.length - 1
      ? 'Finish <i class="fas fa-check"></i>'
      : 'Next <i class="fas fa-chevron-right"></i>';
}

// Select Option
function selectOption(index) {
  if (userAnswers[currentQuestion] !== null) return; // Already answered

  userAnswers[currentQuestion] = index;
  const data = readingData[currentQuestion];

  // Update score
  if (index === data.correct) {
    score++;
    updateScore();
  }

  // Update UI
  const options = optionsContainer.querySelectorAll(".option-btn");
  options.forEach((btn, i) => {
    btn.classList.add("selected");
    if (i === data.correct) {
      btn.classList.add("correct");
    } else if (i === index && i !== data.correct) {
      btn.classList.add("incorrect");
    }
  });
}

// Navigation
prevBtn.onclick = () => {
  if (currentQuestion > 0) {
    currentQuestion--;
    loadQuestion();
    updateProgress();
  }
};

nextBtn.onclick = () => {
  if (currentQuestion < readingData.length - 1) {
    currentQuestion++;
    loadQuestion();
    updateProgress();
  } else {
    showResult();
  }
};

// Translate Passage
translatePassageBtn.onclick = () => {
  const data = readingData[currentQuestion];
  if (!passageTranslated) {
    passageTranslation.textContent = data.translation.passage;
    passageTranslation.style.display = "block";
    translatePassageBtn.innerHTML =
      '<i class="fas fa-eye-slash"></i> Hide Translation';
    passageTranslated = true;
  } else {
    passageTranslation.style.display = "none";
    translatePassageBtn.innerHTML = '<i class="fas fa-language"></i> Translate';
    passageTranslated = false;
  }
};

// Translate Question
translateQuestionBtn.onclick = () => {
  const data = readingData[currentQuestion];
  if (!questionTranslated) {
    questionTranslation.textContent = data.translation.question;
    questionTranslation.style.display = "block";
    translateQuestionBtn.innerHTML =
      '<i class="fas fa-eye-slash"></i> Hide Translation';
    questionTranslated = true;
  } else {
    questionTranslation.style.display = "none";
    translateQuestionBtn.innerHTML =
      '<i class="fas fa-language"></i> Translate Question';
    questionTranslated = false;
  }
};

// Update Progress
function updateProgress() {
  const progress = ((currentQuestion + 1) / readingData.length) * 100;
  progressBar.style.width = `${progress}%`;
  progressText.textContent = `Question ${currentQuestion + 1}/${readingData.length}`;
}

// Update Score
function updateScore() {
  scoreDisplay.textContent = `Score: ${score}`;
}

// Show Result
function showResult() {
  finalScore.textContent = score;

  let message = "";
  const percentage = (score / readingData.length) * 100;
  if (percentage >= 90) {
    message = "Excellent! You're ready for the EPS-TOPIK!";
  } else if (percentage >= 70) {
    message = "Good job! Keep practicing to improve!";
  } else if (percentage >= 50) {
    message = "Not bad! Try again to get a better score!";
  } else {
    message = "Keep studying! You can do better!";
  }
  resultMessage.textContent = message;

  // Save score to localStorage
  localStorage.setItem("readingScore", score);

  // Save to history
  const history = JSON.parse(localStorage.getItem("quizHistory") || "[]");
  history.push({
    type: "Reading",
    score: score,
    total: readingData.length,
    date: new Date().toISOString(),
  });
  localStorage.setItem("quizHistory", JSON.stringify(history));

  resultModal.style.display = "flex";
}

// Retry
retryBtn.onclick = () => {
  currentQuestion = 0;
  score = 0;
  userAnswers = new Array(readingData.length).fill(null);
  resultModal.style.display = "none";
  updateScore();
  loadQuestion();
  updateProgress();
};

// Go Home
homeBtn.onclick = () => {
  window.location.href = "home.html";
};

// Initialize the app
init();
