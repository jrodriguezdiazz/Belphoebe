class ChatBox {
  constructor() {
    this.args = {
      openButton: document.querySelector('.chatbox__button'),
      chatBox: document.querySelector('.chatbox__support'),
      sendButton: document.querySelector('.send__button'),
    };
    this.state = false;
    this.messages = [];
  }
  
  toggleState(chatBox) {
    this.state = !this.state;
    this.state
      ? chatBox.classList.add('chatbox--active')
      : chatBox.classList.remove('chatbox--active');
  }
  
  onSendButton(chatBox) {
    let textField = chatBox.querySelector('input');
    let text1 = textField.value;
    if (text1 === '') {
      return;
    }
    this.messages.push({
      name: "User",
      message: text1
    });
    
    fetch(`${$SCRIPT_ROOT}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      mode: 'cors',
      body: JSON.stringify({
        message: text1
      })
    })
      .then(res => res.json())
      .then(data => {
        console.log(data);
        this.messages.push({
          name: "Belpoebe",
          message: data.response
        });
        this.updateChatText(chatBox);
        textField.value = '';
      })
      .catch(err => {
        console.log(err);
        this.updateChatText(chatBox);
        textField.value = '';
      });
  }
  
  updateChatText(chatbox) {
    let html = '';
    this.messages.slice().reverse().forEach(item => {
      console.log(item);
      if (item.name === "Belpoebe") {
        html += `<div class="messages__item messages__item--visitor">${item.message}</div>`;
      } else {
        html += `<div class="messages__item messages__item--operator">${item.message}</div>`;
      }
      const chatText = chatbox.querySelector('.chatbox__messages');
      chatText.innerHTML = html;
    });
  }
  
  display() {
    const {openButton, chatBox, sendButton} = this.args;
    
    openButton.addEventListener('click', () => {
      this.toggleState(chatBox);
    });
    
    sendButton.addEventListener('click', () => {
      this.onSendButton(chatBox);
    });
    
    const mode = chatBox.querySelector('input');
    mode.addEventListener("keyup", ({key}) => {
      if (key === "Enter") {
        this.onSendButton(chatBox);
      }
    });
  }
}


const chatbox = new ChatBox();
chatbox.display();