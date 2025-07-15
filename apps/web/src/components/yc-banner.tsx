import React from 'react'

export function YCBanner() {
  return (
    <div className="flex justify-center my-5">
      <a
        href="https://www.ycombinator.com/"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-3 rounded-lg px-6 py-3 hover:bg-gray-50 transition-colors"
      >
        <span className="text-xl font-medium text-gray-800">Backed by</span>
        <span className="flex items-center gap-1">
          <span className="inline-flex items-center justify-center bg-[#FF6600] px-3 py-2">
            <span className="text-xl font-semibold text-white leading-none">Y</span>
          </span>
          <span className="text-xl font-medium text-gray-800 ml-1">Combinator</span>
        </span>
      </a>
    </div>
  )
} 