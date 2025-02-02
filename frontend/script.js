const chatLog = document.getElementById('chatLog');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const senderID = 'user_' + Math.floor(Math.random() * 100000);

function scrollChatToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

function addMessageToChat(text, className) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', className);

  // this is so janky remove this later lol. we shouldnt be using regex for this
  messageDiv.innerHTML = makeLink(text);
  // messageDiv.innerText = text;

  chatLog.appendChild(messageDiv);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function sendMessageToRasa(message) {
  userInput.value = '';
  addMessageToChat(message, 'userMsg');

  const payload = {
    sender: senderID,
    message: message
  };

  fetch('http://localhost:5005/webhooks/rest/webhook', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(response => response.json())
    .then(data => {
      data.forEach(msgObj => {
        if (msgObj.text) {
          addMessageToChat(msgObj.text, 'botMsg');
        }
      });
    })
    .catch(err => console.error('Error:', err));
}

function makeLink(text) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, url => {
    return `<a href="${url}" target="_blank">${url}</a>`; 
  });
}


sendBtn.addEventListener('click', () => {
  const message = userInput.value.trim();
  if (message) {
    sendMessageToRasa(message);
  }
});

userInput.addEventListener('keypress', e => {
  if (e.key === 'Enter') {
    const message = userInput.value.trim();
    if (message) {
      sendMessageToRasa(message);
    }
  }
});
