import { useState } from 'react'
// Change to work with Gemini API v
// import { Chatbot } from 'supersimpledev'
// Change to work with Gemini API ^
import './ChatInput.css'

export function ChatInput({ chatMessages, setChatMessages }) { //Must start with capital letter
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  function SaveInputText(event) {
    setInputText(event.target.value);  //event.target gets input, so we do input.value
  }

  async function sendMessage() {
    if (!inputText.trim()) return;

    const currentInput = inputText;
    const robotMessageId = crypto.randomUUID();

    const newChatMessages = [
      ...chatMessages, //spread operator, copies vals into new array
      {
        message: currentInput,
        sender: 'user',
        id: crypto.randomUUID()
      }
    ];

    // Immediately trigger loading state and show typing bubble
    setIsLoading(true);
    setInputText('');
    setChatMessages([
      ...newChatMessages,
      {
        message: '',
        sender: 'robot',
        isLoading: true,
        id: robotMessageId
      }
    ]);

    try {
      const res = await fetch(
        `http://localhost:8000/respond_to_prompt?prompt=${encodeURIComponent(currentInput)}`
      );
      const data = await res.json();

      setChatMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === robotMessageId
            ? {
              ...msg,
              message: data.response || data.data || "Sorry, I couldn't process your request.",
              isLoading: false
            }
            : msg
        )
      );
    } catch (error) {
      setChatMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === robotMessageId
            ? {
              ...msg,
              message: "Unable to connect to the server. Please check your connection and try again.",
              isLoading: false
            }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }

  function checkClear() {
    if (event.key === 'Enter' && !isLoading) {
      sendMessage();
    } else if (event.key === 'Escape') {
      setInputText('');
    }
  }

  function clearChatMessages() {
    setChatMessages([]);
    setIsLoading(false);
  }

  return (
    <div className='chat-input-container'>
      <input
        placeholder="Send a message to ChatBot"
        size="30"
        onChange={SaveInputText}
        value={inputText /*Controlled Input*/}
        onKeyDown={checkClear}
        className="input-text"
      />
      <button
        onClick={(!isLoading) && sendMessage}
        className="send-button"
      >Send</button>
      <button
        onClick={clearChatMessages}
        className="clear-button"
      >Clear</button>
    </div>
  );
}