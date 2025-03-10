import { saveMessageFeedback, saveSurveyFeedback } from "./firebase.js";

const chatLog = document.getElementById("chatLog");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const survey = document.getElementById("survey");
const ratingInput = document.getElementById("rating");
const commentsInput = document.getElementById("comments");
const submitFeedbackBtn = document.getElementById("submitFeedbackBtn");
const senderID = "user_" + Math.floor(Math.random() * 100000);
let lastUserQuestion = "";
let messageCounter = 0;

const LOCAL_LINK = "http://localhost:5005/webhooks/rest/webhook";
const PROD_LINK =
  "https://rasa-chatbot-42751455718.us-east1.run.app/webhooks/rest/webhook";

function scrollChatToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function addMessageToChat(text, className) {
  const container = document.createElement("div");
  container.classList.add("message-container");

  // For bot messages, store the last user question as a data attribute
  if (className === "botMsg") {
    container.setAttribute("data-user-question", lastUserQuestion);
  }

  // Preserve intentional paragraph breaks while removing extra newlines
  // Replace 2 or more newlines with exactly 2 newlines
  text = text.replace(/\n{3,}/g, "\n\n").trim();
  text = marked.parse(text);

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", className);
  // Replace full URLs with link icons
  const formattedText = text.replace(
    /<a href='([^']+)'[^>]*>([^<]+)<\/a>/g,
    (match, url, text) =>
      `<a href='${url}' target='_blank'>Visit Resource <img src='link-icon.png' class='link-icon' alt='Link'/></a>`
  );
  messageDiv.innerHTML = formattedText;
  container.appendChild(messageDiv);

  if (className === "botMsg") {
    const feedbackDiv = document.createElement("div");
    feedbackDiv.classList.add("feedback-buttons");
    const messageId = `msg_${messageCounter++}`;
    messageDiv.setAttribute("data-message-id", messageId);

    const feedbackContainer = document.createElement("div");
    feedbackContainer.classList.add("feedback-container");

    feedbackDiv.innerHTML = `
      <div class="feedback-buttons-wrapper">
        <button class="feedback-btn thumbs-up" onclick="handleFeedbackClick('${messageId}', 'positive')">👍</button>
        <button class="feedback-btn thumbs-down" onclick="handleFeedbackClick('${messageId}', 'negative')">👎</button>
      </div>
      <div class="feedback-input-wrapper" style="display: none;">
        <input type="text" class="feedback-text-input" placeholder="">
        <button class="submit-feedback-btn">Submit</button>
      </div>
    `;
    container.appendChild(feedbackDiv);
  }

  chatLog.appendChild(container);
  scrollChatToBottom();
}

function handleFeedbackClick(messageId, feedbackType) {
  const messageContainer = document.querySelector(
    `[data-message-id="${messageId}"]`
  ).parentElement;
  const feedbackWrapper = messageContainer.querySelector(
    ".feedback-input-wrapper"
  );
  const textInput = messageContainer.querySelector(".feedback-text-input");
  const targetBtn = messageContainer.querySelector(
    feedbackType === "positive" ? ".thumbs-up" : ".thumbs-down"
  );

  // Toggle off if already selected
  if (targetBtn.classList.contains("selected")) {
    targetBtn.classList.remove("selected");
    feedbackWrapper.style.display = "none";
    return;
  }

  const buttons = messageContainer.querySelectorAll(".feedback-btn");
  buttons.forEach((btn) => btn.classList.remove("selected"));

  targetBtn.classList.add("selected");
  feedbackWrapper.style.display = "flex";

  // Scroll the chat down to ensure feedback input is visible
  scrollChatToBottom();

  if (feedbackType === "positive") {
    textInput.classList.remove("negative");
    textInput.classList.add("positive");
    textInput.placeholder = "Enter your positive feedback...";
  } else {
    textInput.classList.remove("positive");
    textInput.classList.add("negative");
    textInput.placeholder = "Enter your negative feedback...";
  }

  const submitBtn = messageContainer.querySelector(".submit-feedback-btn");
  submitBtn.onclick = () =>
    submitMessageFeedback(messageId, feedbackType, textInput.value);
}

function submitMessageFeedback(messageId, feedback, feedbackText) {
  if (feedbackText === "") return;
  const messageElement = document.querySelector(
    `[data-message-id="${messageId}"]`
  );
  const messageText = messageElement.textContent;
  const messageContainer = messageElement.parentElement;
  const userQuestion =
    messageContainer.getAttribute("data-user-question") || "";
  const feedbackData = {
    feedback: feedback,
    feedbackText: feedbackText,
    question: userQuestion,
    response: messageText,
  };

  // Save feedback to Firebase
  saveMessageFeedback(feedbackData)
    .then(() => {
      // Hide input wrapper after submission
      const container = messageElement.parentElement;
      const feedbackWrapper = container.querySelector(
        ".feedback-input-wrapper"
      );
      feedbackWrapper.style.display = "none";

      // Show thank you message
      const thankYouMsg = document.createElement("div");
      thankYouMsg.classList.add("feedback-thank-you");
      thankYouMsg.textContent = "Thank you for your feedback!";
      feedbackWrapper.parentElement.appendChild(thankYouMsg);

      // Remove thank you message after 3 seconds
      setTimeout(() => {
        thankYouMsg.remove();
      }, 3000);
    })
    .catch((error) => {
      console.error("Error saving message feedback:", error);
    });
}

function submitFeedback() {
  const rating = ratingInput.value;
  const comments = commentsInput.value;
  if (comments === "") return;
  if (!rating || rating < 1 || rating > 5) {
    alert("Please provide a valid rating between 1 and 5.");
    return;
  }

  // Construct survey feedback data
  const feedbackData = {
    rating: rating,
    feedback: comments,
    sender: senderID,
  };

  // Save survey feedback to Firebase
  saveSurveyFeedback(feedbackData)
    .then(() => {
      console.log("Survey feedback submitted to Firebase");
      survey.style.display = "none";
      ratingInput.value = "";
      commentsInput.value = "";
      addMessageToChat("Thank you for your feedback!", "botMsg");
    })
    .catch((error) => {
      console.error("Error saving survey feedback:", error);
    });
}

// initial greeting and adding survey close button
document.addEventListener("DOMContentLoaded", () => {
  sendMessageToRasa("/greet");

  // Ensure the survey modal has a close (X) button in the survey-content
  const surveyModal = document.querySelector(".survey-modal");
  if (surveyModal) {
    const surveyContent = surveyModal.querySelector(".survey-content");
    if (surveyContent && !surveyContent.querySelector("#closeSurveyBtn")) {
      const closeBtn = document.createElement("button");
      closeBtn.id = "closeSurveyBtn";
      closeBtn.innerHTML = "X";
      surveyContent.appendChild(closeBtn);
      closeBtn.addEventListener("click", () => {
        surveyModal.style.display = "none";
      });
    }
  }
});

// quick action btns
document.querySelectorAll(".actionBtn").forEach((button) => {
  button.addEventListener("click", () => {
    const query = button.dataset.query;
    userInput.value = query;
    sendMessageToRasa(query);
  });
});

function sendMessageToRasa(message) {
  const isIntent = message.startsWith("/");
  const payload = {
    sender: senderID,
    message: message,
  };

  if (!isIntent) {
    userInput.value = "";
    // Store the user question globally
    lastUserQuestion = message;
    addMessageToChat(message, "userMsg");
  }

  fetch(LOCAL_LINK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((response) => response.json())
    .then((data) => {
      // Combine all text responses into a single message
      // Preserve original spacing between messages
      const combinedText = data
        .filter((msgObj) => msgObj.text)
        .map((msgObj) => msgObj.text)
        .join("\n\n");

      if (combinedText) {
        addMessageToChat(combinedText, "botMsg");
      }
    })
    .catch((err) => console.error("Error:", err));
}

// brooooooooooooo css is booty
function showSurvey() {
  // Instead of manually setting top, left, transform, etc, rely on CSS for centering
  survey.style.display = "flex";
}

// Event Listeners
sendBtn.addEventListener("click", () => {
  const message = userInput.value.trim();
  if (message) {
    sendMessageToRasa(message);
  }
});

userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    const message = userInput.value.trim();
    if (message) {
      sendMessageToRasa(message);
    }
  }
});

submitFeedbackBtn.addEventListener("click", submitFeedback);

// End chat button functionality
document.getElementById("endChatBtn").addEventListener("click", () => {
  showSurvey();
});

// Expose handleFeedbackClick to the global scope for inline event handlers
window.handleFeedbackClick = handleFeedbackClick;
