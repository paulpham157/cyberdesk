import { motion } from "motion/react";
import { VercelIcon } from "@/components/playground/icons";
import { ComputerIcon } from "lucide-react";
import Link from "next/link";
import { AppLogo } from "../shared/app-logo";

export const ProjectInfo = () => {
  return (
    <motion.div className="w-full px-4">
      <div className="rounded-lg border-border border p-6 flex flex-col gap-4 text-center text-base dark:text-zinc-400">
        <p className="flex flex-row justify-center gap-4 items-center text-zinc-900 dark:text-zinc-50">
          <AppLogo />
          <span>+</span>
          <ComputerIcon />
        </p>
        <h3 className="text-center text-2xl font-bold">Cyberdesk Agent</h3>
        <p>
          This demo showcases a Computer Agent built with the{" "}
          <StyledLink href="https://www.anthropic.com/claude/sonnet">
            Anthropic Claude Sonnet 3.7
          </StyledLink>
          and <StyledLink href="https://cyberdesk.io">Cyberdesk</StyledLink>.
        </p>
        <p>
          {" "}
          The code for this demo is open source on{" "}
          <Link
            className="text-blue-500 dark:text-blue-400"
            href="https://github.com/cyberdesk-hq/cyberdesk-agent"
            target="_blank"
          >
            GitHub
          </Link>
          .
        </p>
      </div>
    </motion.div>
  );
};

const StyledLink = ({
  children,
  href,
}: {
  children: React.ReactNode;
  href: string;
}) => {
  return (
    <Link
      className="text-blue-500 dark:text-blue-400"
      href={href}
      target="_blank"
    >
      {children}
    </Link>
  );
};

// const Code = ({ text }: { text: string }) => {
//   return <code className="">{text}</code>;
// };
