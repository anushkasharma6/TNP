import React, { useState } from 'react';
import './VoiceInput.css';

const VoiceInput = () => {
  const [text, setText] = useState('');
  const [response, setResponse] = useState('');

  const handleClick = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Browser does not support speech recognition!');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setText(transcript);

      fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: transcript })
      })
      .then(res => res.json())
      .then(data => {
        setResponse(data.response);
      });
    };

    recognition.onerror = (event) => {
      console.error('Error:', event.error);
    };
  };

  return (
    <div className="voice-input-container">
      <button onClick={handleClick}>🎤 Speak</button>
      <p><span>User:</span> {text}</p>
      <p><span>AI:</span> {response}</p>
    </div>
  );
};

export default VoiceInput;
