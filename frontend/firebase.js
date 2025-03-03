import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-analytics.js";
import {
  getFirestore,
  collection,
  addDoc,
} from "https://www.gstatic.com/firebasejs/9.22.1/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyDOxApOTKHFJAOuGbVMUytu7q4IzCu6TGk",
  authDomain: "drs-chatbot.firebaseapp.com",
  projectId: "drs-chatbot",
  storageBucket: "drs-chatbot.firebasestorage.app",
  messagingSenderId: "425418688280",
  appId: "1:425418688280:web:02670aceb91ecccc7ec06d",
  measurementId: "G-Z73V709CN8",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// Initialize Firestore
const db = getFirestore(app);

export async function saveMessageFeedback(feedbackData) {
  try {
    const docRef = await addDoc(
      collection(db, "messageFeedback"),
      feedbackData
    );
    console.log("Message feedback saved with ID:", docRef.id);
  } catch (error) {
    console.error("Error saving message feedback:", error);
    throw error;
  }
}

export async function saveSurveyFeedback(feedbackData) {
  try {
    const docRef = await addDoc(collection(db, "surveyFeedback"), feedbackData);
    console.log("Survey feedback saved with ID:", docRef.id);
  } catch (error) {
    console.error("Error saving survey feedback:", error);
    throw error;
  }
}
