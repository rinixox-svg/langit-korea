// extract-unit31.js - Extract text & images from PDF
// Run: node extract-unit31.js

const fs = require('fs');
const pdf = require('pdf-parse'); // npm install pdf-parse

const PDF_PATH = 'assets/unit_31_attire_work_attitude.pdf';
const OUTPUT_JSON = 'assets/unit31-data.json';
const OUTPUT_TEXT = 'assets/unit31-text.txt';

async function extractPDF() {
    try {
        console.log('Loading PDF:', PDF_PATH);

        // Read PDF
        const dataBuffer = fs.readFileSync(PDF_PATH);
        const data = await pdf(dataBuffer);

        console.log('PDF loaded. Pages:', data.numpages);
        console.log('Extracting text...');

        // Save raw text
        fs.writeFileSync(OUTPUT_TEXT, data.text);
        console.log('Text saved to:', OUTPUT_TEXT);

        // Analyze structure (simple heuristic for EPS-TOPIK)
        const text = data.text;
        const lines = text.split('\n')
            .map(l => l.trim())
            .filter(l => l.length > 0);

        // Find questions (heuristic: lines with numbers, Korean text)
        const questions = [];
        let currentQuestion = null;

        lines.forEach((line, index) => {
            // Detect question start (e.g., "1.", "1)", "Question 1")
            if (line.match(/^(\d+[\.\)]|Question\s+\d+)/i)) {
                if (currentQuestion) {
                    questions.push(currentQuestion);
                }
                currentQuestion = {
                    number: line.match(/\d+/)?.[0] || (questions.length + 1),
                    rawText: line,
                    content: []
                };
            } else if (currentQuestion && line.length > 5) {
                currentQuestion.content.push(line);
            }
        });

        if (currentQuestion) {
            questions.push(currentQuestion);
        }

        // Save structure
        fs.writeFileSync(OUTPUT_JSON, JSON.stringify(questions, null, 2));
        console.log('Structure saved to:', OUTPUT_JSON);
        console.log('Found questions:', questions.length);

        // Print first 3 questions as sample
        questions.slice(0, 3).forEach((q, i) => {
            console.log(`\n=== Question ${i+1} ===`);
            console.log('Number:', q.number);
            console.log('Raw:', q.rawText);
            console.log('Content:', q.content.slice(0, 3).join(' | '));
        });

    } catch (error) {
        console.error('Error:', error.message);
        console.log('\nManual extraction needed:');
        console.log('1. Open PDF in browser');
        console.log('2. Copy text for questions');
        console.log('3. Format like readingQuestionBank format');
    }
}

extractPDF();
