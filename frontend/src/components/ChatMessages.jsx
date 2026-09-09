import { useRef, useEffect } from 'react'
import { ChatMessage } from './ChatMessage';

import './ChatMessages.css'
function useAutoScroll(dependencies) {
    const chatMessagesRef = useRef(null);
  
    useEffect(() => {
      const containerElem = chatMessagesRef.current;
      if (containerElem) {
        containerElem.scrollTop = containerElem.scrollHeight;
        //How Far from top^ = Scroll for height of element , Basically scroll to bottom
      }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, dependencies); //Every time chatMessages changes, it will update
    //    ^ Dependency Array
  
    return chatMessagesRef;
}
  
function ChatMessages({chatMessages}) {
    const chatMessagesRef = useAutoScroll(chatMessages);
    
    return ( 
      <div
      className='chat-messages-container'
      ref={chatMessagesRef}
      >{chatMessages.length === 0 && (
          <div
            className='empty-message'
          > Welcome to the chatbot! Send a message below. </div>
        )}
        <div>
          {chatMessages.map((chatMessage) => {
            return (
                <ChatMessage 
                  message={chatMessage.message} 
                  sender={chatMessage.sender}
                  key={chatMessage.id}
                />
              );
          })}
        </div>
      </div>
    );  
}

export default ChatMessages;
