/**
 * firebase.js
 * Initializes Firebase Web SDK with Google Authentication for MEDexplain AI.
 */

// Firebase configuration provided for MEDexplain AI
const firebaseConfig = {
  apiKey: "AIzaSyDPuzXxmha1-CI_Ur-ge_JC3LwI2fSm3io",
  authDomain: "blood-report-ai-9caf7.firebaseapp.com",
  projectId: "blood-report-ai-9caf7",
  storageBucket: "blood-report-ai-9caf7.firebasestorage.app",
  messagingSenderId: "1083615932376",
  appId: "1:1083615932376:web:47941cd69b86fc8ce08cad",
  measurementId: "G-QXX994R849"
};

// Initialize Firebase App
let app;
let auth;
let googleProvider;

try {
  if (typeof firebase !== 'undefined') {
    app = firebase.initializeApp(firebaseConfig);
    auth = firebase.auth();
    googleProvider = new firebase.auth.GoogleAuthProvider();
    googleProvider.setCustomParameters({ prompt: 'select_account' });
    console.log("MEDexplain AI: Firebase Auth initialized successfully.");
  } else {
    console.warn("Firebase SDK script not loaded yet.");
  }
} catch (error) {
  console.error("Firebase Initialization Error:", error);
}
