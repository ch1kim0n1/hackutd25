import * as React from "react";

export const TooltipProvider = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const Tooltip = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const TooltipTrigger = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ children, ...props }, ref) => <div ref={ref} {...props}>{children}</div>
);
TooltipTrigger.displayName = "TooltipTrigger";
export const TooltipContent = ({ children }: { children: React.ReactNode }) => null;
