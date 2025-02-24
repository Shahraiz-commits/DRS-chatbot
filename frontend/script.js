const chatLog = document.getElementById("chatLog");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const survey = document.getElementById("survey");
const ratingInput = document.getElementById("rating");
const commentsInput = document.getElementById("comments");
const submitFeedbackBtn = document.getElementById("submitFeedbackBtn");
const senderID = "user_" + Math.floor(Math.random() * 100000);
let messageCounter = 0;

LOCAL_LINK = "http://localhost:5005/webhooks/rest/webhook";
PROD_LINK =
  "https://rasa-chatbot-42751455718.us-east1.run.app/webhooks/rest/webhook";

function scrollChatToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function addMessageToChat(text, className) {
  const container = document.createElement("div");
  container.classList.add("message-container");

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
  const buttons = messageContainer.querySelectorAll(".feedback-btn");

  // Reset all buttons
  buttons.forEach((btn) => btn.classList.remove("selected"));

  // Select clicked button
  messageContainer
    .querySelector(feedbackType === "positive" ? ".thumbs-up" : ".thumbs-down")
    .classList.add("selected");

  // Show input wrapper
  feedbackWrapper.style.display = "flex";

  // Style based on feedback type
  if (feedbackType === "positive") {
    textInput.classList.remove("negative");
    textInput.classList.add("positive");
    textInput.placeholder = "Enter your positive feedback...";
  } else {
    textInput.classList.remove("positive");
    textInput.classList.add("negative");
    textInput.placeholder = "Enter your negative feedback...";
  }

  // Add submit handler
  const submitBtn = messageContainer.querySelector(".submit-feedback-btn");
  submitBtn.onclick = () =>
    submitMessageFeedback(messageId, feedbackType, textInput.value);
}

function submitMessageFeedback(messageId, feedback, feedbackText) {
  const messageElement = document.querySelector(
    `[data-message-id="${messageId}"]`
  );
  const messageText = messageElement.textContent;
  const feedbackData = {
    message: messageText,
    feedback: feedback,
    feedbackText: feedbackText,
    timestamp: new Date().toISOString(),
  };

  // Send feedback to server
  fetch(
    "https://rasa-chatbot-42751455718.us-east1.run.app/webhooks/rest/webhook/feedback",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedbackData),
    }
  ).then(() => {
    // Hide input wrapper after submission
    const container = messageElement.parentElement;
    const feedbackWrapper = container.querySelector(".feedback-input-wrapper");
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
  });
}

// initial greeting
document.addEventListener("DOMContentLoaded", () => {
  sendMessageToRasa("/greet");
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

function showSurvey() {
  survey.style.display = "block";
}

function submitFeedback() {
  const rating = ratingInput.value;
  const comments = commentsInput.value;

  if (!rating || rating < 1 || rating > 5) {
    alert("Please provide a valid rating between 1 and 5.");
    return;
  }

  const feedbackPayload = {
    sender: senderID,
    message: `/rate_experience{"rating": "${rating}", "comments": "${comments}"}`,
  };

  fetch(LOCAL_LINK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedbackPayload),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Feedback submitted:", data);
      survey.style.display = "none";
      ratingInput.value = "";
      commentsInput.value = "";
      addMessageToChat("Thank you for your feedback!", "botMsg");
    })
    .catch((err) => console.error("Error:", err));
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
