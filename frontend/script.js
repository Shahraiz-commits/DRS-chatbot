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

// Modal elements
const policyDialog = document.getElementById("policyDialog");
const viewPolicyBtn = document.getElementById("viewPolicyBtn");
const closeSurveyBtn = document.getElementById("closeSurveyBtn");
const closePolicyBtn = document.getElementById("closePolicyBtn");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");

const LOCAL_LINK = "http://localhost:5005/webhooks/rest/webhook";
const PROD_LINK =
  "https://rasa-chatbot-42751455718.us-east1.run.app/webhooks/rest/webhook";

function scrollChatToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

// --- Modal Control Functions ---
function openModal(modal) {
  if (modal) {
    modal.style.display = "flex";
  }
}

function closeModal(modal) {
  if (modal) {
    modal.style.display = "none";
  }
}

// --- Helper to extract text content from HTML ---
function getTextContentFromHtml(htmlString) {
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = htmlString;
  return tempDiv.textContent || tempDiv.innerText || "";
}

// --- Typing Effect Function (Modified) ---
function typeWriterEffect(element, textToType, finalHtml, speed = 0.01) {
  let i = 0;
  element.innerHTML = ""; // Clear existing content
  element.classList.add("typing"); // Add typing class for cursor

  function type() {
    if (i < textToType.length) {
      const char = textToType.charAt(i);
      // Append character (use textContent to avoid potential HTML injection)
      element.textContent += char;
      i++;
      // Scroll to bottom during typing
      if (element.closest('.message-container') === chatLog.lastElementChild || element.closest('.option-card')) {
        scrollChatToBottom();
      }
      setTimeout(type, speed);
    } else {
      element.classList.remove("typing"); // Remove typing class when done
      // Replace typed text with the final formatted HTML
      element.innerHTML = finalHtml;
      scrollChatToBottom(); // Ensure scrolled to bottom after typing

      // Check for 'Show more' button visibility AFTER final HTML is set
      const messageDiv = element.closest('.message');
      const controlsDiv = messageDiv?.querySelector('.message-controls');
      if (messageDiv && controlsDiv && element.scrollHeight > element.clientHeight + 5) {
        controlsDiv.style.display = 'block';
      }
      // Check for option card show more
      const optionCard = element.closest('.option-card');
      const optionControls = optionCard?.querySelector('.option-controls .show-more-btn');
      if (optionCard && optionControls && element.scrollHeight > element.clientHeight + 5) {
        optionControls.style.display = 'inline-block'; // or 'block'
      } else if (optionControls) {
        optionControls.style.display = 'none';
      }
    }
  }
  type();
}

function addMessageToChat(text, ...classNames) {
  const isBotMsg = classNames.includes("botMsg");
  const isErrorMsg = classNames.includes("errorMsg");
  const isUserMsg = classNames.includes("userMsg");

  const container = document.createElement("div");
  container.classList.add("message-container");

  if (isBotMsg) {
    container.setAttribute("data-user-question", lastUserQuestion);
  }

  text = text.replace(/\n{3,}/g, "\n\n").trim();

  // --- PARSE MARKDOWN EARLY --- 
  let parsedHtml = '';
  let textContent = text; // Default to original text for non-markdown cases
  let formattedText = text; // Default

  if (isBotMsg || !isUserMsg) { // Parse for bot messages or system messages (like errors)
    try {
      parsedHtml = marked.parse(text);
      // Enhance links to open in new tab
      formattedText = parsedHtml.replace(
        /<a href='([^']+)'>([^<]+)<\/a>/g, // Simpler regex, assumes no extra attributes in markdown links
        (match, url, linkText) =>
          `<a href='${url}' target='_blank' rel='noopener noreferrer'>${linkText} <img src='link-icon.png' class='link-icon' alt='Link'/></a>`
      );
      // Get text content for typewriter
      textContent = getTextContentFromHtml(parsedHtml); // Use the non-link-enhanced version for typing
    } catch (e) {
      console.error("Markdown parsing error:", e);
      formattedText = text; // Fallback to original text on error
      textContent = text;
    }
  }
  // --- END PARSE --- 

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", ...classNames);

  // Add icon for bot messages
  if (isBotMsg && !isErrorMsg) {
    const iconContainer = document.createElement("div");
    iconContainer.classList.add("bot-icon-container");

    let iconText = "DRS";
    let iconClass = "drs-icon";
    const iconDiv = document.createElement("div");
    iconDiv.classList.add("response-icon", iconClass);
    iconDiv.textContent = iconText;
    iconContainer.appendChild(iconDiv);
    container.appendChild(iconContainer);
  }

  const shouldApplyTypewriter = isBotMsg &&
    !text.startsWith("Sorry, I am a bit unsure") &&
    !text.startsWith("Thank you for your feedback!") &&
    !isErrorMsg;

  if (shouldApplyTypewriter) {
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content-preview');
    messageDiv.appendChild(contentDiv);

    const controlsDiv = document.createElement('div');
    controlsDiv.classList.add('message-controls');
    controlsDiv.style.display = 'none'; // Hide initially

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

    chatLog.appendChild(container);
    scrollChatToBottom();

    // Start typing effect with textContent and final formatted HTML
    typeWriterEffect(contentDiv, textContent, formattedText);

  } else if (isUserMsg) {
    messageDiv.textContent = text; // User messages are plain text
    container.appendChild(messageDiv);
    chatLog.appendChild(container);
    scrollChatToBottom();
  } else {
    // For simple bot messages (feedback, errors) or non-markdown messages
    // Set the final formatted HTML directly without typing
    messageDiv.innerHTML = formattedText;
    container.appendChild(messageDiv);
    chatLog.appendChild(container);
    scrollChatToBottom();
  }
}

// --- Event Listeners for Modals ---
viewPolicyBtn.addEventListener('click', () => openModal(policyDialog));
closeSurveyBtn.addEventListener('click', () => closeModal(survey));
closePolicyBtn.addEventListener('click', () => closeModal(policyDialog));

// Close modal if clicking outside the content
window.addEventListener('click', (event) => {
  if (event.target.classList.contains('modal')) {
    closeModal(event.target);
  }
});

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
  if (comments === "") {
    alert("Please enter some comments to provide feedback.")
    return;
  }
  if (!rating || rating < 1 || rating > 5) {
    alert("Please provide a valid rating between 1 and 5.");
    return;
  }

  const feedbackData = {
    rating: rating,
    feedback: comments,
    sender: senderID,
  };

  saveSurveyFeedback(feedbackData)
    .then(() => {
      console.log("Survey feedback submitted to Firebase");
      closeModal(survey);
      ratingInput.value = "";
      commentsInput.value = "";
      addMessageToChat("Thank you for your feedback!", "botMsg");
    })
    .catch((error) => {
      console.error("Error saving survey feedback:", error);
    });
}

// --- Initial Setup --- 
document.addEventListener("DOMContentLoaded", () => {
  // Remove preload class after initial setup to enable transitions
  document.body.classList.remove('preload');

  sendMessageToRasa("/greet");

  // --- Theme Setup --- 
  const currentTheme = localStorage.getItem('theme') || 'light-mode'; // Default to light
  document.body.classList.add(currentTheme);
  themeToggleBtn.textContent = currentTheme === 'dark-mode' ? '🌙' : '☀️';

  // Add event listener for theme toggle button
  themeToggleBtn.addEventListener('click', toggleTheme);

  // --- Sidebar Toggle Setup --- 
  const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (sidebarCollapsed) {
    document.body.classList.add('sidebar-collapsed');
  }

  sidebarToggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('sidebarCollapsed', document.body.classList.contains('sidebar-collapsed'));
  });

  // Ensure all links in the chat open in new tabs
  chatLog.addEventListener('click', (event) => {
    const link = event.target.closest('a');
    if (link && !link.hasAttribute('target')) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });
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
  addMessageToChat("Sorry, I am a bit unsure. Please <strong>select</strong> one of the options below:", "botMsg");

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

    // --- Parse and Format Option Content --- 
    let parsedHtml = '';
    let textContent = combinedText;
    let formattedText = combinedText;
    try {
      parsedHtml = marked.parse(combinedText.trim());
      formattedText = parsedHtml.replace(
        /<a href='([^']+)'>([^<]+)<\/a>/g, // Simpler regex
        (match, url, linkText) =>
          `<a href='${url}' target='_blank' rel='noopener noreferrer'>${linkText} <img src='link-icon.png' class='link-icon' alt='Link'/></a>`
      );
      textContent = getTextContentFromHtml(parsedHtml);
    } catch (markdownError) {
      console.error(`Error parsing Markdown for Option ${option.number}:`, markdownError, combinedText);
      formattedText = `<p>Error displaying content.</p>`;
      textContent = "Error displaying content.";
    }
    // --- End Parse --- 

    const header = document.createElement("h3");
    header.textContent = `Option ${option.number}`;

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("option-content-preview");
    // Content div will be populated by typeWriterEffect

    const controlsDiv = document.createElement("div");
    controlsDiv.classList.add("option-controls");

    const showMoreBtn = document.createElement("button");
    showMoreBtn.classList.add("show-more-btn");
    showMoreBtn.textContent = "Show more";
    showMoreBtn.style.display = 'none'; // Hide initially, typing effect will show if needed
    showMoreBtn.onclick = () => {
      card.classList.toggle("expanded");
      showMoreBtn.textContent = card.classList.contains("expanded") ? "Show less" : "Show more";
      setTimeout(scrollChatToBottom, 100);
    };

    const selectBtn = document.createElement("button");
    selectBtn.classList.add("select-option-btn");
    selectBtn.textContent = `Select Option ${option.number}`;
    selectBtn.onclick = () => {
      // Disable buttons logic
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
    card.appendChild(contentDiv); // Add empty content div
    card.appendChild(controlsDiv);

    optionsContainer.appendChild(card);

    // Start typing effect for the option content
    typeWriterEffect(contentDiv, textContent, formattedText);

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

  // Append the container and button in a new message container
  const wrapper = document.createElement("div");
  wrapper.classList.add("message-container"); // Don't add botMsg here, it's just a container
  wrapper.appendChild(optionsContainer);
  wrapper.appendChild(noneButton);

  chatLog.appendChild(wrapper);
  scrollChatToBottom();
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
  } else if (isFeedbackNumber && message !== "0") { // Only add thanks if not "None of these"
    addMessageToChat("Thank you for your feedback! Can I help you with anything else?", "botMsg");
  } else if (isFeedbackNumber && message === "0") {
    addMessageToChat("Okay, I understand. How else can I assist you?", "botMsg");
  }

  if (!isIntent && !isFeedbackNumber && userInput) {
    userInput.value = "";
  }

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
          console.log("text after: " + combinedText);
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
  openModal(survey);
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


// Update theme toggle functionality
function toggleTheme() {
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const body = document.body;

  // Toggle dark mode class
  body.classList.toggle('dark-mode');

  // Update theme toggle button content based on current state
  const isDarkMode = body.classList.contains('dark-mode');
  themeToggleBtn.textContent = isDarkMode ? '🌙' : '☀️';

  // Save theme preference
  localStorage.setItem('theme', isDarkMode ? 'dark-mode' : 'light-mode');
}