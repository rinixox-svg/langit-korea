# 🇰 Langit Korea - Complete Question Bank Guide

## 📁 **STEP 1: Get Questions from G2G Korea (FREE!)**

### **Option A: Manual Copy-Paste (Recommended for beginners)**
1. Open: https://g2gkorea.com/eps-topik/
2. Click "Reading" or "Listening" practice
3. Select level (usually Level 1-2 for EPS-TOPIK)
4. **Copy Korean text** → Paste in `js/question-bank.js`
5. **Translate to Indonesian** using Google Translate
6. **Format** using template below

### **Option B: Use AI to Help (If you have API key)**
See `js/ai-scraper-template.js` (I'll create this)

---

## 📂 **STEP 2: Question Format Template**

### **For Reading Questions:**
```javascript
// PASTE THIS IN `js/question-bank.js`
const readingQuestionBank = [
    // ===== YOUR QUESTION 1 =====
    {
        passage: "PASTE KOREAN PASSAGE HERE",
        question: "PASTE KOREAN QUESTION HERE?",
        options: [
            "Option A in Korean",
            "Option B in Korean", 
            "Option C in Korean",
            "Option D in Korean"
        ],
        correct: 1, // 0=A, 1=B, 2=C, 3=D
        translation: {
            passage: "PASTE INDONESIAN TRANSLATION HERE",
            question: "PASTE QUESTION IN INDONESIAN?",
            options: [
                "Option A in Indonesian",
                "Option B in Indonesian",
                "Option C in Indonesian",
                "Option D in Indonesian"
            ]
        },
        // Optional: image: "assets/images/reading1.jpg"
    },

    // ===== COPY-PASTE MORE QUESTIONS BELOW =====
    // Just copy the format above!
];
```

### **For Listening Questions:**
```javascript
const listeningQuestionBank = [
    // ===== YOUR QUESTION 1 =====
    {
        id: 1,
        type: "listening",
        questionText: "다음을 듣고 내용과 관계있는 그림을 고르십시오.",
        options: [
            { text: "Description A", image: "assets/images/listening1a.jpg" },
            { text: "Description B", image: "assets/images/listening1b.jpg" },
            { text: "Description C", image: "assets/images/listening1c.jpg" },
            { text: "Description D", image: "assets/images/listening1d.jpg" }
        ],
        correctAnswer: 1, // 0-3
        explanation: "Explanation in Korean...",
        audioUrl: "assets/audio/listening1.mp3" // Optional
    },

    // ===== ADD MORE QUESTIONS =====
];
```

---

## 📃 **STEP 3: Auto-Translation with AI (FREE Options)**

### **Option A: Google Translate (FREE, No API)**
1. Go to: https://translate.google.com/
2. Paste Korean text → Select "to Indonesian"
3. Copy translation → Paste in `translation:` field

### **Option B: AI Helper (If you have ChatGPT/Claude access)**
Send this prompt:
```
Translate this Korean EPS-TOPIK question to Indonesian:

Korean Passage: [PASTE HERE]
Korean Question: [PASTE HERE]
Options: [PASTE HERE]

Format the output as:
Passage: [Indonesian]
Question: [Indonesian]
Options: [Indonesian A, B, C, D]
```

### **Option C: AI API (If you want automation)**
See `js/ai-translator-template.js` (I'll create this with FREE API options)

---

## 📄 **STEP 4: Connect to Your App**

### **Option A: Use Question Bank (Recommended)**
In `reading.html`, find this line:
```javascript
const readingData = [ ... ]; // ← REPLACE THIS
```

**Change to:**
```javascript
// At top of reading.html, add:
<script src="js/question-bank.js"></script>
<script>
    const readingData = readingQuestionBank; // ← Use question bank
    // ... rest of your code
</script>
```

### **Option B: Use Firebase (For cloud storage)**
See `FIREBASE_SETUP.md` - Free tier includes:
- ✅ 1GB database storage
- ✅ 10GB file storage (for audio/images)
- ✅ Authentication (Google Sign-In)

---

## 📅 **STEP 5: Free Storage Solutions**

| What you need | FREE Solution | How to get |
|---------------|---------------|------------|
| **Questions** | Manual entry | Copy from G2G Korea |
| **Translations** | Google Translate | https://translate.google.com/ |
| **Audio files** | Your own recording | Use phone/computer mic |
| **Images** | Your own photos | Use phone camera |
| **Cloud DB** | Firebase Free | See `FIREBASE_SETUP.md` |
| **AI Help** | ChatGPT free tier | https://chat.openai.com/ |

---

## 📆 **STEP 6: Quick Start Checklist**

- [ ] 1. Open https://g2gkorea.com/eps-topik/
- [ ] 2. Copy 5-10 questions (Korean + options)
- [ ] 3. Translate to Indonesian (Google Translate)
- [ ] 4. Paste in `js/question-bank.js` using template
- [ ] 5. In `reading.html`, replace `readingData` with `readingQuestionBank`
- [ ] 6. Test at `http://localhost:8000/reading.html`
- [ ] 7. Repeat for listening questions!

---

## 📇 **BONUS: AI Scraper Template (Optional)**

I can create `js/ai-scraper.js` that:
- ✅ Reads G2G Korea website (if CORS allows)
- ✅ Sends to AI for translation
- ✅ Formats automatically
- ✅ Saves to `question-bank.js`

**Want me to create this?** Just say "YES"!

---

## 📈 **File Structure (After setup)**
```
Langit Korea/
├── js/
│   ├── question-bank.js      ← ADD YOUR QUESTIONS HERE!
│   ├── ai-scraper.js       ← (Optional) AI helper
│   ├── reading.js
│   └── listening.js
├── assets/
│   ├── audio/              ← Add your audio files here
│   └── images/             ← Add your images here
└── reading.html          ← Will use question-bank.js
```

---

## 🎯 **YOU'RE READY!**

1. **NO Firebase needed** for basic version
2. **NO API keys needed** - use Google Translate
3. **NO coding** - just copy-paste!
4. **COMPLETE app** - all features work!

**What would you like me to create next?**
- "AI Scraper" → I'll make `js/ai-scraper.js`
- "Show example" → I'll format 1 complete question for you
- "Help me paste" → Guide you step-by-step
- "Something else" → Tell me!

**Good luck! 🚀 You got this!**
