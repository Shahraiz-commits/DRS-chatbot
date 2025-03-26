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

function addMessageToChat(text, ...classNames) {
  const container = document.createElement("div");
  container.classList.add("message-container");

  // For bot messages, store the last user question as a data attribute
  if (classNames.includes("botMsg")) {
    container.setAttribute("data-user-question", lastUserQuestion);
  }

  text = text.replace(/\n{3,}/g, "\n\n").trim();
  const parsedHtml = marked.parse(text);

  const formattedText = parsedHtml.replace(
    /<a href='([^']+)'[^>]*>([^<]+)<\/a>/g,
    (match, url, linkText) =>
      `<a href='${url}' target='_blank'>Visit Resource <img src='link-icon.png' class='link-icon' alt='Link'/></a>`
  );

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", ...classNames);

  const shouldAddExtras = classNames.includes("botMsg") &&
    !parsedHtml.startsWith("<p>Sorry,") &&
    !parsedHtml.startsWith("<p>Thank you for your feedback!") &&
    !classNames.includes("errorMsg");

  if (shouldAddExtras) {
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content-preview');
    contentDiv.innerHTML = formattedText;
    messageDiv.appendChild(contentDiv);

    const controlsDiv = document.createElement('div');
    controlsDiv.classList.add('message-controls');
    controlsDiv.style.display = 'none';

    const showMoreBtn = document.createElement('button');
    showMoreBtn.classList.add('show-more-btn');
    showMoreBtn.textContent = 'Show more';
    showMoreBtn.onclick = () => {
      messageDiv.classList.toggle('expanded');
      showMoreBtn.textContent = messageDiv.classList.contains('expanded') ? 'Show less' : 'Show more';
      if (chatLog && container === chatLog.lastElementChild) {
        setTimeout(scrollChatToBottom, 50);
      }
    };
    controlsDiv.appendChild(showMoreBtn);
    messageDiv.appendChild(controlsDiv);

    setTimeout(() => {
      if (contentDiv.scrollHeight > contentDiv.clientHeight + 5) {
        controlsDiv.style.display = 'block';
      }
    }, 0);

    const messageId = `msg_${messageCounter++}`;
    messageDiv.setAttribute("data-message-id", messageId);

    container.appendChild(messageDiv);

    const feedbackDiv = document.createElement("div");
    feedbackDiv.classList.add("feedback-buttons");

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

  } else {
    messageDiv.innerHTML = formattedText;
    container.appendChild(messageDiv);
  }

  chatLog.appendChild(container);
  scrollChatToBottom(); // Scroll after adding any message
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

function displayAlternativeButtons(data) {
  addMessageToChat("Sorry, I am a bit unsure. Please choose one of the options below:", "botMsg");

  const optionsContainer = document.createElement("div");
  optionsContainer.classList.add("alternative-options-container");

  const startIndex1 = data.findIndex(msg => msg.text?.includes("[1]"));
  const startIndex2 = data.findIndex(msg => msg.text?.includes("[2]"));
  const startIndex3 = data.findIndex(msg => msg.text?.includes("[3]"));
  const endIndex = data.findIndex(msg => msg.text?.startsWith("Did any of these"));
  const effectiveEndIndex = endIndex === -1 ? data.length : endIndex;

  const optionsData = [];
  if (startIndex1 !== -1) {
    const endSlice1 = startIndex2 !== -1 ? startIndex2 : (startIndex3 !== -1 ? startIndex3 : effectiveEndIndex);
    optionsData.push({ number: 1, messages: data.slice(startIndex1 + 1, endSlice1) });
  }
  if (startIndex2 !== -1) {
    const endSlice2 = startIndex3 !== -1 ? startIndex3 : effectiveEndIndex;
    optionsData.push({ number: 2, messages: data.slice(startIndex2 + 1, endSlice2) });
  }
  if (startIndex3 !== -1) {
    optionsData.push({ number: 3, messages: data.slice(startIndex3 + 1, effectiveEndIndex) });
  }

  optionsData.forEach(option => {
    const card = document.createElement("div");
    card.classList.add("option-card");

    const combinedText = option.messages
      .map(msg => msg.text)
      .filter(text => text && text.trim() !== '---' && text.trim() !== '')
      .join('\n\n');

    if (!combinedText) return;

    let parsedHtml = "";
    try {
      parsedHtml = marked.parse(combinedText.trim());
    } catch (markdownError) {
      console.error(`Error parsing Markdown for Option ${option.number}:`, markdownError, combinedText);
      parsedHtml = `<p>Error displaying content.</p>`;
    }

    let formattedText = parsedHtml;
    try {
      formattedText = parsedHtml.replace(
        /<a href='([^']+)'[^>]*>([^<]+)<\/a>/g,
        (match, url, linkText) =>
          `<a href='${url}' target='_blank'>Visit Resource <img src='link-icon.png' class='link-icon' alt='Link'/></a>`
      );
    } catch (regexError) {
      console.error(`Error applying link regex for Option ${option.number}:`, regexError);
      formattedText = parsedHtml;
    }

    // Create elements for the card
    const header = document.createElement("h3");
    header.textContent = `Option ${option.number}`;

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("option-content-preview");
    contentDiv.innerHTML = formattedText;

    const controlsDiv = document.createElement("div");
    controlsDiv.classList.add("option-controls");

    const showMoreBtn = document.createElement("button");
    showMoreBtn.classList.add("show-more-btn");
    showMoreBtn.textContent = "Show more";
    showMoreBtn.onclick = () => {
      card.classList.toggle("expanded");
      showMoreBtn.textContent = card.classList.contains("expanded") ? "Show less" : "Show more";

      // --- FIX: Only scroll if it's the last message container ---
      const wrapper = card.closest('.message-container');
      if (chatLog && wrapper === chatLog.lastElementChild) {
        // Use a small timeout to allow the browser to render
        setTimeout(scrollChatToBottom, 100);
      }
    };

    const selectBtn = document.createElement("button");
    selectBtn.classList.add("select-option-btn");
    selectBtn.textContent = `Select Option ${option.number}`;
    selectBtn.onclick = () => {
      const wrapper = optionsContainer.closest('.message-container');
      if (wrapper) {
        wrapper.querySelectorAll('.select-option-btn, .none-btn-alt').forEach(btn => btn.disabled = true);
      } else {
        optionsContainer.querySelectorAll('.select-option-btn').forEach(btn => btn.disabled = true);
        const noneBtn = chatLog.querySelector('.none-btn-alt:not(:disabled)');
        if (noneBtn) noneBtn.disabled = true;
      }

      card.classList.add('selected-option');
      sendMessageToRasa(String(option.number));
      console.log(option.number);
    };

    controlsDiv.appendChild(showMoreBtn);
    controlsDiv.appendChild(selectBtn);

    card.appendChild(header);
    card.appendChild(contentDiv);
    card.appendChild(controlsDiv);

    optionsContainer.appendChild(card);
    scrollChatToBottom()

    // slight delay for the browser to render and calculate height
    setTimeout(() => {
      if (contentDiv.scrollHeight <= contentDiv.clientHeight) {
        showMoreBtn.style.display = 'none';
      }
    }, 0);

  });

  const noneButton = document.createElement("button");
  noneButton.classList.add("none-btn-alt");
  noneButton.textContent = "None of these were helpful 👎";
  noneButton.onclick = () => {
    const wrapper = noneButton.closest('.message-container');
    if (wrapper) {
      wrapper.querySelectorAll('.select-option-btn, .none-btn-alt').forEach(btn => btn.disabled = true);
    } else {
      optionsContainer.querySelectorAll('.select-option-btn').forEach(btn => btn.disabled = true);
      noneButton.disabled = true;
    }

    sendMessageToRasa("0");
    console.log("0");
  };

  const wrapper = document.createElement("div");
  wrapper.classList.add("message-container");
  wrapper.appendChild(optionsContainer);
  wrapper.appendChild(noneButton);

  chatLog.appendChild(wrapper);
  scrollChatToBottom()
}

function sendMessageToRasa(message) {
  const isIntent = message.startsWith("/");
  const isFeedbackNumber = /^[0-3]$/.test(message);

  const payload = {
    sender: senderID,
    message: message,
  };

  if (!isIntent && !isFeedbackNumber) {
    lastUserQuestion = message;
    addMessageToChat(message, "userMsg");
  } else if (isFeedbackNumber) {
    addMessageToChat("Thank you for your feedback! Can I help you with anything else?", "botMsg");
  }

  if (!isIntent && !isFeedbackNumber && userInput) {
    userInput.value = "";
  }

  // fetch(LOCAL_LINK, {
  fetch(PROD_LINK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((response) => response.json())
    .then((data) => {
      const isAlternative =
        Array.isArray(data) &&
        data.length > 1 &&
        data[0]?.text?.startsWith("Sorry,");

      if (isAlternative) {
        console.log("Alternative Response detected, displaying interactive options.");
        displayAlternativeButtons(data);
      } else {
        const combinedText = data
          .filter((msgObj) => msgObj && msgObj.text)
          .map((msgObj) => msgObj.text)
          .join("\n\n");

        if (combinedText) {
          addMessageToChat(combinedText, "botMsg");
        } else if (!isFeedbackNumber) {
          console.log("Received data but combinedText is empty or invalid.");
          addMessageToChat("Received an empty response from the bot.", "botMsg", "errorMsg");
        }
      }
    })
    .catch((err) => {
      console.error("Error during fetch or JSON parsing:", err);
      addMessageToChat("Sorry, I couldn't reach the server or process its response. Please try again later.", "botMsg", "errorMsg");
    });
}

// brooooooooooooo css is booty
function showSurvey() {
  survey.style.display = "flex";
}

// Event Listeners
sendBtn.addEventListener("click", () => {
  const message = userInput.value.trim();
  if (message) {
    sendMessageToRasa(message);
    setTimeout(scrollChatToBottom(), 50);
  }
});

userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    const message = userInput.value.trim();
    if (message) {
      sendMessageToRasa(message);
      setTimeout(scrollChatToBottom(), 50);

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

