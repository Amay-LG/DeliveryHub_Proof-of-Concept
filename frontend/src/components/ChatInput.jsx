import { useState } from 'react'
// Change to work with Gemini API v
// import { Chatbot } from 'supersimpledev'
// Change to work with Gemini API ^
import './ChatInput.css'

export function ChatInput({chatMessages, setChatMessages}){ //Must start with capital letter
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    function SaveInputText(event) {
      setInputText(event.target.value);  //event.target gets input, so we do input.value
    }
    
    async function sendMessage() {

      const newChatMessages = [
        ...chatMessages, //spread operator, copies vals into new array
        {
          message: inputText,
          sender: 'user',
          id: crypto.randomUUID()
        }
      ];
  
      setChatMessages(newChatMessages);

      setInputText(''); //Sets inputText to empty, but does NOT update HTML
      const res = await fetch(
        `http://localhost:8000/classify-message?model_name=gemini-3.5-flash-lite&prompt=${encodeURIComponent(inputText)}`
      );
      const data = await res.json();

      setIsLoading(true);
      setChatMessages([ //Added new value to end of array
        ...newChatMessages,
        {
          message: '',
          sender: 'robot',
          id: crypto.randomUUID()
        }
      ]);
  
      setChatMessages([ //Added new value to end of array
        ...newChatMessages,
        {
          // message: "Filler",
          message: "("+data.category+"; "+data.confidence+")\n\n"+data.response,
          sender: 'robot',
          id: crypto.randomUUID()
        }
      ]);
      setIsLoading(false);
  
    }
  
    function checkClear() {
      if (event.key === 'Enter' && !isLoading){
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