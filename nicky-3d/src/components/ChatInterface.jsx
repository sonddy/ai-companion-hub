import { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

const CHAT_ENDPOINT = 'http://127.0.0.1:8005/chat';

export function ChatInterface({ onTalkingChange }) {
  const [messages, setMessages] = useState([
    { sender: 'nicky', text: "Hey there, sweetheart... I'm Nicky. Ask me anything you want. 😏" }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('Ready to chat!');
  const audioRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const playAudio = (audioUrl) => {
    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(err => {
        console.error('Audio play error:', err);
        setStatus('Could not play audio');
      });
    }
  };

  const handleAudioPlay = () => {
    onTalkingChange(true);
    setStatus('Nicky is speaking...');
  };

  const handleAudioEnd = () => {
    onTalkingChange(false);
    setStatus('Ready to chat!');
  };

  const sendMessage = async () => {
    const text = inputValue.trim();
    if (!text || isLoading) return;

    // Add user message
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setInputValue('');
    setIsLoading(true);
    setStatus('Nicky is thinking...');

    try {
      const res = await fetch(CHAT_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      // Get response text from header
      const rawResponse = res.headers.get('X-Sicky-Response') || '...';
      const responseText = decodeURIComponent(rawResponse);

      // Add Nicky's message
      setMessages(prev => [...prev, { sender: 'nicky', text: responseText }]);

      // Play audio
      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      playAudio(audioUrl);

    } catch (err) {
      console.error('Chat error:', err);
      setStatus('Error: ' + err.message);
      setMessages(prev => [...prev, { 
        sender: 'nicky', 
        text: "Sorry sweetheart, I'm having trouble connecting. Make sure the server is running!" 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      { sender: 'nicky', text: "Hey there, sweetheart... I'm Nicky. Ask me anything you want. 😏" }
    ]);
    setStatus('Chat cleared!');
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Chat with Nicky</h2>
        <span className="status">{status}</span>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <div className="message-label">{msg.sender === 'user' ? 'You' : 'Nicky'}</div>
            <div className="message-text">{msg.text}</div>
          </div>
        ))}
        {isLoading && (
          <div className="message nicky loading">
            <div className="message-label">Nicky</div>
            <div className="message-text">
              <span className="typing-indicator">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask Nicky anything..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading || !inputValue.trim()}>
          {isLoading ? '...' : 'Send'}
        </button>
      </div>

      <div className="chat-controls">
        <button className="secondary" onClick={clearChat}>Clear Chat</button>
      </div>

      <audio 
        ref={audioRef} 
        onPlay={handleAudioPlay}
        onEnded={handleAudioEnd}
        onPause={handleAudioEnd}
      />
    </div>
  );
}

export default ChatInterface;


