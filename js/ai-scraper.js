/**
 * AI Question Scraper for Langit Korea
 *
 * WHAT IT DOES:
 * 1. Fetches questions from G2G Korea (manual input or API)
 * 2. Auto-translates to Indonesian (using free APIs)
 * 3. Formats and saves to `js/question-bank.js`
 *
 * HOW TO USE:
 * 1. Install Node.js: https://nodejs.org/ (if not installed)
 * 2. Run: node js/ai-scraper.js
 * 3. Follow the prompts!
 */

const fs = require("fs");
const https = require("https");

// ====================
// CONFIGURATION
// ====================
const CONFIG = {
  // G2G Korea URL (example)
  g2gUrl: "https://g2gkorea.com/eps-topik/",

  // Output file
  outputFile: "js/question-bank.js",

  // Free translation API (choose one):
  // Option 1: MyMemory (free, no key): https://mymemory.com/
  // Option 2: LibreTranslate (free, open source): https://libretranslate.com/
  translationApi: "https://api.mymemory.translation.io/get",

  // Number of questions to generate
  questionCount: 10,
};

// ====================
// TRANSLATION FUNCTION (FREE - No API key needed!)
// ====================
async function translateToIndonesian(text) {
  return new Promise((resolve, reject) => {
    const params = new URLSearchParams({
      q: text,
      langpair: "ko|id", // Korean to Indonesian
    });

    https
      .get(`${CONFIG.translationApi}?${params}`, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            const json = JSON.parse(data);
            // MyMemory API response format
            const translated =
              json.responseData?.translatedText || json.response;
            resolve(translated || text);
          } catch (e) {
            console.log("Translation failed, using original text");
            resolve(text); // Fallback to original
          }
        });
      })
      .on("error", (err) => {
        console.log("Translation error:", err.message);
        resolve(text); // Fallback to original
      });
  });
}

// ====================
// QUESTION FORMATTER
// ====================
function formatQuestion(
  koreanPassage,
  koreanQuestion,
  options,
  correctIndex,
  indonesianPassage,
  indonesianQuestion,
  indonesianOptions,
) {
  return {
    passage: koreanPassage,
    question: koreanQuestion,
    options: options,
    correct: correctIndex,
    translation: {
      passage: indonesianPassage,
      question: indonesianQuestion,
      options: indonesianOptions,
    },
  };
}

// ====================
// MAIN FUNCTION: Manual Entry with Auto-Translation
// ====================
async function main() {
  console.log("🚀 Langit Korea - AI Question Scraper");
  console.log("====================================");
  console.log("");
  console.log("Instructions:");
  console.log("1. Go to: https://g2gkorea.com/eps-topik/");
  console.log("2. Copy Korean text (passage, question, options)");
  console.log("3. Paste below when prompted");
  console.log("4. AI will auto-translate to Indonesian!");
  console.log("");

  const readline = require("readline").createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const questionBank = [];
  let count = 0;

  function askQuestion() {
    if (count >= CONFIG.questionCount) {
      saveToFile(questionBank);
      console.log(
        `\n✅ Done! ${count} questions saved to ${CONFIG.outputFile}`,
      );
      readline.close();
      return;
    }

    console.log(`\n--- Question ${count + 1} of ${CONFIG.questionCount} ---`);

    readline.question("Paste Korean passage: ", async (passage) => {
      readline.question("Paste Korean question: ", async (question) => {
        readline.question("Option A (Korean): ", (optA) => {
          readline.question("Option B (Korean): ", (optB) => {
            readline.question("Option C (Korean): ", (optC) => {
              readline.question("Option D (Korean): ", (optD) => {
                readline.question(
                  "Correct answer (0=A, 1=B, 2=C, 3=D): ",
                  async (correct) => {
                    console.log("\n⏳ Translating to Indonesian...");

                    try {
                      const [
                        passageId,
                        questionId,
                        optAId,
                        optBId,
                        optCId,
                        optDId,
                      ] = await Promise.all([
                        translateToIndonesian(passage),
                        translateToIndonesian(question),
                        translateToIndonesian(optA),
                        translateToIndonesian(optB),
                        translateToIndonesian(optC),
                        translateToIndonesian(optD),
                      ]);

                      const formatted = formatQuestion(
                        passage,
                        question,
                        [optA, optB, optC, optD],
                        parseInt(correct),
                        passageId,
                        questionId,
                        [optAId, optBId, optCId, optDId],
                      );

                      questionBank.push(formatted);
                      console.log("✅ Question added!");
                      count++;
                      askQuestion(); // Ask next question
                    } catch (e) {
                      console.error("❌ Translation error:", e.message);
                      askQuestion();
                    }
                  },
                );
              });
            });
          });
        });
      });
    });
  }

  askQuestion();
}

// ====================
// SAVE TO FILE
// ====================
function saveToFile(questionBank) {
  const content = `/**
 * Auto-generated Question Bank for Langit Korea
 * Generated by: ai-scraper.js
 * Total questions: ${questionBank.length}
 */

const readingQuestionBank = ${JSON.stringify(questionBank, null, 4)};

// For use in reading.js:
// const readingData = readingQuestionBank;

module.exports = { readingQuestionBank };
`;

  fs.writeFileSync(CONFIG.outputFile, content);
  console.log(`\n💾 File saved: ${CONFIG.outputFile}`);
}

// ====================
// RUN
// ====================
main().catch(console.error);
