# Langit Korea - Firebase Setup Guide

## Setting up Firebase Authentication

To make the Google Sign-In work, you need to set up a Firebase project:

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or "Create a project"
3. Name it "Langit Korea" (or your preferred name)
4. Enable Google Analytics (optional)
5. Click "Create project"

### 2. Enable Google Authentication
1. In your Firebase project, go to **Authentication** section (left sidebar)
2. Click "Get started" or "Sign-in method"
3. Click "Add new provider"
4. Select "Google"
5. Enable it and configure:
   - Project support email: your-email@gmail.com
   - Project public facing name: "Langit Korea"
6. Save

### 3. Get Firebase Configuration
1. In Firebase project, click the **gear icon** ⚙ next to "Project Overview"
2. Select "Project settings"
3. Scroll down to "Your apps" section
4. Click the **</> (Web)** icon to add a web app
5. Register app with nickname "Langit Korea Web"
6. Copy the `firebaseConfig` object values

### 4. Update Configuration File
Open `js/auth/firebase-config.js` and replace the placeholder values:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyA...", // Replace with your actual API key
  authDomain: "langit-korea-xxxx.firebaseapp.com",
  projectId: "langit-korea-xxxx",
  storageBucket: "langit-korea-xxxx.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456..."
};
```

### 5. Enable Local Storage (for testing)
Since you're running locally (file:// protocol), you need to:
1. Use a local server (like Live Server in VS Code)
2. Or deploy to Firebase Hosting

**Quick local server options:**
- **VS Code**: Install "Live Server" extension, right-click `index.html` → "Open with Live Server"
- **Python**: Run `python -m http.server 8000` in project folder
- **Node.js**: Install `http-server` globally: `npm install -g http-server`, then run `http-server`

### 6. Test the Flow
1. Start your local server
2. Open `http://localhost:8000` (or whatever port)
3. You should be redirected to `onboarding.html`
4. Click "Continue with Google"
5. Sign in with your Google account
6. You should be redirected to `home.html` with your name displayed

## File Structure
```
Langit Korea/
├── index.html              # Entry point (redirects to onboarding)
├── onboarding.html         # Welcome page with auth check
├── login.html             # Login page (alternative)
├── home.html              # Dashboard (requires auth)
├── listening.html          # Listening practice
├── reading.html           # Reading practice
├── latihan-eps.html       # EPS practice
├── hangul-path.html        # Hangul learning
├── vocabulary.html         # Vocabulary builder
├── css/
│   └── style.css
├── js/
│   ├── auth/
│   │   └── firebase-config.js  # ← UPDATE THIS FILE
│   ├── reading.js
│   └── ...
└── assets/
    ├── audio/
    └── images/
```

## Troubleshooting

**Issue: "Firebase is not defined"**
- Make sure Firebase SDK scripts are loaded before `firebase-config.js`
- Check browser console for errors

**Issue: "Popup closed by user"**
- Popup blockers might interfere
- Try allowing popups for localhost

**Issue: "auth/operation-not-allowed"**
- Make sure Google provider is enabled in Firebase Console
- Verify OAuth client ID is configured

**Issue: Scores not showing on home page**
- Check browser localStorage (F12 → Application → Local Storage)
- Practice pages should save to: `listeningScore`, `readingScore`, `practiceScore`

## Next Steps
After Firebase is configured:
1. Add more questions to databases
2. Add real audio files for listening practice
3. Implement progress syncing to Firebase Firestore
4. Add user profile page
5. Deploy to Firebase Hosting for public access

Good luck! 🚀
