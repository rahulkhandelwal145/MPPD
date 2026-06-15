import { useState } from "react";

export default function ChatPanel() {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      {showTooltip && (
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-lift text-sm text-slate-600 max-w-[220px] text-center">
          <p className="font-medium text-slate-800">AI Assistant</p>
          <p className="mt-0.5 text-xs text-slate-500">Incoming feature — coming soon.</p>
        </div>
      )}
      <button
        onClick={() => setShowTooltip((v) => !v)}
        className="flex items-center gap-2 rounded-full bg-brand-gradient px-5 py-3.5 text-sm font-semibold text-white shadow-lift transition-transform hover:scale-105"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
          <path fillRule="evenodd" d="M10 2c-2.236 0-4.43.18-6.57.524C1.993 2.755 1 4.014 1 5.426v5.148c0 1.413.993 2.67 2.43 2.902.848.137 1.705.248 2.57.331v3.443a.75.75 0 0 0 1.28.53l3.58-3.579a.78.78 0 0 1 .527-.224 41.202 41.202 0 0 0 5.183-.5c1.437-.232 2.43-1.49 2.43-2.903V5.426c0-1.413-.993-2.67-2.43-2.902A41.289 41.289 0 0 0 10 2Zm0 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2ZM8 9a1 1 0 1 1-2 0 1 1 0 0 1 2 0Zm5 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
        </svg>
        Ask about MPs
      </button>
    </div>
  );
}
