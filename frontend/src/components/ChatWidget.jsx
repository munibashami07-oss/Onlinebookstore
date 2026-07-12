import React, { useEffect, useState, useRef, useContext, useCallback } from 'react';
import chatbotService from '../api/chatbotService';
import { AuthContext } from '../context/AuthContext';
import { extractErrorMessage } from '../utils/errorUtils';

const GREETING = {
  sender: 'ai',
  text: 'Hello! I am your BookHaven AI Reading Companion. Ask me anything about book recommendations, plot synopses, store shipping rules, or return policies!',
};

// Browser vendor prefix handling for the Web Speech API.
const SpeechRecognitionAPI =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;
const SPEECH_RECOGNITION_SUPPORTED = !!SpeechRecognitionAPI;
const SPEECH_SYNTHESIS_SUPPORTED =
  typeof window !== 'undefined' && 'speechSynthesis' in window;

/**
 * Site-wide floating AI chat widget.
 * Renders as a small circular avatar pinned to the right edge of the
 * viewport on every page (mounted once in Layout). Clicking it expands
 * a compact chat panel without navigating away from the current page.
 */
const ChatWidget = () => {
  const { isAuthenticated } = useContext(AuthContext);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Voice state
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(() => {
    try {
      return localStorage.getItem('aichat_auto_speak') !== 'false';
    } catch {
      return true;
    }
  });

  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const lastSpokenIndexRef = useRef(0);
  const committedTranscriptRef = useRef(''); // finalized speech not yet sent
  const micOnRef = useRef(false); // true only while the USER wants the mic on

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (open) scrollToBottom();
  }, [messages, loading, open]);

  // Load persisted chat history the first time the widget is opened
  // (only for authenticated users; guests just get the greeting).
  const fetchHistory = useCallback(async () => {
    if (!isAuthenticated || historyLoaded) return;
    try {
      const logs = await chatbotService.getChatHistory(1, 50);
      if (logs && logs.length > 0) {
        const formatted = [];
        logs.reverse().forEach((log) => {
          formatted.push({ sender: 'user', text: log.question });
          formatted.push({ sender: 'ai', text: log.answer });
        });
        setMessages(formatted);
        // Don't speak historical messages on load, only new ones going forward.
        lastSpokenIndexRef.current = formatted.length - 1;
      }
    } catch {
      // Non-fatal if history fails to load
    } finally {
      setHistoryLoaded(true);
    }
  }, [isAuthenticated, historyLoaded]);

  useEffect(() => {
    if (open) fetchHistory();
  }, [open, fetchHistory]);

  // Reset the locally-loaded history flag if the user logs out/in so the
  // widget re-syncs with the correct account next time it's opened.
  useEffect(() => {
    setHistoryLoaded(false);
    setMessages([GREETING]);
    lastSpokenIndexRef.current = 0;
  }, [isAuthenticated]);

  // ── Text-to-Speech ────────────────────────────────────────────────────────
  const speakText = useCallback(
    (text) => {
      if (!SPEECH_SYNTHESIS_SUPPORTED || !autoSpeak || !text) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    },
    [autoSpeak]
  );

  const stopSpeaking = () => {
    if (SPEECH_SYNTHESIS_SUPPORTED) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // Speak the newest AI message whenever it's appended (only while the
  // widget is open, so background tabs don't start talking unexpectedly).
  useEffect(() => {
    if (!open || messages.length === 0) return;
    const lastIdx = messages.length - 1;
    const lastMsg = messages[lastIdx];
    if (lastMsg.sender === 'ai' && lastIdx > lastSpokenIndexRef.current && !loading) {
      lastSpokenIndexRef.current = lastIdx;
      speakText(lastMsg.text);
    }
  }, [messages, loading, open, speakText]);

  // Stop speaking / listening when the panel is closed or unmounted.
  useEffect(() => {
    if (!open) {
      stopSpeaking();
      micOnRef.current = false;
      recognitionRef.current?.stop();
      setIsListening(false);
    }
  }, [open]);

  useEffect(() => {
    return () => {
      if (SPEECH_SYNTHESIS_SUPPORTED) window.speechSynthesis.cancel();
      micOnRef.current = false;
      recognitionRef.current?.stop();
    };
  }, []);

  const toggleAutoSpeak = () => {
    setAutoSpeak((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('aichat_auto_speak', String(next));
      } catch {
        // ignore storage failures (e.g. private browsing)
      }
      if (!next) stopSpeaking();
      return next;
    });
  };

  // ── Sending a question (shared by typed submit and voice) ────────────────
  const submitQuestion = useCallback(
    async (userText) => {
      if (!userText.trim() || loading) return;
      setQuestion('');
      committedTranscriptRef.current = '';
      setError('');
      stopSpeaking();

      setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
      setLoading(true);

      try {
        const res = await chatbotService.askChatbot(userText);
        setMessages((prev) => [...prev, { sender: 'ai', text: res.answer }]);
      } catch (err) {
        setError(extractErrorMessage(err, 'AI Assistant service is currently unreachable.'));
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  const handleSendMessage = async (e) => {
    e.preventDefault();
    await submitQuestion(question.trim());
  };

  const handleClearHistory = async () => {
    stopSpeaking();
    if (!isAuthenticated) {
      setMessages([GREETING]);
      lastSpokenIndexRef.current = 0;
      return;
    }
    try {
      await chatbotService.clearChatHistory();
      setMessages([{ sender: 'ai', text: 'Chat history cleared. How can I help you today?' }]);
      lastSpokenIndexRef.current = 0;
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to clear chat history.'));
    }
  };

  // ── Speech-to-Text ────────────────────────────────────────────────────────
  const initRecognition = useCallback(() => {
    if (!SPEECH_RECOGNITION_SUPPORTED) return null;
    const recognition = new SpeechRecognitionAPI();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    // Continuous so the mic keeps listening across pauses instead of
    // stopping after the first thing the user says.
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let interim = '';
      let finalChunk = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalChunk += transcript;
        } else {
          interim += transcript;
        }
      }
      if (finalChunk) {
        committedTranscriptRef.current = `${committedTranscriptRef.current} ${finalChunk}`.trim();
      }
      // Just populate the input — never auto-send. The user reviews/edits
      // the transcribed text and sends it themselves via the send button.
      setQuestion(`${committedTranscriptRef.current} ${interim}`.trim());
    };

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        micOnRef.current = false;
        setIsListening(false);
        setError('Microphone access was denied. Please allow microphone permissions to use voice input.');
      } else if (event.error !== 'no-speech' && event.error !== 'aborted') {
        setError('Voice input error. Please try again or type your question.');
      }
      // 'no-speech'/'aborted' are transient — onend will decide whether to restart.
    };

    recognition.onend = () => {
      // Some browsers stop recognition on their own after a period of
      // silence even with continuous=true. If the user hasn't manually
      // turned the mic off, restart it so listening effectively continues
      // until they press the mic button again.
      if (micOnRef.current) {
        try {
          recognition.start();
        } catch {
          setIsListening(false);
        }
      } else {
        setIsListening(false);
      }
    };

    return recognition;
  }, []);

  const handleMicClick = () => {
    if (!SPEECH_RECOGNITION_SUPPORTED) {
      setError('Voice input is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    if (isListening) {
      // User is explicitly turning the mic off.
      micOnRef.current = false;
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    stopSpeaking(); // don't listen while the AI is talking
    setError('');
    committedTranscriptRef.current = '';
    micOnRef.current = true;
    const recognition = initRecognition();
    recognitionRef.current = recognition;
    if (recognition) {
      recognition.start();
      setIsListening(true);
    }
  };

  return (
    <>
      {/* Floating avatar toggle button, pinned to the right edge on every page */}
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-label={open ? 'Close AI chat assistant' : 'Open AI chat assistant'}
        className="shadow-lg border-0 d-flex align-items-center justify-content-center"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '58px',
          height: '58px',
          borderRadius: '50%',
          backgroundColor: 'var(--color-accent)',
          color: '#fff',
          zIndex: 1050,
          fontSize: '1.5rem',
          transition: 'transform 0.15s ease',
        }}
        onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.94)')}
        onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
      >
        <i className={`bi ${open ? 'bi-x-lg' : 'bi-robot'}`}></i>
      </button>

      {/* Expandable chat panel */}
      {open && (
        <div
          className="shadow-lg rounded-4 bg-white d-flex flex-column overflow-hidden"
          style={{
            position: 'fixed',
            bottom: '92px',
            right: '24px',
            width: '360px',
            maxWidth: 'calc(100vw - 32px)',
            height: '520px',
            maxHeight: 'calc(100vh - 140px)',
            zIndex: 1049,
            border: '1px solid rgba(0,0,0,0.08)',
          }}
        >
          {/* Header */}
          <div
            className="d-flex justify-content-between align-items-center px-3 py-3 text-white flex-shrink-0"
            style={{ backgroundColor: 'var(--color-accent)' }}
          >
            <div className="d-flex align-items-center gap-2">
              <i className="bi bi-robot fs-5"></i>
              <div>
                <div className="fw-bold" style={{ fontSize: '0.95rem', lineHeight: 1.1 }}>
                  AI Book Companion
                </div>
                <div style={{ fontSize: '0.7rem', opacity: 0.85 }}>Ask about books, orders & policies</div>
              </div>
            </div>
            <div className="d-flex align-items-center gap-1">
              {SPEECH_SYNTHESIS_SUPPORTED && (
                <button
                  type="button"
                  className="btn btn-sm btn-link text-white p-1"
                  onClick={toggleAutoSpeak}
                  title={autoSpeak ? 'Voice replies on — click to mute' : 'Voice replies off — click to unmute'}
                >
                  <i className={`bi ${autoSpeak ? 'bi-volume-up-fill' : 'bi-volume-mute-fill'}`}></i>
                </button>
              )}
              <button
                type="button"
                className="btn btn-sm btn-link text-white p-1"
                onClick={handleClearHistory}
                title="Clear Chat History"
              >
                <i className="bi bi-trash"></i>
              </button>
              <button
                type="button"
                className="btn btn-sm btn-link text-white p-1"
                onClick={() => setOpen(false)}
                title="Close"
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="alert alert-danger m-2 py-2 px-3 mb-0 small" role="alert">
              <i className="bi bi-exclamation-triangle-fill me-1"></i> {error}
            </div>
          )}

          {/* Messages */}
          <div className="flex-grow-1 overflow-auto p-3" style={{ backgroundColor: '#f8fafc' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`d-flex mb-3 ${msg.sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
              >
                <div className="d-flex gap-2" style={{ maxWidth: '85%' }}>
                  {msg.sender === 'ai' && (
                    <div
                      className="rounded-circle text-white d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{ width: '28px', height: '28px', backgroundColor: '#4f46e5', fontSize: '0.8rem' }}
                    >
                      <i className="bi bi-robot"></i>
                    </div>
                  )}

                  <div
                    className={`p-2 px-3 rounded-4 shadow-sm ${
                      msg.sender === 'user' ? 'text-white' : 'bg-white text-dark border'
                    }`}
                    style={msg.sender === 'user' ? { backgroundColor: 'var(--color-accent)' } : {}}
                  >
                    <p className="mb-0 small" style={{ whiteSpace: 'pre-wrap' }}>
                      {msg.text}
                    </p>
                    {msg.sender === 'ai' && idx === messages.length - 1 && isSpeaking && (
                      <small className="text-muted d-flex align-items-center gap-1 mt-1">
                        <i className="bi bi-soundwave"></i> Speaking…
                      </small>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="d-flex justify-content-start mb-3">
                <div className="d-flex align-items-center gap-2 bg-white p-2 px-3 rounded-4 border shadow-sm text-muted">
                  <div className="spinner-grow spinner-grow-sm text-primary" role="status"></div>
                  <small>Thinking…</small>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input Footer */}
          <div className="p-2 border-top bg-white flex-shrink-0">
            {isListening && (
              <small className="text-danger d-flex align-items-center gap-1 mb-1 px-1">
                <i className="bi bi-record-circle"></i> Listening — speak now
              </small>
            )}
            <form onSubmit={handleSendMessage} className="d-flex gap-2">
              {SPEECH_RECOGNITION_SUPPORTED && (
                <button
                  type="button"
                  className={`btn btn-sm rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center ${
                    isListening ? 'btn-danger text-white' : 'btn-outline-secondary'
                  }`}
                  style={{ width: '34px', height: '34px' }}
                  onClick={handleMicClick}
                  disabled={loading}
                  title={isListening ? 'Stop listening' : 'Ask by voice'}
                >
                  <i
                    className={`bi ${isListening ? 'bi-mic-fill' : 'bi-mic'}`}
                    style={{ fontSize: '0.8rem' }}
                  ></i>
                </button>
              )}
              <input
                type="text"
                className="form-control form-control-sm rounded-pill px-3"
                placeholder={isListening ? 'Listening…' : 'Type a message…'}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
                autoFocus
              />
              <button
                type="submit"
                className="btn btn-sm rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center text-white"
                style={{ width: '34px', height: '34px', backgroundColor: 'var(--color-accent)' }}
                disabled={loading || !question.trim()}
              >
                {loading ? (
                  <span className="spinner-border spinner-border-sm" role="status"></span>
                ) : (
                  <i className="bi bi-send-fill" style={{ fontSize: '0.8rem' }}></i>
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;