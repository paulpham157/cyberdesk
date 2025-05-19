import { useEffect, useRef, type RefObject } from 'react';

export function useScrollToBottom(): [
  RefObject<HTMLDivElement>,
  RefObject<HTMLDivElement>,
] {
  const containerRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;

    if (container) {
      const observer = new MutationObserver(() => {
        // Directly set scrollTop to scrollHeight to scroll to the bottom of the container.
        // This manipulation is localized to the 'container' element.
        container.scrollTop = container.scrollHeight;
      });

      // Observe changes that would typically require scrolling in a chat interface
      observer.observe(container, {
        childList: true,    // For new messages being added
        subtree: true,      // For changes within messages (e.g., streaming content updating)
        characterData: true // Specifically for text changes during streaming
      });

      // Initial scroll to bottom in case there's pre-existing content 
      // that might not trigger an immediate mutation but should be scrolled past.
      // Use a microtask to ensure layout has been calculated.
      queueMicrotask(() => {
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      });

      return () => observer.disconnect();
    }
  }, []); // Effect runs once on mount

  return [containerRef, endRef];
}