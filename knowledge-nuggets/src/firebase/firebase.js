// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
import { getDatabase } from "firebase/database";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAgiblJpVISM371D6-0NH0txmNgMqSnJ4c",
  authDomain: "knowledge-nuggets.firebaseapp.com",
  projectId: "knowledge-nuggets",
  storageBucket: "knowledge-nuggets.firebasestorage.app",
  messagingSenderId: "947446377751",
  appId: "1:947446377751:web:8b2f5d861b3c08ec98db52",
  measurementId: "G-SF4NLTQ414",
  databaseURL:
    "https://knowledge-nuggets-default-rtdb.asia-southeast1.firebasedatabase.app/",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);
const db = getDatabase(app);

export { app, auth, db };
