import RobotProfileImage from '../assets/robot.png';
import UserProfileImage from '../assets/user.png';

import './ChatMessage.css'
//Double dots => bo back two folders

export function ChatMessage({message, sender}) {
    //const {message, sender} = props ^
    
    //const message = props.message ^^
    //const sender = props.sender
  
    return (
      <div 
        className={sender === 'user' 
        ? 'chat-message-user' 
        : 'chat-message-robot'
      }>
        {(sender === 'robot') && (
          <img src={RobotProfileImage} 
            width="50" 
            className='chat-message-profile'
          />
        )}
        <div 
          className='chat-message-text'>
          {message}
        </div>
        {(sender === 'user') && (
          <img src={UserProfileImage} 
            width="50"
            className='chat-message-profile'
          />
        )}
      </div>
    ); 
    // if (sender === 'robot'), then <img src="robot.png" width="50"/>
  }