const chatLog = document.getElementById("chatLog");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const survey = document.getElementById("survey");
const ratingInput = document.getElementById("rating");
const commentsInput = document.getElementById("comments");
const submitFeedbackBtn = document.getElementById("submitFeedbackBtn");
const senderID = "user_" + Math.floor(Math.random() * 100000);
let messageCounter = 0;

function scrollChatToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function addMessageToChat(text, className) {
  const container = document.createElement("div");
  container.classList.add("message-container");
  text = marked.parse(text)
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

    feedbackDiv.innerHTML = `
      <button class="feedback-btn thumbs-up" onclick="submitMessageFeedback('${messageId}', 'positive')">👍</button>
      <button class="feedback-btn thumbs-down" onclick="submitMessageFeedback('${messageId}', 'negative')">👎</button>
    `;
    container.appendChild(feedbackDiv);
  }

  chatLog.appendChild(container);
  scrollChatToBottom();
}

function submitMessageFeedback(messageId, feedback) {
  const messageElement = document.querySelector(
    `[data-message-id="${messageId}"]`
  );
  const messageText = messageElement.textContent;
  const feedbackData = {
    message: messageText,
    feedback: feedback,
    timestamp: new Date().toISOString(),
  };

  // Send feedback to server
  fetch("http://localhost:5005/webhook/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedbackData),
  }).then(() => {
    // Update button styles
    const container = messageElement.parentElement;
    const buttons = container.querySelectorAll(".feedback-btn");
    buttons.forEach((btn) => btn.classList.remove("selected"));
    if (feedback === "positive") {
      container.querySelector(".thumbs-up").classList.add("selected");
    } else {
      container.querySelector(".thumbs-down").classList.add("selected");
    }
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

  fetch("http://localhost:5005/webhooks/rest/webhook", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((response) => response.json())
    .then((data) => {
      data.forEach((msgObj) => {
        if (msgObj.text) {
          addMessageToChat(msgObj.text, "botMsg");
        }
      });
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

  fetch("http://localhost:5005/webhooks/rest/webhook", {
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
  sendMessageToRasa("goodbye");
  showSurvey();
});
