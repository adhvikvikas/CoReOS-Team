import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'blue' | 'cyan' | 'green' | 'amber' | 'red' | 'neutral';
  className?: string;
}

export default function Badge({ children, variant = 'neutral', className = '' }: BadgeProps) {
  const variantStyles = {
    blue: 'bg-[#60A5FA]/10 text-[#60A5FA] border-[#60A5FA]/30',
    cyan: 'bg-[#34D3E9]/10 text-[#34D3E9] border-[#34D3E9]/30',
    green: 'bg-[#34D399]/10 text-[#34D399] border-[#34D399]/30',
    amber: 'bg-[#FBBF24]/10 text-[#FBBF24] border-[#FBBF24]/30',
    red: 'bg-[#F87171]/10 text-[#F87171] border-[#F87171]/30',
    neutral: 'bg-[#20262B] text-[#A1A1AA] border-[#303A40]',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
