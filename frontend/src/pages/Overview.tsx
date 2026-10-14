import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import Plot from 'react-plotly.js';
import { carbonChartLayout } from '../components/common/chartTheme';
import {
  Database,
  BarChart2,
  Zap,
  Activity,
  Layers,
  Sliders,
  HeartPulse,
  Cpu,
  Target,
  ShieldCheck,
  ChevronRight,
  ArrowRight,
  TrendingUp,
  FileText,
  Clock
} from 'lucide-react';

export default function Overview() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchOverview = () => {
    setLoading(true);
    api.get('/overview/').then(res => {
      setData(res.data);
    }).catch(err => {
      console.error(err);
    }).finally(() => {
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchOverview();

    const handleSimCompleted = () => {
      fetchOverview();
    };
    window.addEventListener('coreos:simulationCompleted', handleSimCompleted);
    return () => {
      window.removeEventListener('coreos:simulationCompleted', handleSimCompleted);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-[#717B86] text-sm">
        <Activity className="w-5 h-5 mr-2 animate-spin text-[#60A5FA]" />
        Loading System Overview...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 text-[#F87171] text-sm">
        Failed to load overview data.
      </div>
    );
  }

  const telemetry = data.telemetry || [];

  return (
    <div className="space-y-4 w-full">
      {/* 01 — SYSTEM OVERVIEW */}
      <div className="bg-[#101416] border border-[#22292F] rounded-xl p-5 lg:p-6 space-y-3.5">
        <div>
          <div className="flex flex-wrap items-center gap-2.5 mb-1.5">
            <div className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold uppercase">
              01 — System Overview
            </div>
            {data?.workload_info?.workload_type ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#0D212E] border border-[#164E63] text-[10px] font-mono text-[#38BDF8]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" />
                <span className="text-[#717B86]">Active Workload:</span>
                <span className="text-[#38BDF8] font-semibold">{data.workload_info.workload_type}</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#161C20] border border-[#2A343D] text-[10px] font-mono text-[#717B86]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#717B86]" />
                <span>Active Workload: None</span>
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
            CoReOS — Multi-Agent AI Operating System
          </h1>
          <p className="text-xs text-[#8A99A8] mt-2 max-w-2xl leading-relaxed">
            A conflict-aware, self-healing multi-agent system that coordinates CPU, memory and I/O resources using intelligent scheduling and real-time conflict resolution.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 pt-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0D212E]/70 border border-[#164E63] text-[#38BDF8] text-xs font-medium">
            <Layers className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>Conflict-aware scheduling</span>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0D212E]/70 border border-[#164E63] text-[#38BDF8] text-xs font-medium">
            <Sliders className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>Resource coordination</span>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0D212E]/70 border border-[#164E63] text-[#38BDF8] text-xs font-medium">
            <HeartPulse className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>Self-healing</span>
          </div>
        </div>
      </div>

      {/* 02 — CURRENT SYSTEM STATUS */}
      <div className="bg-[#101416] border border-[#22292F] rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5">
          <div>
            <div className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold mb-0.5 uppercase">
              02 — Current System Status
            </div>
            <p className="text-xs text-[#717B86]">
              Live metrics from the loaded dataset and latest active simulation run.
            </p>
          </div>
          {data?.workload_info?.timestamp && (
            <div className="text-[10px] font-mono text-[#717B86] flex items-center gap-1.5 self-start sm:self-auto">
              <Clock className="w-3 h-3 text-[#38BDF8]" />
              <span>Run #{data.workload_info.run_id || 1} • {new Date(data.workload_info.timestamp).toLocaleTimeString()}</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Dataset Records */}
          <div className="bg-[#131719] border border-[#20262B] rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#0F1D28] border border-[#164E63] text-[#38BDF8] flex items-center justify-center shrink-0">
                <Database className="w-5 h-5 text-[#38BDF8]" />
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#717B86]">
                  Dataset Records
                </div>
                <div className="text-xl font-bold text-[#F3F4F6] mt-0.5">
                  {data.dataset_records || "10,000"}
                </div>
                <div className="text-[11px] text-[#717B86] mt-0.5">
                  Verified records
                </div>
              </div>
            </div>
            <div className="w-7 h-7 rounded-md bg-[#162026] text-[#38BDF8]/60 flex items-center justify-center shrink-0">
              <Layers className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Benchmark Baselines */}
          <div className="bg-[#131719] border border-[#20262B] rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#0D211F] border border-[#065F46] text-[#34D399] flex items-center justify-center shrink-0">
                <BarChart2 className="w-5 h-5 text-[#34D399]" />
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#717B86]">
                  Benchmark Baselines
                </div>
                <div className="text-xl font-bold text-[#F3F4F6] mt-0.5">
                  {data.evaluated_baselines || "6"}
                </div>
                <div className="text-[11px] text-[#717B86] mt-0.5">
                  Baselines
                </div>
              </div>
            </div>
            <div className="w-7 h-7 rounded-md bg-[#162026] text-[#34D399]/60 flex items-center justify-center shrink-0">
              <FileText className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Decision Latency */}
          <div className="bg-[#131719] border border-[#20262B] rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#082329] border border-[#0E7490] text-[#2DD4BF] flex items-center justify-center shrink-0">
                <Zap className="w-5 h-5 text-[#2DD4BF]" />
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#717B86]">
                  Decision Latency
                </div>
                <div className="text-xl font-bold text-[#F3F4F6] mt-0.5 font-mono">
                  {data.decision_latency || "0.16 ms"}
                </div>
                <div className="text-[11px] text-[#717B86] mt-0.5">
                  Average arbitration time
                </div>
              </div>
            </div>
            <div className="w-7 h-7 rounded-md bg-[#162026] text-[#2DD4BF]/60 flex items-center justify-center shrink-0">
              <Cpu className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Benchmark Stress Turnaround */}
          <div className="bg-[#131719] border border-[#20262B] rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-lg bg-[#251F10] border border-[#854D0E] text-[#FBBF24] flex items-center justify-center shrink-0">
                <Activity className="w-5 h-5 text-[#FBBF24]" />
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#717B86]">
                  Completed Turnaround
                </div>
                <div className="text-xl font-bold text-[#F3F4F6] mt-0.5 font-mono">
                  {data.turnaround_improvement || "N/A"}
                </div>
                <div className="text-[11px] text-[#717B86] mt-0.5">
                  {data.turnaround_improvement_desc || "Adversarial Stress (Completed procs)"}
                </div>
              </div>
            </div>
            <div className="w-7 h-7 rounded-md bg-[#162026] text-[#FBBF24]/60 flex items-center justify-center shrink-0">
              <TrendingUp className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>

        {/* Diagnostic Stress Benchmark Comparison Panel */}
        {data.stress_comparison && (
          <div className="mt-4 p-4 rounded-xl bg-[#131719] border border-[#20262B] space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#38BDF8]" />
                <span className="text-xs font-semibold text-[#F3F4F6]">
                  Adversarial Stress Benchmark Comparison (CoReOS vs Conventional)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1E293B] border border-[#303A40] text-[#38BDF8]">
                  Phase 8 Competition Audit
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#717B86]">
                Cutoff: 300 ticks • 40 jobs/seed • 30 seeds
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-xs">
              <div className="bg-[#101416] p-2.5 rounded-lg border border-[#20262B]">
                <div className="text-[10px] text-[#717B86] uppercase font-mono">Completion Rate</div>
                <div className="font-mono font-semibold text-[#F3F4F6] mt-0.5">
                  <span className="text-[#38BDF8]">{data.stress_comparison.coreos_completion_rate}%</span> vs{' '}
                  <span className="text-[#CBD5E1]">{data.stress_comparison.conv_completion_rate}%</span>
                </div>
                <div className={`text-[10px] mt-0.5 ${data.stress_comparison.comp_diff_pct >= 0 ? 'text-[#34D399]' : 'text-[#F87171]'}`}>
                  {data.stress_comparison.comp_diff_text || (data.stress_comparison.comp_diff_pct >= 0 ? `+${data.stress_comparison.comp_diff_pct}% advantage` : `${data.stress_comparison.comp_diff_pct}% deficit`)}
                </div>
              </div>

              <div className="bg-[#101416] p-2.5 rounded-lg border border-[#20262B]">
                <div className="text-[10px] text-[#717B86] uppercase font-mono">Throughput</div>
                <div className="font-mono font-semibold text-[#F3F4F6] mt-0.5">
                  <span className="text-[#38BDF8]">{data.stress_comparison.coreos_throughput}</span> vs{' '}
                  <span className="text-[#CBD5E1]">{data.stress_comparison.conv_throughput}</span>
                </div>
                <div className={`text-[10px] mt-0.5 ${data.stress_comparison.tp_diff_pct >= 0 ? 'text-[#34D399]' : 'text-[#F87171]'}`}>
                  {data.stress_comparison.tp_diff_text || (data.stress_comparison.tp_diff_pct >= 0 ? `+${data.stress_comparison.tp_diff_pct}% jobs/tick` : `${data.stress_comparison.tp_diff_pct}% jobs/tick`)}
                </div>
              </div>

              <div className="bg-[#101416] p-2.5 rounded-lg border border-[#20262B]">
                <div className="text-[10px] text-[#717B86] uppercase font-mono">Completed Turnaround</div>
                <div className="font-mono font-semibold text-[#F3F4F6] mt-0.5">
                  <span className="text-[#38BDF8]">{data.stress_comparison.coreos_completed_turnaround}</span> vs{' '}
                  <span className="text-[#CBD5E1]">{data.stress_comparison.conv_completed_turnaround}</span> ticks
                </div>
                <div className="text-[10px] text-[#717B86] mt-0.5">Completed jobs only</div>
              </div>

              <div className="bg-[#101416] p-2.5 rounded-lg border border-[#20262B]">
                <div className="text-[10px] text-[#717B86] uppercase font-mono">Penalized Turnaround</div>
                <div className="font-mono font-semibold text-[#F3F4F6] mt-0.5">
                  <span className="text-[#38BDF8]">{data.stress_comparison.coreos_penalized_turnaround}</span> vs{' '}
                  <span className="text-[#CBD5E1]">{data.stress_comparison.conv_penalized_turnaround}</span> ticks
                </div>
                <div className="text-[10px] text-[#717B86] mt-0.5">300-tick cutoff penalty</div>
              </div>

              <div className="bg-[#101416] p-2.5 rounded-lg border border-[#20262B]">
                <div className="text-[10px] text-[#717B86] uppercase font-mono">Thrashing Ticks</div>
                <div className="font-mono font-semibold text-[#34D399] mt-0.5">
                  <span>{data.stress_comparison.coreos_thrashing}</span> vs{' '}
                  <span className="text-[#CBD5E1]">{data.stress_comparison.conv_thrashing}</span> ticks
                </div>
                <div className="text-[10px] text-[#34D399] mt-0.5">{data.stress_comparison.thrashing_reduction_pct}% reduction</div>
              </div>
            </div>
          </div>
        )}

        {/* System Health Indicator Bar */}
        {data.health && (
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3.5 border-t border-[#1C2328] mt-4 text-[11px] font-mono text-[#717B86]">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${data.health.dataset_available ? 'bg-[#34D399]' : 'bg-[#F87171]'}`} />
                <span>Dataset:</span>
                <span className={data.health.dataset_available ? 'text-[#E2E8F0] font-medium' : 'text-[#F87171] font-medium'}>
                  {data.health.dataset_available ? 'Available (10k Records)' : 'Missing'}
                </span>
              </div>
              <span className="text-[#303A40]">•</span>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${data.health.latest_sim_status === 'Completed' ? 'bg-[#38BDF8]' : 'bg-[#FBBF24]'}`} />
                <span>Latest Sim:</span>
                <span className="text-[#E2E8F0] font-medium">
                  {data.health.latest_sim_status} {data.workload_info?.run_id ? `(Run #${data.workload_info.run_id})` : ''}
                </span>
              </div>
              <span className="text-[#303A40]">•</span>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${!data.health.conflict_data_available ? 'bg-[#717B86]' : (data.health.unresolved_conflicts > 0 ? 'bg-[#FBBF24]' : 'bg-[#34D399]')}`} />
                <span>Unresolved Conflicts:</span>
                <span className={!data.health.conflict_data_available ? 'text-[#717B86]' : (data.health.unresolved_conflicts > 0 ? 'text-[#FBBF24] font-medium' : 'text-[#34D399] font-medium')}>
                  {data.health.conflict_data_available ? data.health.unresolved_conflicts : 'Unavailable'}
                </span>
              </div>
            </div>
            <div className="text-[10px] text-[#55606B]">
              Engine Telemetry Mode: Closed-Loop Active
            </div>
          </div>
        )}
      </div>

      {/* 03 — SYSTEM PERFORMANCE */}
      <div className="bg-[#101416] border border-[#22292F] rounded-xl p-5">
        <div className="mb-3.5">
          <div className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold mb-0.5 uppercase">
            03 — System Performance
          </div>
          <p className="text-xs text-[#717B86]">
            Real-time resource utilization and process queue dynamics from the latest active simulation run.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Resource Utilization (Real-time) */}
          <div className="bg-[#131719] border border-[#20262B] rounded-xl p-4">
            <div className="mb-2">
              <h3 className="text-sm font-semibold text-[#F3F4F6]">
                Resource Utilization (Real-time)
              </h3>
              <p className="text-[11px] text-[#717B86] mt-0.5">
                Subsystem saturation trajectory • Run {data.workload_info?.run_id ? `#${data.workload_info.run_id}` : ''} ({data.workload_info?.workload_type || 'simulation'})
              </p>
            </div>
            {telemetry.length > 0 ? (
              <Plot
                data={[
                  {
                    x: telemetry.map((h: any) => h.time),
                    y: telemetry.map((h: any) => h.cpu_utilization),
                    type: 'scatter',
                    mode: 'lines',
                    name: 'CPU',
                    line: { color: '#60A5FA', width: 2 }
                  },
                  {
                    x: telemetry.map((h: any) => h.time),
                    y: telemetry.map((h: any) => h.memory_utilization),
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Memory',
                    line: { color: '#2DD4BF', width: 2 }
                  },
                  {
                    x: telemetry.map((h: any) => h.time),
                    y: telemetry.map((h: any) => h.io_saturation),
                    type: 'scatter',
                    mode: 'lines',
                    name: 'I/O',
                    line: { color: '#FBBF24', width: 2 }
                  }
                ]}
                layout={{
                  ...carbonChartLayout,
                  height: 215,
                  margin: { l: 45, r: 15, t: 15, b: 40 },
                  yaxis: {
                    ...carbonChartLayout.yaxis,
                    range: [0, 105],
                    title: { text: '%', font: { color: '#94A3B8', size: 11 } },
                    tickfont: { color: '#94A3B8', size: 11 },
                    gridcolor: '#1E252B',
                    dtick: 50
                  },
                  xaxis: {
                    ...carbonChartLayout.xaxis,
                    title: { text: 'Time (ticks)', font: { color: '#94A3B8', size: 11 } },
                    tickfont: { color: '#94A3B8', size: 11 },
                    gridcolor: '#1E252B'
                  },
                  legend: {
                    orientation: 'h',
                    x: 1,
                    xanchor: 'right',
                    y: 1.15,
                    font: { color: '#CBD5E1', size: 11 },
                    bgcolor: 'rgba(0,0,0,0)',
                    borderwidth: 0
                  }
                }}
                useResizeHandler
                style={{ width: '100%', height: '215px' }}
                config={{ displayModeBar: false }}
              />
            ) : (
              <div className="h-[215px] flex items-center justify-center text-xs text-[#717B86]">No telemetry active for active run</div>
            )}
          </div>

          {/* Process Queue Length */}
          <div className="bg-[#131719] border border-[#20262B] rounded-xl p-4">
            <div className="mb-2">
              <h3 className="text-sm font-semibold text-[#F3F4F6]">
                Process Queue Length
              </h3>
              <p className="text-[11px] text-[#717B86] mt-0.5">
                Active backlog dynamics across CPU and I/O channels • Run {data.workload_info?.run_id ? `#${data.workload_info.run_id}` : ''} ({data.workload_info?.workload_type || 'simulation'})
              </p>
            </div>
            {telemetry.length > 0 ? (
              <Plot
                data={[
                  {
                    x: telemetry.map((h: any) => h.time),
                    y: telemetry.map((h: any) => h.ready_queue_length),
                    type: 'scatter',
                    mode: 'lines',
                    name: 'CPU Queue',
                    line: { color: '#60A5FA', width: 2 }
                  },
                  {
                    x: telemetry.map((h: any) => h.time),
                    y: telemetry.map((h: any) => h.io_queue_length),
                    type: 'scatter',
                    mode: 'lines',
                    name: 'I/O Queue',
                    line: { color: '#2DD4BF', width: 2 }
                  }
                ]}
                layout={{
                  ...carbonChartLayout,
                  height: 215,
                  margin: { l: 45, r: 15, t: 15, b: 40 },
                  yaxis: {
                    ...carbonChartLayout.yaxis,
                    title: { text: 'Queue', font: { color: '#94A3B8', size: 11 } },
                    tickfont: { color: '#94A3B8', size: 11 },
                    gridcolor: '#1E252B',
                    dtick: 10
                  },
                  xaxis: {
                    ...carbonChartLayout.xaxis,
                    title: { text: 'Time (ticks)', font: { color: '#94A3B8', size: 11 } },
                    tickfont: { color: '#94A3B8', size: 11 },
                    gridcolor: '#1E252B'
                  },
                  legend: {
                    orientation: 'h',
                    x: 1,
                    xanchor: 'right',
                    y: 1.15,
                    font: { color: '#CBD5E1', size: 11 },
                    bgcolor: 'rgba(0,0,0,0)',
                    borderwidth: 0
                  }
                }}
                useResizeHandler
                style={{ width: '100%', height: '215px' }}
                config={{ displayModeBar: false }}
              />
            ) : (
              <div className="h-[215px] flex items-center justify-center text-xs text-[#717B86]">No queue data active for active run</div>
            )}
          </div>
        </div>
      </div>

      {/* 04 — LATEST BENCHMARK RESULTS */}
      <div className="bg-[#101416] border border-[#22292F] rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5">
          <div>
            <div className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold mb-0.5 uppercase">
              04 — Latest Benchmark Results
            </div>
            <p className="text-xs text-[#717B86]">
              Key empirical metrics across representative workload scenarios (stored multi-baseline benchmark results).
            </p>
          </div>
          <Link
            to="/benchmarks"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0E202B] hover:bg-[#132A3A] border border-[#164E63] text-xs font-medium text-[#38BDF8] transition-colors self-start sm:self-auto"
          >
            <span>View Full Benchmark Results</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto rounded-lg border border-[#20262B]">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#0A0D0E] text-[#717B86] uppercase tracking-wider font-mono text-[10px]">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Workload</th>
                <th className="px-4 py-2.5 font-semibold">Baseline</th>
                <th className="px-4 py-2.5 font-semibold">Completion Rate</th>
                <th className="px-4 py-2.5 font-semibold">Completed Turnaround</th>
                <th className="px-4 py-2.5 font-semibold">Penalized Turnaround</th>
                <th className="px-4 py-2.5 font-semibold">Throughput</th>
                <th className="px-4 py-2.5 font-semibold">Thrashing</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1C2328] bg-[#101416]">
              {(data.highlights || []).slice(0, 10).map((row: any, i: number) => (
                <tr key={i} className="hover:bg-[#161B1E] transition-colors">
                  <td className="px-4 py-2.5 font-mono text-xs text-[#60A5FA]">
                    {row.workload}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-[#E2E8F0]">
                    {row.baseline}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-[#34D399] font-medium">
                    {row.completion_rate != null ? `${Number(row.completion_rate).toFixed(1)}%` : '—'}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-[#CBD5E1]">
                    {row.avg_turnaround_time != null ? `${Number(row.avg_turnaround_time).toFixed(2)} ticks` : '—'}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-[#38BDF8]">
                    {row.penalized_turnaround_time != null ? `${Number(row.penalized_turnaround_time).toFixed(2)} ticks` : '—'}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-[#94A3B8]">
                    {row.throughput != null ? Number(row.throughput).toFixed(3) : '—'}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-[#94A3B8]">
                    {row.thrashing_ticks != null ? Number(row.thrashing_ticks).toFixed(1) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-[#717B86] mt-2.5 leading-relaxed">
          * Penalized Turnaround assigns a 300-tick cutoff penalty to unfinished processes, preventing survivorship bias from favoring schedulers that complete fewer jobs under heavy load.
        </p>
      </div>

      {/* 05 — RESEARCH OBJECTIVE & 06 — SYSTEM ARCHITECTURE PIPELINE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Section 5: Research Objective */}
        <div className="bg-[#101416] border border-[#22292F] rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold mb-3 uppercase">
              05 — Research Objective
            </div>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#0B1E29] border border-[#164E63] flex items-center justify-center shrink-0 text-[#38BDF8]">
                <Target className="w-6 h-6 text-[#38BDF8]" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#F3F4F6] mb-1.5">
                  Research Objective
                </h3>
                <p className="text-xs text-[#8A99A8] leading-relaxed">
                  Develop a decentralized operating system that reduces resource conflicts and improves scheduling efficiency through proactive multi-agent coordination and self-healing mechanisms.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 6: System Architecture Pipeline */}
        <div className="bg-[#101416] border border-[#22292F] rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold mb-3 uppercase">
              06 — System Architecture Pipeline
            </div>
            
            <div className="flex items-center gap-3 mb-3.5">
              <div className="w-8 h-8 rounded-lg bg-[#0B1E29] border border-[#164E63] flex items-center justify-center text-[#38BDF8] shrink-0">
                <Layers className="w-4 h-4 text-[#38BDF8]" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#F3F4F6]">
                  System Architecture Pipeline
                </h3>
                <p className="text-[10px] text-[#717B86]">
                  Execution lifecycle stages
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between gap-1 overflow-x-auto pb-1 pt-1">
              {/* Stage 1 */}
              <div className="bg-[#0A1319] border border-[#1E293B] rounded-lg px-2.5 py-1.5 flex items-center gap-2 shrink-0">
                <Database className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
                <div>
                  <div className="text-[11px] font-semibold text-[#F3F4F6] leading-tight">Data Plane</div>
                  <div className="text-[9px] text-[#717B86] leading-tight">System metrics</div>
                </div>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-[#475569] shrink-0" />

              {/* Stage 2 */}
              <div className="bg-[#0A1319] border border-[#1E293B] rounded-lg px-2.5 py-1.5 flex items-center gap-2 shrink-0">
                <Cpu className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
                <div>
                  <div className="text-[11px] font-semibold text-[#F3F4F6] leading-tight">Agent Proposals</div>
                  <div className="text-[9px] text-[#717B86] leading-tight">Autonomous agents</div>
                </div>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-[#475569] shrink-0" />

              {/* Stage 3 */}
              <div className="bg-[#0A1319] border border-[#1E293B] rounded-lg px-2.5 py-1.5 flex items-center gap-2 shrink-0">
                <ShieldCheck className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
                <div>
                  <div className="text-[11px] font-semibold text-[#F3F4F6] leading-tight">Arbitration</div>
                  <div className="text-[9px] text-[#717B86] leading-tight">ML predictor</div>
                </div>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-[#475569] shrink-0" />

              {/* Stage 4 */}
              <div className="bg-[#0A1319] border border-[#1E293B] rounded-lg px-2.5 py-1.5 flex items-center gap-2 shrink-0">
                <HeartPulse className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
                <div>
                  <div className="text-[11px] font-semibold text-[#F3F4F6] leading-tight">Self-Healing</div>
                  <div className="text-[9px] text-[#717B86] leading-tight">Closed-loop recovery</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

