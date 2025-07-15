import React from 'react';
import { cn } from '@/utils/misc-utils'; // Assuming you use shadcn/ui or similar for utils

interface LogoTextProps extends React.HTMLAttributes<HTMLSpanElement> {}

export const LogoText: React.FC<LogoTextProps> = ({ className, ...props }) => {
  return (
    <span
      className={cn(
        'text-[35px] font-medium tracking-tight text-gray-950',
        className
      )}
      {...props}
    >
      Cyberdesk
    </span>
  );
};
