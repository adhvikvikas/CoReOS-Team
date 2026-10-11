import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  desc?: string;
  subtext?: string;
  subtitle?: string;
  icon?: LucideIcon;
  iconColor?: 'blue' | 'cyan' | 'green' | 'amber' | 'red' | 'purple' | string;
  trend?: string;
}

export default function MetricCard({
  title,
  value,
  desc,
  subtext,
  subtitle,
  icon: Icon,
  iconColor = 'blue',
  trend
}: MetricCardProps) {
  const colorMap: Record<string, { bg: string; border: string; text: string }> = {
    blue: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/20',
      text: 'text-[#60A5FA]',
    },
    cyan: {
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/20',
      text: 'text-[#34D3E9]',
    },
    green: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      text: 'text-[#34D399]',
    },
    amber: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      text: 'text-[#FBBF24]',
    },
    red: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/20',
      text: 'text-[#F87171]',
    },
    purple: {
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/20',
      text: 'text-[#A78BFA]',
    },
  };

  const colors = colorMap[iconColor] || {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    text: iconColor.startsWith('text-') ? iconColor : 'text-[#60A5FA]',
  };
  const description = desc || subtext || subtitle;

  return (
    <div className="bg-[#1A1F23] border border-[#303A40] rounded-xl p-5 flex items-start justify-between shadow-sm hover:border-[#4B5563] transition-colors">
      <div className="flex-1 min-w-0 pr-3">
        <div className="flex items-center space-x-2">
          <p className="text-xs font-medium text-[#717B86] uppercase tracking-wider truncate">{title}</p>
          {trend && (
            <span className="text-[10px] font-semibold text-[#34D399] bg-[#34D399]/10 px-1.5 py-0.5 rounded">
              {trend}
            </span>
          )}
        </div>
        <div className="text-2xl font-bold text-[#F3F4F6] mt-2 tracking-tight truncate">{value}</div>
        {description && (
          <p className="text-xs text-[#A1A1AA] mt-1 truncate">{description}</p>
        )}
      </div>
      {Icon && (
        <div className={`p-2.5 rounded-lg border ${colors.bg} ${colors.border} ${colors.text} shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
      )}
    </div>
  );
}
