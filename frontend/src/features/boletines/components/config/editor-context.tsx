"use client";

import { createContext, useContext, type ReactNode } from "react";

interface EditorContextValue {
  /** Whether this editor is for the event loop template */
  isInEventLoop: boolean;
}

const EditorContext = createContext<EditorContextValue>({ isInEventLoop: false });

export function EditorContextProvider({
  children,
  isInEventLoop
}: {
  children: ReactNode;
  isInEventLoop: boolean;
}) {
  return (
    <EditorContext.Provider value={{ isInEventLoop }}>
      {children}
    </EditorContext.Provider>
  );
}

export function useEditorContext() {
  return useContext(EditorContext);
}
