/**
 * Context for sharing event template content between editors and previews
 */

"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { JSONContent } from "@tiptap/react";

interface EventTemplateContextType {
  /** Current event template content from the eventEditor */
  eventTemplateContent: JSONContent | null;
  /** Update the template content */
  setEventTemplateContent: (content: JSONContent | null) => void;
}

const EventTemplateContext = createContext<EventTemplateContextType | null>(null);

export function EventTemplateProvider({ children }: { children: ReactNode }) {
  const [eventTemplateContent, setEventTemplateContentState] = useState<JSONContent | null>(null);

  const setEventTemplateContent = useCallback((content: JSONContent | null) => {
    setEventTemplateContentState(content);
  }, []);

  return (
    <EventTemplateContext.Provider value={{ eventTemplateContent, setEventTemplateContent }}>
      {children}
    </EventTemplateContext.Provider>
  );
}

export function useEventTemplateContext() {
  const context = useContext(EventTemplateContext);
  if (!context) {
    throw new Error("useEventTemplateContext must be used within EventTemplateProvider");
  }
  return context;
}

/** Safe hook that returns null if not within provider */
export function useEventTemplateContextSafe() {
  return useContext(EventTemplateContext);
}
