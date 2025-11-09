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
      onPress={onAnalyze}
      isLoading={isAnalyzing}
      color="primary"
      size="lg"
      variant="shadow"
      className={`font-semibold px-8 animate-glow ${className}`}
    >
      {isAnalyzing ? "Analyzing..." : "Analyze Portfolio"}
    </Button>
  );
};
