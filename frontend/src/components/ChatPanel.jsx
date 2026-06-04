import { useEffect, useRef, useState } from "react";
import useChat from "../hooks/useChat";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

const SUGGESTIONS = [
  "Top 5 MPs by attendance",
  "MPs with no questions asked",
  "Which MP asked the most questions?",
];

export default function ChatPanel() {
  const [open, setOpen] = useState(false);
  const { messages, isLoading, sendMessage } = useChat();
  const bottomRef = useRef(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, open]);

  return (
    <>
      {/* Floating toggle button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-brand-gradient px-5 py-3.5 text-sm font-semibold text-white shadow-lift transition-transform hover:scale-105"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
            <path fillRule="evenodd" d="M10 2c-2.236 0-4.43.18-6.57.524C1.993 2.755 1 4.014 1 5.426v5.148c0 1.413.993 2.67 2.43 2.902.848.137 1.705.248 2.57.331v3.443a.75.75 0 0 0 1.28.53l3.58-3.579a.78.78 0 0 1 .527-.224 41.202 41.202 0 0 0 5.183-.5c1.437-.232 2.43-1.49 2.43-2.903V5.426c0-1.413-.993-2.67-2.43-2.902A41.289 41.289 0 0 0 10 2Zm0 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2ZM8 9a1 1 0 1 1-2 0 1 1 0 0 1 2 0Zm5 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
          </svg>
          Ask about MPs
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-0 right-0 z-50 flex flex-col sm:bottom-6 sm:right-6 w-full sm:w-[380px] h-[70vh] sm:h-[520px] rounded-none sm:rounded-4xl overflow-hidden shadow-lift border border-slate-200/70 bg-white">
          {/* Header */}
          <div className="flex items-center justify-between bg-brand-gradient px-4 py-3.5 text-white">
            <span className="flex items-center gap-2 text-sm font-semibold">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-white/20">✦</span>
              Ask about MPs
            </span>
            <button
              onClick={() => setOpen(false)}
              className="text-white/70 transition-colors hover:text-white"
              aria-label="Close chat"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
                <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
              </svg>
            </button>
          </div>

          {/* Message area */}
          <div className="flex flex-1 flex-col gap-3 overflow-y-auto bg-slate-50 p-4">
            {messages.length === 0 && (
              <>
                <div className="rounded-2xl rounded-bl-sm bg-white px-4 py-3 text-sm text-slate-700 shadow-sm self-start max-w-[85%]">
                  Ask me anything about MPs. Try: <em>"Which MP from your state has the best attendance?"</em>
                </div>
                <div className="flex flex-wrap gap-2 mt-1">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => sendMessage(s)}
                      disabled={isLoading}
                      className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs text-indigo-700 hover:bg-indigo-100 transition-colors disabled:opacity-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </>
            )}

            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} isLoading={false} />
            ))}

            {isLoading && <ChatMessage isLoading />}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </div>
      )}
    </>
  );
}
