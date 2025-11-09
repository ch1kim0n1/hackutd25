import { useState, useEffect, useCallback, useRef } from 'react';

export const useVoiceRecognition = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState(null);
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef('');
  const holdOnDetectedRef = useRef(false);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser');
      setIsSupported(false);
      return;
    }

    setIsSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      holdOnDetectedRef.current = false;
    };

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        
        if (event.results[i].isFinal) {
          final += transcriptPiece + ' ';
        } else {
          interim += transcriptPiece;
        }
      }

      if (final) {
        finalTranscriptRef.current += final;
        setTranscript(finalTranscriptRef.current);
        
        const lowerFinal = final.toLowerCase();
        if ((lowerFinal.includes('hold on') || lowerFinal.includes('holdon') || lowerFinal.includes('wait')) && !holdOnDetectedRef.current) {
          holdOnDetectedRef.current = true;
          setIsPaused(true);
        }
      }

      setInterimTranscript(interim);
    };

    recognition.onerror = (event) => {
      setError(event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;

    try {
      finalTranscriptRef.current = '';
      holdOnDetectedRef.current = false;
      setTranscript('');
      setInterimTranscript('');
      setIsPaused(false);
      setError(null);
      recognitionRef.current.start();
    } catch (err) {
      if (err.name !== 'InvalidStateError') {
        setError(err.message);
      }
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;

    try {
      recognitionRef.current.stop();
    } catch (err) {
      console.error('Error stopping recognition:', err);
    }
  }, []);

  const clearTranscript = useCallback(() => {
    finalTranscriptRef.current = '';
    setTranscript('');
    setInterimTranscript('');
    setIsPaused(false);
    holdOnDetectedRef.current = false;
  }, []);

  const resumeAfterHoldOn = useCallback(() => {
    setIsPaused(false);
    holdOnDetectedRef.current = false;
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    isPaused,
    error,
    isSupported,
    startListening,
    stopListening,
    clearTranscript,
    resumeAfterHoldOn,
  };
};

export default useVoiceRecognition;
