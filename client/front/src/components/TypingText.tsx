import { useTypingAnimation } from "@/hooks/useTypingAnimation";
import { cn } from "@/lib/utils";

interface TypingTextProps {
  text: string;
  speed?: number;
  className?: string;
  onComplete?: () => void;
  showCursor?: boolean;
}

export const TypingText = ({
  text,
  speed = 50,
  className,
  onComplete,
  showCursor = true,
}: TypingTextProps) => {
  const { displayedText, isTyping } = useTypingAnimation(text, {
    speed,
    onComplete,
  });

  return (
    <span className={cn("inline-block", className)}>
      {displayedText}
      {showCursor && isTyping && (
        <span className="inline-block w-0.5 h-4 bg-primary ml-1 animate-pulse" />
      )}
    </span>
  );
};

export default TypingText;
