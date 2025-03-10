import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-analytics.js";
import {
  getFirestore,
  collection,
  addDoc,
  setDoc,
  doc,
} from "https://www.gstatic.com/firebasejs/9.22.1/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyB2o6nc-wshofHBGDUik6qIehZCmOO2YF8",
  authDomain: "drs-chatbot-75b67.firebaseapp.com",
  projectId: "drs-chatbot-75b67",
  storageBucket: "drs-chatbot-75b67.firebasestorage.app",
  messagingSenderId: "721902099793",
  appId: "1:721902099793:web:cf812adb9ff75702038770",
  measurementId: "G-XDYMZY4K3E",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// Initialize Firestore
const db = getFirestore(app);

export async function saveMessageFeedback(feedbackData) {
  try {
    const currentTime = new Date().toISOString();
    await setDoc(doc(db, "messageFeedback", currentTime), feedbackData);
    console.log("Message feedback saved with ID:", currentTime);
  } catch (error) {
    console.error("Error saving message feedback:", error);
    throw error;
  }
}

export async function saveSurveyFeedback(feedbackData) {
  try {
    const currentTime = new Date().toISOString();
    await setDoc(doc(db, "surveyFeedback", currentTime), feedbackData);
    console.log("Survey feedback saved with ID:", currentTime);
  } catch (error) {
    console.error("Error saving survey feedback:", error);
    throw error;
  }
}

