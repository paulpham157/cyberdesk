import { type BaseLayoutProps } from "fumadocs-ui/layout";

// basic configuration here
export const baseOptions: BaseLayoutProps = {
  nav: {
    title: "Cyberdesk Docs",
  },
  links: [
    {
      text: "Documentation",
      url: "/docs",
      active: "nested-url",
    },
    {
      text: "Main Site",
      url: "https://cyberdesk.io",
    }
  ],
  githubUrl: "https://github.com/cyberdesk-hq/cyberdesk",
};
