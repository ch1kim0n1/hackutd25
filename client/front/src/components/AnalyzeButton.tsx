import { Button } from "@heroui/button";
import React from "react";

interface AnalyzeButtonProps {
  onAnalyze: () => void;
  isAnalyzing?: boolean;
  className?: string;
}

export const AnalyzeButton: React.FC<AnalyzeButtonProps> = ({
  onAnalyze,
  isAnalyzing = false,
  className = "",
}) => {
  return (
    <Button
      className={`font-semibold px-8 animate-glow ${className}`}
      color="primary"
      isLoading={isAnalyzing}
      size="lg"
      variant="shadow"
      onPress={onAnalyze}
    >
      {isAnalyzing ? "Analyzing..." : "Analyze Portfolio"}
    </Button>
  );
};
