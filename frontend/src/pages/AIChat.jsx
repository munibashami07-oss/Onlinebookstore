import React, { useEffect, useState, useRef, useContext, useCallback } from 'react';
import chatbotService from '../api/chatbotService';
import { AuthContext } from '../context/AuthContext';
import { extractErrorMessage } from '../utils/errorUtils';

// Browser vendor prefix handling for the Web Speech API.
const SpeechRecognitionAPI =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;
const SPEECH_RECOGNITION_SUPPORTED = !!SpeechRecognitionAPI;
const SPEECH_SYNTHESIS_SUPPORTED =
  typeof window !== 'undefined' && 'speechSynthesis' in window;

const AIChat = () => {
  const { isAuthenticated } = useContext(AuthContext);
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello! I am your BookHaven AI Reading Companion. Ask me anything about book recommendations, plot synopses, store shipping rules, or return policies!',
    },
  ]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
  // Guards against speaking a message twice (e.g. re-renders) and lets us
  // know which message index triggered the current send, so we only
  // auto-speak the answer that was just generated, not old history.
  const lastSpokenIndexRef = useRef(-1);
  // Speech-to-text turn-taking state:
  // - micOnRef: true only while the USER wants the mic on (persists across turns)
  // - canProcessRef: true only while it's the user's "turn" to speak. While
  //   false (AI is generating/speaking its answer) the recognizer keeps
  //   running — the mic stays connected/open — but any transcribed speech
  //   is ignored, so we don't pick up the AI's own voice or interrupt mid-answer.
  // - committedTranscriptRef: finalized speech chunks not yet sent.
  const micOnRef = useRef(false);
  const canProcessRef = useRef(true);
  const committedTranscriptRef = useRef('');

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load chat history if authenticated
  const fetchHistory = useCallback(async () => {
    if (!isAuthenticated) return;
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
      // Non-fatal if history fails
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // ── Text-to-Speech ────────────────────────────────────────────────────────
  const speakText = useCallback(
    (text, onDone) => {
      if (!SPEECH_SYNTHESIS_SUPPORTED || !autoSpeak || !text) {
        onDone?.();
        return;
      }
      window.speechSynthesis.cancel(); // stop anything currently playing
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        onDone?.();
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        onDone?.();
      };
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

  // Speak the newest AI message whenever it's appended.
  useEffect(() => {
    if (messages.length === 0) return;
    const lastIdx = messages.length - 1;
    const lastMsg = messages[lastIdx];
    if (
      lastMsg.sender === 'ai' &&
      lastIdx > lastSpokenIndexRef.current &&
      !loading
    ) {
      lastSpokenIndexRef.current = lastIdx;
      speakText(lastMsg.text, () => {
        // The AI has finished talking — hand the turn back to the user.
        // The recognizer never stopped, so this just resumes processing.
        if (micOnRef.current) canProcessRef.current = true;
      });
    }
  }, [messages, loading, speakText]);

  // Stop any speech on unmount
  useEffect(() => {
    return () => {
      if (SPEECH_SYNTHESIS_SUPPORTED) window.speechSynthesis.cancel();
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

  // ── Speech-to-Text ────────────────────────────────────────────────────────
  const submitQuestion = useCallback(
    async (userText) => {
      if (!userText.trim() || loading) return;
      setQuestion('');
      setError('');
      stopSpeaking();

      setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
      setLoading(true);

      try {
        const res = await chatbotService.askChatbot(userText);
        setMessages((prev) => [...prev, { sender: 'ai', text: res.answer }]);
      } catch (err) {
        setError(extractErrorMessage(err, 'AI Assistant service is currently unreachable.'));
        // No AI message will be appended, so the "speak finished" callback
        // that normally reopens the mic will never fire — reopen it here.
        if (micOnRef.current) canProcessRef.current = true;
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  const initRecognition = useCallback(() => {
    if (!SPEECH_RECOGNITION_SUPPORTED) return null;
    const recognition = new SpeechRecognitionAPI();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    // Continuous: the mic stream stays open across the whole conversation
    // instead of closing after each utterance. We control turn-taking
    // ourselves via canProcessRef rather than by stopping/restarting the
    // underlying recognition session.
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      // It's the AI's turn (thinking or speaking) — ignore anything the
      // mic picks up right now (this also prevents the AI's own TTS audio
      // from being transcribed back in as if the user said it).
      if (!canProcessRef.current) return;

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
      setQuestion(`${committedTranscriptRef.current} ${interim}`.trim());

      // The browser's own speech engine detected a pause (that's what
      // `isFinal` means) — send right away instead of waiting for a click.
      if (finalChunk && committedTranscriptRef.current) {
        const toSend = committedTranscriptRef.current;
        committedTranscriptRef.current = '';
        canProcessRef.current = false; // hold the mic's attention until the AI responds
        submitQuestion(toSend);
      }
    };

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        micOnRef.current = false;
        setIsListening(false);
        setError('Microphone access was denied. Please allow microphone permissions to use voice input.');
      } else if (event.error !== 'no-speech' && event.error !== 'aborted') {
        setError('Voice input error. Please try again or type your question.');
      }
      // 'no-speech'/'aborted' are transient — onend decides whether to restart.
    };

    recognition.onend = () => {
      // Some browsers end the recognition session on their own after a
      // stretch of silence, even with continuous=true. If the user hasn't
      // explicitly turned the mic off, restart it immediately so, from
      // their perspective, the mic never disconnects.
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
  }, [submitQuestion]);

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
    canProcessRef.current = true;
    const recognition = initRecognition();
    recognitionRef.current = recognition;
    if (recognition) {
      recognition.start();
      setIsListening(true);
    }
  };

  // Stop recognition on unmount
  useEffect(() => {
    return () => {
      micOnRef.current = false;
      recognitionRef.current?.stop();
    };
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    await submitQuestion(question.trim());
  };

  const handleClearHistory = async () => {
    stopSpeaking();
    if (!isAuthenticated) {
      setMessages([
        {
          sender: 'ai',
          text: 'Hello! I am your BookHaven AI Reading Companion. Ask me anything about book recommendations!',
        },
      ]);
      lastSpokenIndexRef.current = 0;
      return;
    }
    try {
      await chatbotService.clearChatHistory();
      setMessages([
        {
          sender: 'ai',
          text: 'Chat history cleared. How can I help you today?',
        },
      ]);
      lastSpokenIndexRef.current = 0;
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to clear chat history.'));
    }
  };

  return (
    <div className="container py-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
          <div>
            <h1 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
              <i className="bi bi-robot text-primary me-2"></i> AI Book Companion
            </h1>
            <p className="text-muted mb-0">Powered by RAG architecture & vector similarity search</p>
          </div>
          <div className="d-flex align-items-center gap-2">
            {SPEECH_SYNTHESIS_SUPPORTED && (
              <button
                type="button"
                className={`btn btn-sm rounded-pill ${autoSpeak ? 'btn-accent' : 'btn-outline-secondary'}`}
                style={autoSpeak ? { backgroundColor: 'var(--color-accent)', color: '#fff', border: 'none' } : {}}
                onClick={toggleAutoSpeak}
                title={autoSpeak ? 'Voice replies on — click to mute' : 'Voice replies off — click to unmute'}
              >
                <i className={`bi ${autoSpeak ? 'bi-volume-up-fill' : 'bi-volume-mute-fill'} me-1`}></i>
                {autoSpeak ? 'Voice On' : 'Voice Off'}
              </button>
            )}
            <button
              className="btn btn-outline-secondary btn-sm rounded-pill"
              onClick={handleClearHistory}
              title="Clear Chat History"
            >
              <i className="bi bi-trash me-1"></i> Clear Chat
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="alert alert-danger d-flex align-items-center mb-4" role="alert">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            <div>{error}</div>
          </div>
        )}

        {/* Chat Box Card */}
        <div className="card border-0 shadow-lg rounded-4 overflow-hidden bg-white">
          {/* Messages List Container */}
          <div
            className="card-body p-4 overflow-auto"
            style={{ height: '480px', backgroundColor: '#f8fafc' }}
          >
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`d-flex mb-3 ${msg.sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
              >
                <div className="d-flex gap-2 max-w-lg">
                  {msg.sender === 'ai' && (
                    <div
                      className="rounded-circle bg-indigo text-white d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{ width: '36px', height: '36px', backgroundColor: '#4f46e5' }}
                    >
                      <i className="bi bi-robot"></i>
                    </div>
                  )}

                  <div
                    className={`p-3 rounded-4 shadow-sm ${
                      msg.sender === 'user'
                        ? 'bg-accent text-white rounded-bottom-end-0'
                        : 'bg-white text-dark border rounded-bottom-start-0'
                    }`}
                    style={msg.sender === 'user' ? { backgroundColor: 'var(--color-accent)' } : {}}
                  >
                    <p className="mb-0 leading-relaxed" style={{ whiteSpace: 'pre-wrap' }}>
                      {msg.text}
                    </p>
                    {msg.sender === 'ai' &&
                      idx === messages.length - 1 &&
                      isSpeaking && (
                        <small className="text-muted d-flex align-items-center gap-1 mt-2">
                          <i className="bi bi-soundwave"></i> Speaking…
                        </small>
                      )}
                  </div>

                  {msg.sender === 'user' && (
                    <div
                      className="rounded-circle bg-dark text-white d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{ width: '36px', height: '36px' }}
                    >
                      <i className="bi bi-person-fill"></i>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* AI Generation Loading Indicator */}
            {loading && (
              <div className="d-flex justify-content-start mb-3">
                <div className="d-flex align-items-center gap-2 bg-white p-3 rounded-4 border shadow-sm text-muted">
                  <div className="spinner-grow spinner-grow-sm text-primary" role="status"></div>
                  <small className="fw-semibold">AI is analyzing catalog & generating response…</small>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Question Input Footer */}
          <div className="card-footer bg-white p-3 border-top">
            <form onSubmit={handleSendMessage} className="d-flex gap-2">
              {SPEECH_RECOGNITION_SUPPORTED && (
                <button
                  type="button"
                  className={`btn rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center ${
                    isListening ? 'btn-danger' : 'btn-outline-primary'
                  }`}
                  style={{ width: '44px', height: '44px' }}
                  onClick={handleMicClick}
                  disabled={loading}
                  title={isListening ? 'Stop listening' : 'Ask by voice'}
                >
                  <i className={`bi ${isListening ? 'bi-mic-fill' : 'bi-mic'}`}></i>
                </button>
              )}
              <input
                type="text"
                className="form-control rounded-pill px-4"
                placeholder={
                  isListening
                    ? loading || isSpeaking
                      ? "AI is responding…"
                      : 'Listening…'
                    : 'Ask about books, authors, genres, or store policies...'
                }
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="btn btn-accent rounded-pill px-4 shadow-sm flex-shrink-0"
                disabled={loading || !question.trim()}
              >
                {loading ? (
                  <span className="spinner-border spinner-border-sm" role="status"></span>
                ) : (
                  <>Send <i className="bi bi-send-fill ms-1"></i></>
                )}
              </button>
            </form>
            {isListening && (
              <small className="text-danger d-flex align-items-center gap-1 mt-2">
                <i className="bi bi-record-circle"></i>
                {loading || isSpeaking
                  ? ' Mic is on, waiting for the AI to finish responding…'
                  : ' Listening — speak your question, it sends automatically when you pause'}
              </small>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChat;