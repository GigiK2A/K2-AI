import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm placeholder:text-[color:var(--color-text-muted)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)] disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
