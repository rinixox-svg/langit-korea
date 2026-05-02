// pdf-processor.js - Extract text from PDF for AI analysis
// Run: node pdf-processor.js

const fs = require('fs');
const pdf = require('pdf-parse'); // npm install pdf-parse

const PDF_PATH = 'assets/EPS-TOPIK tdxfkg tlnkxzmz_2xt(npmxhvuw tdxfkg)(25.06.ionk).pdf';
const OUTPUT_TEXT = 'assets/modul-content.txt';
const OUTPUT_JSON = 'assets/modul-structure.json';

// Check if pdf-parse is installed
try {
    require.resolve('pdf-parse');
} catch (e) {
    console.log('Installing pdf-parse...');
    require('child_process').execSync('npm install pdf-parse', { stdio: 'inherit' });
}

async function extractPDF() {
    try {
        const dataBuffer = fs.readFileSync(PDF_PATH);

        const data = await pdf(dataBuffer);

        console.log('PDF loaded. Pages:', data.numpages);

        // Extract text
        fs.writeFileSync(OUTPUT_TEXT, data.text);
        console.log('Text extracted to:', OUTPUT_TEXT);

        // Analyze structure (simple AI-like analysis)
        const text = data.text;
        const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);

        // Find chapters/sections (simple heuristic)
        const chapters = [];
        let currentChapter = null;

        lines.forEach((line, index) => {
            // Detect chapter headings (heuristic)
            if (line.match(/^Bab\s+\d+/i) || line.match(/^Chapter\s+\d+/i)) {
                if (currentChapter) {
                    chapters.push(currentChapter);
                }
                currentChapter = {
                    title: line,
                    startLine: index,
                    content: []
                };
            } else if (currentChapter && line.length > 10) {
                currentChapter.content.push(line);
            }
        });

        if (currentChapter) {
            chapters.push(currentChapter);
        }

        // Save structure
        fs.writeFileSync(OUTPUT_JSON, JSON.stringify(chapters, null, 2));
        console.log('Structure saved to:', OUTPUT_JSON);
        console.log('Found chapters:', chapters.length);

    } catch (error) {
        console.error('Error:', error.message);
        console.log('\nAlternative: Manual extraction');
        console.log('1. Open PDF in browser');
        console.log('2. Copy text manually');
        console.log('3. Save to assets/modul-content.txt');
    }
}

extractPDF();
