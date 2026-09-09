import { useState, useEffect } from 'react'
// import { Chatbot } from 'supersimpledev'
import { ChatInput} from './components/ChatInput'
import ChatMessages from './components/ChatMessages'; //Default export, just one
//export from a file, either one of these work but the first way seems better
import './App.css'


function App() { //Components inside components, split website into pieces
  //Use a State
  const [chatMessages, setChatMessages] = useState([]);
  
  // const [chatMessages, setChatMessages] = array;
  // const chatMessages = array[0]; //current data
  // const setChatMessage = array[1]; //Updater Function: replaces array w/ new

  useEffect(() => {
    Chatbot.addResponses({
      'goodbye' : 'Goodbye! Have a great day!',
      'Give me a unique ID' : function() {
        return 'Sure! Your unique ID is' + crypto.randomUUID();
      }
    })
  }, []); //[] == Do the useEffect ONCE

  return (
    <div className='app-container'>
      <ChatMessages 
        chatMessages={chatMessages}
      />
      <ChatInput 
        chatMessages={chatMessages}
        setChatMessages={setChatMessages}  
      />
    </div>
  );
} //React == Create your own HTML elements, so can we use CSS??

export default App
