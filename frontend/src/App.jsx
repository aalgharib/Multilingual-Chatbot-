import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE_URL, getChatHistory, postChatMessage, resetChatHistory } from './api.js';

const LANGUAGE_OPTIONS = [
  { code: 'auto', label: 'Auto-detect' },
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'hi', label: 'Hindi' },
  { code: 'zh', label: 'Chinese (Simplified)' }
];

const TARGET_LANGUAGE_OPTIONS = LANGUAGE_OPTIONS.filter(option => option.code !== 'auto');

const LANGUAGE_TO_LOCALE = {
  en: 'en-US',
  es: 'es-ES',
  fr: 'fr-FR',
  de: 'de-DE',
  hi: 'hi-IN',
  zh: 'zh-CN'
};

function usePersistentSessionId(key) {
  const [sessionId, setSessionId] = useState(() => {
    try {
      if (typeof window === 'undefined' || !window.localStorage) {
        throw new Error('localStorage is not available in this environment.');
      }
      return window.localStorage.getItem(key) || '';
    } catch (error) {
      console.warn('localStorage is not available; falling back to in-memory sessions.', error);
      return '';
    }
  });

  useEffect(() => {
    try {
      if (typeof window === 'undefined' || !window.localStorage) {
        return;
      }

      if (sessionId) {
        window.localStorage.setItem(key, sessionId);
      } else {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.warn('Unable to persist the session id to localStorage.', error);
    }
  }, [key, sessionId]);

  return [sessionId, setSessionId];
}

function Message({ role, text }) {
  return (
    <div className={`message message--${role}`}>
      <div className="message__role">{role === 'user' ? 'You' : 'Assistant'}</div>
      <div className="message__text">{text}</div>
    </div>
  );
}

function App() {
  const [sessionId, setSessionId] = usePersistentSessionId('multilingual-chatbot-session');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recognitionSupported, setRecognitionSupported] = useState(false);
  const [recognitionError, setRecognitionError] = useState('');
  const recognitionRef = useRef(null);

  const sessionSummary = useMemo(() => {
    if (!sessionId) {
      return 'Not connected yet';
    }
    return `Session ${sessionId.slice(0, 8)}…`;
  }, [sessionId]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setRecognitionSupported(false);
      return;
    }

    setRecognitionSupported(true);

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setRecognitionError('');
      setIsRecording(true);
    };

    recognition.onresult = event => {
      const transcript = Array.from(event.results)
        .map(result => result[0]?.transcript ?? '')
        .join(' ')
        .trim();

      if (transcript) {
        setInput(prevInput => {
          if (!prevInput.trim()) {
            return transcript;
          }
          const needsSpace = /\s$/.test(prevInput) ? '' : ' ';
          return `${prevInput}${needsSpace}${transcript}`;
        });
      }
    };

    recognition.onerror = event => {
      let friendlyMessage = 'Voice capture error occurred. Please try again.';
      if (event.error === 'not-allowed') {
        friendlyMessage = 'Microphone access was denied. Allow access in your browser settings and try again.';
      } else if (event.error === 'no-speech') {
        friendlyMessage = 'No speech was detected. Please speak clearly and try again.';
      } else if (event.error === 'audio-capture') {
        friendlyMessage = 'No microphone was found. Connect a microphone and try again.';
      }
      setRecognitionError(friendlyMessage);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.onstart = null;
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      try {
        recognition.stop();
      } catch (stopError) {
        console.warn('Unable to stop speech recognition cleanly.', stopError);
      }
      recognitionRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = LANGUAGE_TO_LOCALE[sourceLanguage] || 'en-US';
    }
  }, [sourceLanguage]);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    let isSubscribed = true;
    getChatHistory(sessionId)
      .then(history => {
        if (isSubscribed) {
          const nextMessages = history.map(item => [
            { role: 'user', text: item.user_input },
            { role: 'assistant', text: item.bot_response }
          ]).flat();
          setMessages(nextMessages);
        }
      })
      .catch(fetchError => {
        console.error(fetchError);
        if (isSubscribed) {
          setError(fetchError.message);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [sessionId]);

  const submitMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }

    const optimisticMessages = [
      ...messages,
      { role: 'user', text: trimmed }
    ];
    setMessages(optimisticMessages);
    setInput('');
    setIsLoading(true);
    setError('');

    try {
      const response = await postChatMessage({
        sessionId,
        message: trimmed,
        sourceLanguage,
        targetLanguage
      });

      if (!sessionId && response.session_id) {
        setSessionId(response.session_id);
      }

      setMessages(prevMessages => [
        ...prevMessages,
        { role: 'assistant', text: response.response }
      ]);
    } catch (requestError) {
      console.error(requestError);
      setError(requestError.message);
      setMessages(prevMessages => prevMessages.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  }, [input, messages, sessionId, setSessionId, sourceLanguage, targetLanguage]);

  const handleSubmit = useCallback(
    event => {
      event.preventDefault();
      submitMessage();
    },
    [submitMessage]
  );

  const handleReset = useCallback(async () => {
    if (!sessionId) {
      setMessages([]);
      setInput('');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      await resetChatHistory(sessionId);
      setMessages([]);
      setSessionId('');
      setInput('');
    } catch (resetError) {
      console.error(resetError);
      setError(resetError.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, setSessionId]);

  const toggleRecording = useCallback(() => {
    if (!recognitionSupported || !recognitionRef.current) {
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    setRecognitionError('');
    try {
      recognitionRef.current.start();
      setIsRecording(true);
    } catch (startError) {
      console.error(startError);
      setRecognitionError('Unable to start voice capture. Please ensure your microphone is available and try again.');
      setIsRecording(false);
    }
  }, [isRecording, recognitionSupported]);

  const voiceStatus = useMemo(() => {
    if (recognitionError) {
      return recognitionError;
    }

    if (!recognitionSupported) {
      return 'Voice capture is not supported in this browser.';
    }

    if (isRecording) {
      return 'Listening… speak now and click again to stop.';
    }

    return 'Use your microphone to dictate a message.';
  }, [isRecording, recognitionError, recognitionSupported]);

  return (
    <div className="app">
      <header className="app__header">
        <h1>Multilingual Chatbot Prototype</h1>
        <p className="app__subtitle">
          Connects to the Flask API at <code>{API_BASE_URL}</code>
        </p>
      </header>

      <section className="app__panel">
        <div className="app__panel-header">
          <h2>Conversation</h2>
          <div className="session-indicator" title={sessionId || 'Session not yet established'}>
            {sessionSummary}
          </div>
        </div>

        <div className="message-list">
          {messages.length === 0 ? (
            <div className="message-list__empty">
              Start the conversation by sending a message below.
            </div>
          ) : (
            messages.map((message, index) => (
              <Message key={`${message.role}-${index}`} role={message.role} text={message.text} />
            ))
          )}
        </div>
      </section>

      <section className="app__panel">
        <div className="app__panel-header">
          <h2>Compose a Message</h2>
        </div>
        <form className="composer" onSubmit={handleSubmit}>
          <label className="composer__label">
            Source language
            <select
              value={sourceLanguage}
              onChange={event => setSourceLanguage(event.target.value)}
              className="composer__select"
              disabled={isLoading}
            >
              {LANGUAGE_OPTIONS.map(option => (
                <option key={option.code} value={option.code}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="composer__label">
            Target language
            <select
              value={targetLanguage}
              onChange={event => setTargetLanguage(event.target.value)}
              className="composer__select"
              disabled={isLoading}
            >
              {TARGET_LANGUAGE_OPTIONS.map(option => (
                <option key={option.code} value={option.code}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="composer__label composer__label--full">
            Message
            <textarea
              className="composer__textarea"
              value={input}
              onChange={event => setInput(event.target.value)}
              placeholder="Ask something in any language…"
              rows={4}
              disabled={isLoading}
            />
          </label>

          <div className="voice-input" role="group" aria-label="Voice message controls">
            <button
              type="button"
              className={`voice-input__button${isRecording ? ' voice-input__button--recording' : ''}`}
              onClick={toggleRecording}
              disabled={!recognitionSupported || isLoading}
              aria-pressed={isRecording}
            >
              <span className="voice-input__indicator" aria-hidden="true" />
              {isRecording ? 'Stop recording' : 'Record voice input'}
            </button>
            <span
              className={`voice-input__status${recognitionError ? ' voice-input__status--error' : ''}`}
              aria-live="polite"
            >
              {voiceStatus}
            </span>
          </div>

          {error && <div className="composer__error">{error}</div>}

          <div className="composer__actions">
            <button type="submit" className="composer__button" disabled={isLoading || !input.trim()}>
              {isLoading ? 'Sending…' : 'Send message'}
            </button>
            <button type="button" className="composer__button composer__button--secondary" onClick={handleReset} disabled={isLoading}>
              Start new session
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default App;
