// Firebase Configuration
// TODO: Replace with your actual Firebase project config
const firebaseConfig = {
  apiKey: "AIzaSyA0iD5l8M03gwsFjlOaCUvNtVPXTqp-l-A",
  authDomain: "langit-korea.firebaseapp.com",
  projectId: "langit-korea",
  storageBucket: "langit-korea.firebasestorage.app",
  messagingSenderId: "495409650626",
  appId: "1:495409650626:web:5ba94f4c8fc6cbce0d945b",
  measurementId: "G-FE06K452H6",
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const provider = new firebase.auth.GoogleAuthProvider();

// Auth State Listener
auth.onAuthStateChanged((user) => {
  if (user) {
    // User is signed in
    console.log("User signed in:", user.displayName);
    localStorage.setItem(
      "user",
      JSON.stringify({
        uid: user.uid,
        name: user.displayName,
        email: user.email,
        photoURL: user.photoURL,
      }),
    );
  } else {
    // User is signed out
    console.log("User signed out");
    localStorage.removeItem("user");
  }
});

// Google Sign-In
function signInWithGoogle() {
  auth
    .signInWithPopup(provider)
    .then((result) => {
      const user = result.user;
      console.log("Sign-in successful:", user);
      window.location.href = "home.html"; // Redirect to home after login
    })
    .catch((error) => {
      console.error("Sign-in error:", error);
      alert("Login failed: " + error.message);
    });
}

// Sign Out
function signOut() {
  auth
    .signOut()
    .then(() => {
      console.log("Sign-out successful");
      window.location.href = "login.html";
    })
    .catch((error) => {
      console.error("Sign-out error:", error);
    });
}

// Check if user is logged in
function isLoggedIn() {
  return auth.currentUser !== null;
}

// Get current user
function getCurrentUser() {
  const userStr = localStorage.getItem("user");
  return userStr ? JSON.parse(userStr) : null;
}
