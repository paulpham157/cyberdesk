import React from "react";
import { FaExclamationTriangle } from "react-icons/fa";

export function ChatError({ error, onRetry }: { error: unknown, onRetry: () => void }) {
  if (!error) return null;
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border border-red-200 bg-white/90 shadow-sm px-6 py-2 mb-2 w-full mx-auto">
      <div className="flex items-center gap-2 text-red-600">
        <FaExclamationTriangle className="text-base" />
        <span className="font-semibold text-sm">An error occurred</span>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="mt-1 px-4 py-1.5 rounded-md bg-red-600 hover:bg-red-700 text-white font-medium shadow transition-colors focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed text-sm"
      >
        Retry
      </button>
    </div>
  );
} 