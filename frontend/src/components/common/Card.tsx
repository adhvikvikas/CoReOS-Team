import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
}

export default function Card({ children, className = '', title, subtitle, headerAction }: CardProps) {
  return (
    <div className={`bg-[#1A1F23] border border-[#303A40] rounded-xl p-6 ${className}`}>
      {(title || headerAction) && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#303A40]">
          <div>
            {title && <h2 className="text-base font-semibold text-[#F3F4F6]">{title}</h2>}
            {subtitle && <p className="text-xs text-[#717B86] mt-0.5">{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
