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
let typingInProgress = false;

const policyDialog = document.getElementById("policyDialog");
const viewPolicyBtn = document.getElementById("viewPolicyBtn");
const closeSurveyBtn = document.getElementById("closeSurveyBtn");
const closePolicyBtn = document.getElementById("closePolicyBtn");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");

const LOCAL_LINK = "http://localhost:5005/webhooks/rest/webhook";
const PROD_LINK =
  "https://rasa-chatbot-42751455718.us-east1.run.app/webhooks/rest/webhook";
const KEYWORD_LINK = "https://api-sue4xaradq-ue.a.run.app/extract_keyword" // TODO: CHANGE ROUTE
const CENSOR_LINK = "https://api-sue4xaradq-ue.a.run.app/censor_text"

let userScrolling = false;
let scrollTimeout = null;

function scrollChatToBottom() {
  if (userScrolling) {
    return;
  }
  if (chatLog && typeof chatLog.scrollHeight !== 'undefined') {
    chatLog.scrollTo({
      top: chatLog.scrollHeight,
      behavior: 'smooth'
    });
  } else {
    console.warn("Chatlog not available or ready for scrolling.");
  }
}

function handleScroll() {
  userScrolling = true;
  if (scrollTimeout) {
    clearTimeout(scrollTimeout);
  }
  scrollTimeout = setTimeout(() => {
    userScrolling = false;
  }, 250);
}

function openModal(modal) {
  if (modal) {
    modal.style.display = "flex";
    const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable) {
      focusable.focus();
    }
  }
}

function closeModal(modal) {
  if (modal) {
    modal.style.display = "none";
  }
}

function wrapTextNodes(node, charSpans) {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = node.nodeValue;
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < text.length; i++) {
      const span = document.createElement('span');
      span.className = 'typewriter-char';
      span.textContent = text[i];

      if (text[i] === ' ' && (i > 0 && text[i - 1] === ' ' || i < text.length - 1 && text[i + 1] === ' ')) {
        span.innerHTML = ' ';
      } else if (text[i] === '\n') {
        span.textContent = '\n';
      }
      fragment.appendChild(span);
      charSpans.push(span);
    }
    try {
      if (node.parentNode) {
        node.parentNode.replaceChild(fragment, node);
      }
    } catch (e) {
      console.error("Error replacing text node:", e, node);
    }
  } else if (node.nodeType === Node.ELEMENT_NODE && node.childNodes.length > 0) {
    const children = Array.from(node.childNodes);
    children.forEach(child => wrapTextNodes(child, charSpans));
  }
}


function typeWriterEffect(element, finalHtml, speed = 10) {
  if (!element) {
    console.error("Typewriter effect called on a null or undefined element.");
    return;
  }
  if (typingInProgress) {
    console.warn("Typing effect already running. Overlapping effects might occur.");
  }
  typingInProgress = true;
  element.innerHTML = finalHtml;
  element.classList.add("typing");

  const charSpans = [];
  wrapTextNodes(element, charSpans);

  let i = 0;
  let initialScrollHeight = 0;
  try {
    initialScrollHeight = element.scrollHeight;
  } catch (e) {
    console.warn("Could not read scrollHeight during typewriter init", e);
  }


  function type() {
    if (i < charSpans.length) {
      const span = charSpans[i];
      if (span) {
        span.style.opacity = '1';
      } else {
        console.warn("Missing span at index", i, "during typing.");
      }
      i++;

      if (element.closest) {
        const isLastMessageContainer = element.closest('.message-container') === chatLog?.lastElementChild;
        const isNearBottom = chatLog && (chatLog.scrollHeight - chatLog.scrollTop <= chatLog.clientHeight + 100); // Threshold

        if (isLastMessageContainer || isNearBottom) {
          try {
            scrollChatToBottom();
          } catch (e) { }
        }
      }

      setTimeout(type, speed);
    } else {
      if (element) {
        element.classList.remove("typing");
      }
      typingInProgress = false;
      setTimeout(scrollChatToBottom, 50);

      const msgContainer = element.closest(".message-container");
      const controlsDivMsg = msgContainer?.querySelector('.message-controls');
      const feedbackDiv = msgContainer?.querySelector(".feedback-buttons");


      if (feedbackDiv) feedbackDiv.style.display = "block";


      if (element?.closest) {
        const messageDiv = element.closest('.message');
        const showMoreBtnMsg = controlsDivMsg?.querySelector('.show-more-btn');

        if (messageDiv && controlsDivMsg && showMoreBtnMsg && element.classList.contains('message-content-preview')) {
          try {
            if (element.scrollHeight > element.clientHeight + 10) {
              showMoreBtnMsg.style.display = 'inline-block';
              controlsDivMsg.style.display = 'block';
            } else {
              showMoreBtnMsg.style.display = 'none';
              controlsDivMsg.style.display = 'none';
            }
          } catch (e) { }
        }

        const optionCard = element.closest('.option-card');
        const optionControls = optionCard?.querySelector('.option-controls');
        const showMoreBtnOption = optionControls?.querySelector('.show-more-btn');

        if (optionCard && optionControls && showMoreBtnOption && element.classList.contains('option-content-preview')) {
          try {
            if (element.scrollHeight > element.clientHeight + 10) {
              showMoreBtnOption.style.display = 'inline-block';
              optionControls.style.display = 'flex';
            } else {
              showMoreBtnOption.style.display = 'none';
            }
          } catch (e) { }
        }
      }

      setTimeout(scrollChatToBottom, 50);
    }
  }
  type();
}

function getTextContentFromHtml(htmlString) {
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = htmlString;
  return tempDiv.textContent || tempDiv.innerText || "";
}


function addMessageToChat(text, ...classNames) {
  const isBotMsg = classNames.includes("botMsg");
  const isErrorMsg = classNames.includes("errorMsg");
  const isUserMsg = classNames.includes("userMsg");
  const isGreeting = text.startsWith("Hi! How can I help you?");
  const isAlternativeIntro = text.includes("Sorry, I am a bit unsure");
  const isOutOfScopeIntro = text.includes("not handled by Digital Research Services")
  const isFollowUp = (text.includes("Okay, I understand. How") || text.includes("Thank you for your feedback!"));
  // console.log(isFollowUp);
  const container = document.createElement("div");
  container.classList.add("message-container");

  if(isBotMsg && isOutOfScopeIntro) {
    text = text.replace(/^.*?\n\n/, '') // Remove the initial text when out of scope
  }

  if (isBotMsg && !isAlternativeIntro && lastUserQuestion) {
    container.setAttribute("data-user-question", lastUserQuestion);
  }


  text = text.replace(/\n{3,}/g, "\n\n").trim();

  let formattedText = text;
  if ((isBotMsg || isErrorMsg) && !isUserMsg && !isAlternativeIntro) {
    try {
      // let parsedHtml = marked.parse(text, { breaks: true });
      // formattedText = parsedHtml.replace(
      //   /<a href="([^"]+)"/g,
      //   (match, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer"`
      // );
      let parsedHtml = marked.parse(text, { breaks: true });
      parsedHtml = parsedHtml
        .replace(/<ul>/g, '<ul style="list-style:none; margin-left:1.5em;">')
        .replace(/<li>/g, '<li>• ');
      formattedText = parsedHtml.replace(
        /<a href="([^"]+)"/g,
        (match, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer"`
      );
    } catch (e) {
      console.error("Markdown parsing error:", e);
      formattedText = `<p>${text.replace(/\n/g, '<br>')}</p>`;
    }
  }

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", ...classNames);

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

    const shouldApplyTypewriter = true;
    if (shouldApplyTypewriter) {
      const contentDiv = document.createElement('div');
      contentDiv.classList.add('message-content-preview');
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
        contentDiv.style.maxHeight = messageDiv.classList.contains('expanded') ? contentDiv.scrollHeight + 'px' : '';
        setTimeout(scrollChatToBottom, 50);
      };
      controlsDiv.appendChild(showMoreBtn);

      const messageId = `msg_${messageCounter++}`;
      messageDiv.setAttribute("data-message-id", messageId);

      container.appendChild(messageDiv);
      container.appendChild(controlsDiv);

    if (!isGreeting && !isAlternativeIntro && !isFollowUp) {
      const feedbackDiv = document.createElement("div");
      feedbackDiv.classList.add("feedback-buttons");
      feedbackDiv.style.display = "none";
      feedbackDiv.innerHTML = `
          <div class="feedback-buttons-wrapper">
            <button class="feedback-btn thumbs-up" title="Good response" aria-label="Good response" onclick="handleFeedbackClick('${messageId}', 'positive')">👍</button>
            <button class="feedback-btn thumbs-down" title="Bad response" aria-label="Bad response" onclick="handleFeedbackClick('${messageId}', 'negative')">👎</button>
          </div>
          <div class="feedback-input-wrapper">
            <input type="text" class="feedback-text-input" placeholder="">
            <button class="submit-feedback-btn">Submit</button>
          </div>
          <div class="feedback-thank-you" style="display: none;">Thank you for your feedback!</div>
        `;
      container.appendChild(feedbackDiv);
    }

      chatLog.appendChild(container);
      setTimeout(scrollChatToBottom, 0);

      typeWriterEffect(contentDiv, formattedText);

    } else {
      messageDiv.innerHTML = formattedText;
      container.appendChild(messageDiv);
      chatLog.appendChild(container);
      setTimeout(scrollChatToBottom, 0);
    }


  } else if (isUserMsg) {
    messageDiv.textContent = text;
    container.appendChild(messageDiv);
    chatLog.appendChild(container);
    setTimeout(scrollChatToBottom, 0);
  } else {
    if (!isAlternativeIntro) {
      messageDiv.innerHTML = formattedText;
      container.appendChild(messageDiv);
      chatLog.appendChild(container);
      setTimeout(scrollChatToBottom, 0);
    } else {
      // console.log("Detected raw alternative block, will be processed by displayAlternativeButtons.");
    }
  }
}

viewPolicyBtn.addEventListener('click', () => openModal(policyDialog));
closeSurveyBtn.addEventListener('click', () => closeModal(survey));
closePolicyBtn.addEventListener('click', () => closeModal(policyDialog));

window.addEventListener('click', (event) => {
  if (event.target.classList.contains('modal')) {
    closeModal(event.target);
  }
});

window.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    const openModalElement = document.querySelector('.modal[style*="display: flex"]');
    if (openModalElement) {
      closeModal(openModalElement);
    }
  }
});

function handleFeedbackClick(messageId, feedbackType) {
  const messageContainer = document.querySelector(`[data-message-id="${messageId}"]`)?.closest('.message-container');
  if (!messageContainer) return;

  const feedbackWrapper = messageContainer.querySelector(".feedback-input-wrapper");
  const textInput = messageContainer.querySelector(".feedback-text-input");
  const targetBtn = messageContainer.querySelector(feedbackType === "positive" ? ".thumbs-up" : ".thumbs-down");
  const thankYouMsg = messageContainer.querySelector(".feedback-thank-you");
  const submitBtn = messageContainer.querySelector(".submit-feedback-btn");

  if (!feedbackWrapper || !textInput || !targetBtn || !thankYouMsg || !submitBtn) {
    console.error("Feedback elements not found for message:", messageId);
    return;
  }


  thankYouMsg.style.display = 'none';

  if (targetBtn.classList.contains("selected")) {
    targetBtn.classList.remove("selected");
    feedbackWrapper.style.opacity = "0";
    feedbackWrapper.style.height = "0";
    feedbackWrapper.style.overflow = "hidden";
    submitBtn.onclick = null;
    return;
  }

  const buttons = messageContainer.querySelectorAll(".feedback-btn");
  buttons.forEach((btn) => btn.classList.remove("selected"));
  targetBtn.classList.add("selected");

  feedbackWrapper.style.opacity = "1";
  feedbackWrapper.style.height = "auto";
  feedbackWrapper.style.overflow = "visible";
  textInput.value = '';

  textInput.className = 'feedback-text-input'; // Reset classes
  textInput.classList.add(feedbackType === "positive" ? "positive" : "negative");
  textInput.placeholder = feedbackType === "positive" ? "What did you like? (Optional)" : "What went wrong? (Optional)";

  textInput.focus();
  setTimeout(scrollChatToBottom, 50);

  submitBtn.onclick = () => submitMessageFeedback(messageId, feedbackType, textInput.value);
}


function submitMessageFeedback(messageId, feedback, feedbackText) {
  if (!feedback) return;

  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  if (!messageElement) {
    console.error("Could not find message element for feedback:", messageId);
    return;
  }
  const messageContentElement = messageElement.querySelector('.message-content-preview');
  const messageHtml = messageContentElement ? messageContentElement.innerHTML : messageElement.innerHTML;
  const messageText = getTextContentFromHtml(messageHtml);

  const messageContainer = messageElement.closest('.message-container');
  const userQuestion = messageContainer ? messageContainer.getAttribute("data-user-question") || "" : "";

  const feedbackData = {
    feedback: feedback,
    feedbackText: feedbackText.trim() || "",
    question: userQuestion,
    response: messageText.trim(),
    timestamp: new Date().toISOString(),
    sender: senderID
  };

  saveMessageFeedback(feedbackData)
    .then(() => {
      const container = messageElement.closest('.message-container');
      if (container) {
        const feedbackWrapper = container.querySelector(".feedback-input-wrapper");
        const thankYouMsg = container.querySelector(".feedback-thank-you");
        const buttonsWrapper = container.querySelector(".feedback-buttons-wrapper");

        if (feedbackWrapper) {
          feedbackWrapper.style.opacity = "0";
          feedbackWrapper.style.height = "0";
          feedbackWrapper.style.overflow = "hidden";
        }
        if (thankYouMsg) {
          thankYouMsg.style.display = 'block';
          thankYouMsg.textContent = "Thank you for your feedback!";
          thankYouMsg.style.color = "#28a745";
        }
        buttonsWrapper?.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('selected'));

        setTimeout(() => {
          if (thankYouMsg) thankYouMsg.style.display = 'none';
        }, 4000);
      }
    })
    .catch((error) => {
      console.error("Error saving message feedback:", error);
      const container = messageElement.closest('.message-container');
      if (container) {
        const thankYouMsg = container.querySelector(".feedback-thank-you");
        if (thankYouMsg) {
          thankYouMsg.textContent = "Error saving feedback.";
          thankYouMsg.style.color = "red";
          thankYouMsg.style.display = 'block';
          setTimeout(() => {
            if (thankYouMsg) {
              thankYouMsg.style.display = 'none';
              thankYouMsg.textContent = "Thank you for your feedback!";
              thankYouMsg.style.color = "#28a745";
            }
          }, 4000);
        }
      }
    });
}


function submitFeedback() {
  const rating = ratingInput.value;
  const comments = commentsInput.value.trim();

  if (!ratingInput.reportValidity()) {
    return;
  }

  const feedbackData = {
    rating: parseInt(rating, 10),
    feedback: comments,
    sender: senderID,
    timestamp: new Date().toISOString()
  };

  // console.log("Submitting survey feedback:", feedbackData);

  submitFeedbackBtn.disabled = true;
  submitFeedbackBtn.textContent = 'Submitting...';

  saveSurveyFeedback(feedbackData)
    .then(() => {
      // console.log("Survey feedback submitted to Firebase");
      closeModal(survey);
      ratingInput.value = "";
      commentsInput.value = "";
      addMessageToChat("Thank you for your feedback! Your input helps improve this service.", "botMsg");
    })
    .catch((error) => {
      console.error("Error saving survey feedback:", error);
      alert("Sorry, there was an error submitting your feedback. Please try again later.");
    })
    .finally(() => {
      submitFeedbackBtn.disabled = false;
      submitFeedbackBtn.textContent = 'Submit';
    });
}

function toggleSidebar() {
  const body = document.body;
  if (!body || !sidebarToggleBtn) return;

  body.classList.toggle('sidebar-collapsed');
  const isCollapsed = body.classList.contains('sidebar-collapsed');
  localStorage.setItem('sidebarCollapsed', isCollapsed);

  if (window.innerWidth > 768) {
    sidebarToggleBtn.textContent = isCollapsed ? '>' : '<';
    sidebarToggleBtn.setAttribute('aria-label', isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar');
  } else {
    sidebarToggleBtn.textContent = '';
    sidebarToggleBtn.setAttribute('aria-label', isCollapsed ? 'Show Info' : 'Hide Info');
  }
  sidebarToggleBtn.setAttribute('aria-expanded', !isCollapsed);

}


document.addEventListener("DOMContentLoaded", () => {
  if (!document.body || !localStorage || !themeToggleBtn || !sidebarToggleBtn || !chatLog || !userInput || !sendBtn || !policyDialog || !viewPolicyBtn || !survey) {
    console.error("Initialization failed: One or more critical DOM elements are missing.");
    return;
  }

  document.body.classList.remove('preload');

  sendMessageToRasa("/greet");

  const currentTheme = localStorage.getItem('theme') || 'light-mode'; // Default to light
  // document.body.classList.add(currentTheme);
  themeToggleBtn.textContent = currentTheme === 'dark-mode' ? '🌙' : '☀️';

  // Add event listener for theme toggle button
  // themeToggleBtn.addEventListener('click', toggleTheme);


  const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  // if (window.innerWidth <= 768) {
  //   if (sidebarCollapsed !== false) {
  //     document.body.classList.add('sidebar-collapsed');
  //   }
  // } else {
  //   if (sidebarCollapsed) {
  //     document.body.classList.add('sidebar-collapsed');
  //   }
  // }


  sidebarToggleBtn.addEventListener('click', toggleSidebar);

  chatLog.addEventListener('click', (event) => {
    const link = event.target.closest('a');
    if (link && link.href) {
      if (link.hostname !== window.location.hostname || link.pathname !== window.location.pathname || !link.target) {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
      }
    }
  });

  chatLog.addEventListener('scroll', handleScroll);


  window.addEventListener('resize', () => {
    // Only update button appearance on resize, not layout
    const isCollapsed = document.body.classList.contains('sidebar-collapsed');
    if (window.innerWidth <= 768) {
      sidebarToggleBtn.textContent = '';
      sidebarToggleBtn.setAttribute('aria-label', isCollapsed ? 'Show Info' : 'Hide Info');
    } else {
      sidebarToggleBtn.textContent = isCollapsed ? '>' : '<';
      sidebarToggleBtn.setAttribute('aria-label', isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar');
    }
    // DO NOT call updateChatContainerMargin - CSS handles resize adjustments
    // updateChatContainerMargin(); // REMOVED
  });
});

// Quick action buttons
document.querySelectorAll(".actionBtn").forEach((button) => {
  button.addEventListener("click", () => {
    const query = button.dataset.query;
    if (userInput) { // Check if userInput exists
      userInput.value = query;
      sendMessageToRasa(query);
      userInput.value = ''; // Clear after sending
    }
  });
});

function displayAlternativeButtons(data) {
  addMessageToChat("Sorry, I am a bit unsure with my response. Is this what you were looking for?", "botMsg");

  const optionsContainer = document.createElement("div");
  optionsContainer.classList.add("alternative-options-container");

  const findMarkerIndex = (marker) => data.findIndex(msg => msg.text?.includes(marker));

  const startIndex1 = findMarkerIndex("[1]");
  const startIndex2 = findMarkerIndex("[2]");
  const startIndex3 = findMarkerIndex("[3]");

  const endMarkerText = "Did any of these";
  const endIndex = data.findIndex(msg => msg.text?.startsWith(endMarkerText));
  const effectiveEndIndex = endIndex === -1 ? data.length : endIndex;

  const optionsData = [];
  let optionCount = 1;

  if (startIndex1 !== -1) {
    const endSlice1 = startIndex2 !== -1 ? startIndex2 : (startIndex3 !== -1 ? startIndex3 : effectiveEndIndex);
    optionsData.push({ number: 1, title: `Option ${optionCount++}`, messages: data.slice(startIndex1 + 1, endSlice1) });
  } else {
    optionCount++;
  }

  if (startIndex2 !== -1) {
    const endSlice2 = startIndex3 !== -1 ? startIndex3 : effectiveEndIndex;
    optionsData.push({ number: 2, title: `Option ${optionCount++}`, messages: data.slice(startIndex2 + 1, endSlice2) });
  } else {
    optionCount++;
  }

  if (startIndex3 !== -1) {
    optionsData.push({ number: 3, title: `Option ${optionCount++}`, messages: data.slice(startIndex3 + 1, effectiveEndIndex) });
  }

  // console.log('Parsed alternative options data:', optionsData);

  if (optionsData.length === 0) {
    console.warn("No valid options parsed from the alternative response data. Displaying raw data as fallback.");
    let combinedRawText = data
      .map(msg => msg.text)
      .filter(text => text && text.trim() !== '' && !text.includes("Did any of these") && !text.includes("[1]") && !text.includes("[2]") && !text.includes("[3]"))
      .join('\n\n');
    if (combinedRawText) {
      addMessageToChat(combinedRawText, "botMsg");
    }
    return;
  }

  // --- Create and Append Cards ---
  optionsData.forEach(option => {
    const card = document.createElement("div");
    card.classList.add("option-card");
    card.setAttribute('role', 'article');
    card.setAttribute('aria-labelledby', `option-title-${option.number}`);

    const combinedBodyText = option.messages
      .map(msg => msg.text)
      .filter(text => text && text.trim() !== '---' && text.trim() !== '')
      .join('\n\n')
      .trim();

    let formattedBodyText = '';
    try {
      if (combinedBodyText) {
        let parsedHtml = marked.parse(combinedBodyText, { breaks: true });
        formattedBodyText = parsedHtml.replace(
          /<a href="([^"]+)"/g,
          (match, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer"`
        );
      } else {
        formattedBodyText = "<p><i>No further details provided.</i></p>";
      }
    } catch (markdownError) {
      console.error(`Error parsing Markdown for Option ${option.number} body:`, markdownError, combinedBodyText);
      formattedBodyText = `<p>Error displaying content.</p>`;
    }

    const header = document.createElement("h3");
    header.id = `option-title-${option.number}`;
    // Use innerHTML to allow potential formatting in title if needed
    header.innerHTML = `<strong>${option.title || `Option ${option.number}`}</strong>`;

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("option-content-preview");

    const controlsDiv = document.createElement("div");
    controlsDiv.classList.add("option-controls");

    const showMoreBtn = document.createElement("button");
    showMoreBtn.classList.add("show-more-btn");
    showMoreBtn.textContent = "Show more";
    showMoreBtn.style.display = 'none';
    showMoreBtn.onclick = (e) => {
      e.stopPropagation();
      const cardElement = e.target.closest('.option-card');
      if (!cardElement) return;
      cardElement.classList.toggle("expanded");
      showMoreBtn.textContent = cardElement.classList.contains("expanded") ? "Show less" : "Show more";
      const contentPreview = cardElement.querySelector('.option-content-preview');
      if (contentPreview) { // Check if contentPreview exists
        contentPreview.style.maxHeight = cardElement.classList.contains("expanded") ? contentPreview.scrollHeight + 'px' : '';
      }
      setTimeout(scrollChatToBottom, 100);
    };

    const selectBtn = document.createElement("button");
    selectBtn.classList.add("select-option-btn");
    selectBtn.textContent = `Select Option ${option.number}`;
    selectBtn.onclick = (e) => {
      e.stopPropagation();
      // Target the specific wrapper holding this set of options/buttons
      const wrapper = optionsContainer.closest('.alternative-options-wrapper');
      if (wrapper) {
        wrapper.querySelectorAll('.select-option-btn, .none-btn-alt').forEach(btn => btn.disabled = true);
      } else {
        console.warn("Could not find wrapper for alternative options to disable buttons.");
        // Fallback if wrapper isn't found (should not happen ideally)
        optionsContainer.querySelectorAll('.select-option-btn, .none-btn-alt').forEach(btn => btn.disabled = true);
      }
      card.classList.add('selected-option');
      sendMessageToRasa(String(option.number)); // Send selected option number
      // console.log(option.number);
      addMessageToChat("Thank you for your feedback! Can I help you with anything else?", "botMsg");
      // console.log(`Selected Option: ${option.number}`);

    };

    controlsDiv.appendChild(showMoreBtn);
    controlsDiv.appendChild(selectBtn);

    card.appendChild(header);
    card.appendChild(contentDiv);
    card.appendChild(controlsDiv);

    optionsContainer.appendChild(card);

    // Start typing effect ONLY if there is body text
    if (combinedBodyText) {
      typeWriterEffect(contentDiv, formattedBodyText, 30); // Slower speed for options?
    } else {
      showMoreBtn.style.display = 'none'; // Ensure hidden if no content
    }

  });

  // --- "None of these" Button ---
  const noneButton = document.createElement("button");
  noneButton.classList.add("none-btn-alt");
  noneButton.innerHTML = "None of these were helpful 👎";
  noneButton.onclick = (e) => {
    e.stopPropagation();
    const wrapper = noneButton.closest('.alternative-options-wrapper');
    if (wrapper) {
      wrapper.querySelectorAll('.select-option-btn, .none-btn-alt').forEach(btn => btn.disabled = true);
    } else {
      console.warn("Could not find wrapper for none button to disable options.");
      optionsContainer.querySelectorAll('.select-option-btn, .none-btn-alt').forEach(btn => btn.disabled = true); // Fallback
    }
    sendMessageToRasa("0");
    addMessageToChat("Okay, I understand. How else can I assist you?", "botMsg");
    // console.log("Selected: None were helpful");
  };

  const wrapperContainer = document.createElement("div");
  wrapperContainer.classList.add("message-container", "alternative-options-wrapper");

  wrapperContainer.appendChild(optionsContainer);
  wrapperContainer.appendChild(noneButton);

  chatLog.appendChild(wrapperContainer);
  setTimeout(scrollChatToBottom, 0);
}

// --- sendMessageToRasa ---
async function sendMessageToRasa(message) {
  message = message?.trim();
  if (!message) return;
  const isIntent = message.startsWith("/");
  const isFeedbackNumber = /^[0-3]$/.test(message);

  const payload = {
    sender: senderID,
    message: message,
  };

  // Check if the message is inappropriate
  try {
    const response = await fetch(CENSOR_LINK, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ text: message }),
    });

    if (!response.ok) {
      throw new Error(`API network response was not ok: ${response.status} ${response.statusText}`);
    }

    const contentType = response.headers.get('content-type');
    const data = contentType && contentType.includes("application/json") ? await response.json() : null;

    if (data?.contains_profanity) {
      const censored_text = data.censored_text;
      lastUserQuestion = censored_text;
      addMessageToChat(censored_text, "userMsg");
      if (userInput) userInput.value = "";
      scrollChatToBottom();
      addMessageToChat(getBadLanguageResponse(), "botMsg");
      return;
    }

  } catch (error) {
    console.error("Censor fetch failed: ", error);
  }

  if (!isIntent && !isFeedbackNumber) {
    lastUserQuestion = message;
    addMessageToChat(message, "userMsg");
    if (userInput) userInput.value = "";
    scrollChatToBottom();
  } else if (isFeedbackNumber) {
    // console.log(`Feedback number ${message} selected, sending to Rasa.`);
  }

  fetch(PROD_LINK, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
      }
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") !== -1) {
        return response.json();
      } else {
        // console.log("Received non-JSON or empty response from Rasa.");
        return null;
      }
    })
    .then((data) => {

      if (data === null) {
        if (!isFeedbackNumber) {
          addMessageToChat("Received an empty response from the server.", "botMsg", "errorMsg");
        }
        return;
      }

      if (!Array.isArray(data)) {
        console.error("Received non-array response from Rasa:", data);
        addMessageToChat("Sorry, I received an unexpected response from the server.", "botMsg", "errorMsg");
        return;
      }

      const isAlternative = data.some(msg =>
        msg.text?.includes("[1]") || msg.text?.includes("[2]") || msg.text?.includes("[3]")
      );

      if (isAlternative) {
        // // console.log("Alternative Response pattern detected. Processing with displayAlternativeButtons.");
        displayAlternativeButtons(data);
      } else {
        let combinedText = data
          .filter((msgObj) => msgObj && msgObj.text)
          .map((msgObj) => msgObj.text)
          .join("\n\n");

          if (combinedText) {
            // console.log("text after: " + combinedText);
            if (!combinedText.startsWith("Hi!")) {
              combinedText += "\n\n" + getContinuationText();
              fetch(KEYWORD_LINK, {
                method: "POST",
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify({ text: message })
              })
                .then(res => res.json())
                .then(data => {
                  if(data.keyword == null || data.keyword == "help"){
                    data.keyword = "that"
                  }
                  combinedText = getInitiationText() + data.keyword + ".\n\n" + combinedText;
                  //console.log("Initiating with:", combinedText);
                  addMessageToChat(combinedText, "botMsg");
                })
                .catch(error => {
                  console.error("Keyword fetch failed:", error);
                  addMessageToChat(combinedText, "botMsg");
                });
            } else {
              addMessageToChat(combinedText, "botMsg");
            }
          } else if (data.length > 0 && !isFeedbackNumber) {
          // console.log("Received non-empty response from Rasa, but no text content found.");
          if (!message.startsWith('/greet')) {
            addMessageToChat("I received a response, but it was empty. Please try again.", "botMsg", "errorMsg");
          }
        } else if (data.length === 0 && !isFeedbackNumber) {
          // console.log("Received empty array response from Rasa.");
          if (!message.startsWith('/greet')) {
            addMessageToChat("I didn't get a response for that. Could you please try rephrasing?", "botMsg", "errorMsg");
          }
        }
      }
    })
    .catch((err) => {
      console.error("Error during fetch or processing Rasa response:", err);
      addMessageToChat(`Sorry, there was an issue connecting to the chatbot service (${err.message}). Please try again later.`, "botMsg", "errorMsg");
    });
}

// Returns a random string in response to inappropriate language
function getBadLanguageResponse() {
  const texts = {
    0: "Please refrain from using inappropriate language! I'm happy to help with a rephrased question.",
    1: "Please keep things respectful. I’m here to help however I can. Could you rephrase your question so I can better understand how to assist you?",
    2: "Let's keep the conversation professional. I'm happy to help if you could clarify your request.",
    3: "I'm here to provide assistance with your queries. Let’s keep things courteous so we can find the best solution for your situation.",
    4: "Let’s work together respectfully. I’d be glad to assist if you could rephrase or clarify your request.",
    5: "I'm happy to help with your questions. Lets try again with a clear and appropriate message."
  }

  let chosen = Math.floor((Math.random() * 6));
  return texts[chosen]
}

// Returns a random string to initiate the conversation
function getInitiationText() {
  const texts = {
    0: "I can definitely help you with ",
    1: "Sure thing! Here's what you need to know about ",
    2: "Got it! Let’s take a look at ",
    3: "Happy to assist! This is what I found on ",
    4: "Here’s some information on ",
    5: "I’ve got you covered. Here’s some info about ",
    6: "Right away — I can help you out with ",
    7: "I'm happy to help you with "
  }

  let chosen = Math.floor((Math.random() * 8));
  return texts[chosen]
}

// Returns a random string to continue the conversation
function getContinuationText() {
  const texts = {
    0: "What else may I help you with?",
    1: "How else may I assist you?",
    2: "Anything else I can help you with?",
    3: "Is there anything else you need? I'm happy to help!",
    4: "Let me know if you need help with anything else!",
    5: "Would you like to learn about anything else?",
    6: "Can I do something else for you?",
    7: "That was a great question! Need anything else?"
  }

  let chosen = Math.floor((Math.random() * 8)); // Scale to 8 max
  return texts[chosen]
}

function showSurvey() {
  openModal(survey);
}

sendBtn.addEventListener("click", () => {
  sendMessageToRasa(userInput.value);
});

userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { // Send on Enter only
    e.preventDefault(); // Prevent default newline on Enter
    sendMessageToRasa(userInput.value);
  }
});

submitFeedbackBtn.addEventListener("click", submitFeedback);

document.getElementById("endChatBtn").addEventListener("click", showSurvey);

window.handleFeedbackClick = handleFeedbackClick;
window.toggleTheme = toggleTheme;

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