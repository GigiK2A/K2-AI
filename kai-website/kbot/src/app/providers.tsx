"use client";

import { ClerkProvider } from "@clerk/nextjs";

const PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      {children}
    </ClerkProvider>
  );
}
