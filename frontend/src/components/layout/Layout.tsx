import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Activity,
  Cpu,
  ShieldAlert,
  HeartPulse,
  BarChart2,
  FileText,
  Zap,
  CheckCircle2,
  Menu,
  X
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/dataset', label: 'Dataset Explorer', icon: Database },
  { path: '/simulation', label: 'Simulation Lab', icon: Activity },
  { path: '/agents', label: 'Agent Control Center', icon: Cpu },
  { path: '/conflicts', label: 'Conflict Analysis', icon: ShieldAlert },
  { path: '/healing', label: 'Self-Healing Center', icon: HeartPulse },
  { path: '/benchmarks', label: 'Benchmark Lab', icon: BarChart2 },
  { path: '/reports', label: 'Reports & Exports', icon: FileText },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen bg-[#0F1010] text-[#F3F4F6] font-sans antialiased overflow-hidden">
      {/* Top Header */}
      <header className="h-14 bg-[#101416] border-b border-[#303A40] flex items-center justify-between px-4 lg:px-6 z-20 shrink-0">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-1.5 rounded text-[#A1A1AA] hover:text-white hover:bg-[#1A1F23] transition-colors"
            aria-label="Toggle Navigation"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          
          <Link to="/" className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-[#34D3E9]">
              <Zap className="w-4 h-4 fill-[#34D3E9]" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-white">CoReOS</span>
              <span className="hidden sm:inline-block text-xs text-[#717B86] ml-2 font-medium">Multi-Agent OS</span>
            </div>
          </Link>
        </div>

        <div className="flex items-center space-x-3 sm:space-x-4">
          {/* Dataset Loaded Badge */}
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-[#34D399]/10 border border-[#34D399]/30 text-[#34D399] text-xs font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Dataset Loaded</span>
          </div>
        </div>
      </header>

      {/* Main Body with Sidebar + Content */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Mobile Backdrop */}
        {mobileOpen && (
          <div
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          />
        )}

        {/* Left Sidebar */}
        <aside
          className={`fixed lg:static top-14 bottom-0 left-0 z-40 w-64 bg-[#111719] border-r border-[#303A40] flex flex-col shrink-0 transition-transform duration-200 ease-in-out ${
            mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          <nav className="flex-1 overflow-y-auto py-3 px-3">
            <ul className="space-y-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={() => setMobileOpen(false)}
                      className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-[#1D4ED8] text-white shadow-sm shadow-blue-500/20 font-semibold'
                          : 'text-[#A1A1AA] hover:bg-[#1A1F23] hover:text-[#F3F4F6]'
                      }`}
                    >
                      <Icon
                        className={`w-4 h-4 mr-3 shrink-0 ${
                          isActive ? 'text-white' : 'text-[#717B86]'
                        }`}
                      />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Sidebar Footer info */}
          <div className="p-3 border-t border-[#303A40] text-xs text-[#717B86]">
            <div className="flex items-center justify-between">
              <span>CoReOS Research Lab</span>
              <span className="text-[#34D399] font-medium">v1.0</span>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-[#0F1010]">
          <div className={`p-4 sm:p-6 lg:p-8 mx-auto min-h-full transition-all duration-150 ${location.pathname === '/' ? 'max-w-[1600px] 2xl:max-w-[1720px]' : 'max-w-7xl'}`}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
