import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const suggestions = [
  {
    text: "Create a website about big floppas",
    prompt: "Create a website about big floppas using Next.js, Tailwind CSS, and TypeScript",
  },
  {
    text: "Create a new text file",
    prompt: "Open a text editor and create a new file called notes.txt and write 'let's go cyberdesk!'",
  },
  {
    text: "Research the latest trends in AI and write a report",
    prompt: "Research the latest trends in AI and write a report",
  },
];

export const PromptSuggestions = ({
  submitPrompt,
  disabled,
}: {
  submitPrompt: (prompt: string) => void;
  disabled: boolean;
}) => {
  return (
    <div className="flex flex-wrap items-center gap-3 px-4">
      {suggestions.map((suggestion, index) => (
        <Button
          key={index}
          variant="pill"
          size="pill"
          onClick={() => submitPrompt(suggestion.prompt)}
          disabled={disabled}
        >
          <span>
            <span className="text-black text-sm">
              {suggestion.text.toLowerCase()}
            </span>
          </span>
          <ArrowUpRight className="ml-1 h-2 w-2 sm:h-3 sm:w-3 text-zinc-500 group-hover:opacity-70" />
        </Button>
      ))}
    </div>
  );
};
