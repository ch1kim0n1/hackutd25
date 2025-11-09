import { useState, useEffect, useRef } from "react";

interface UseTypingAnimationOptions {
  speed?: number; // milliseconds per character
  onComplete?: () => void;
}

export const useTypingAnimation = (
  text: string,
  options: UseTypingAnimationOptions = {}
) => {
  const { speed = 50, onComplete } = options;
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const indexRef = useRef(0);
  const textRef = useRef(text);

  useEffect(() => {
    // Reset if text changes
    if (textRef.current !== text) {
      textRef.current = text;
      setDisplayedText("");
      indexRef.current = 0;
      setIsTyping(true);
    }
  }, [text]);

  useEffect(() => {
    if (!isTyping || indexRef.current >= textRef.current.length) {
      if (indexRef.current >= textRef.current.length && onComplete) {
        onComplete();
      }
      return;
    }

    const timeout = setTimeout(() => {
      setDisplayedText((prev) => prev + textRef.current[indexRef.current]);
      indexRef.current++;

      if (indexRef.current >= textRef.current.length) {
        setIsTyping(false);
      }
    }, speed);

    return () => clearTimeout(timeout);
  }, [displayedText, isTyping, speed, onComplete]);

  const reset = () => {
    setDisplayedText("");
    indexRef.current = 0;
    setIsTyping(true);
  };

  const skip = () => {
    setDisplayedText(textRef.current);
    indexRef.current = textRef.current.length;
    setIsTyping(false);
  };

  return {
    displayedText,
    isTyping,
    reset,
    skip,
  };
};

export default useTypingAnimation;
