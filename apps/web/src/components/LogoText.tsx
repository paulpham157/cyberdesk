import React from 'react';
import { cn } from '@/lib/utils'; // Assuming you use shadcn/ui or similar for utils

interface LogoTextProps extends React.HTMLAttributes<HTMLSpanElement> {}

export const LogoText: React.FC<LogoTextProps> = ({ className, ...props }) => {
  return (
    <span
      className={cn(
        'text-xl font-medium tracking-tight text-gray-950',
        className
      )}
      {...props}
    >
      Cyberdesk
    </span>
  );
};
