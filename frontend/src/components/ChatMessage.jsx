import { useState } from "react";

function LoadingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.3s]" />
      <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.15s]" />
      <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" />
    </div>
  );
}

export default function ChatMessage({ message, isLoading }) {
  const [sqlOpen, setSqlOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-white px-4 py-3 shadow-sm">
          <LoadingDots />
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-3 text-sm text-white">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-white px-4 py-3 text-sm text-slate-800 shadow-sm">
        {message.text}
      </div>
      {message.sql && (
        <div className="max-w-[85%]">
          <button
            onClick={() => setSqlOpen((o) => !o)}
            className="text-xs text-slate-400 hover:text-slate-600 pl-1"
          >
            {sqlOpen ? "Hide query ▲" : "Show query ▼"}
          </button>
          {sqlOpen && (
            <pre className="mt-1 max-w-full overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-600 whitespace-pre-wrap">
              {message.sql}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
