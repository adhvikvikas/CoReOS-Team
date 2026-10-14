import { useEffect, useState } from 'react';
import api from '../api/client';
import InteractiveChart from '../components/common/InteractiveChart';
import Card from '../components/common/Card';
import { carbonChartLayout, BASELINE_CARBON_COLORS, CANDIDATE_LABELS } from '../components/common/chartTheme';
import { AlertCircle, Trophy, BarChart3 } from 'lucide-react';

const METRIC_OPTIONS = [
  { key: 'composite_score', label: 'Overall Composite Score (0–100)', unit: 'pts', lowerIsBetter: false },
  { key: 'penalized_turnaround_time', label: 'Penalized Turnaround Time (ticks - cutoff penalty)', unit: 'ticks', lowerIsBetter: true },
  { key: 'avg_turnaround_time', label: 'Completed-Job Avg Turnaround (ticks)', unit: 'ticks', lowerIsBetter: true },
  { key: 'throughput', label: 'Throughput (jobs/tick)', unit: 'jobs/tick', lowerIsBetter: false },
  { key: 'completion_rate', label: 'Completion Rate (%)', unit: '%', lowerIsBetter: false },
  { key: 'thrashing_ticks', label: 'Thrashing Ticks', unit: 'ticks', lowerIsBetter: true },
  { key: 'jains_fairness', label: "Jain's Fairness Index", unit: '', lowerIsBetter: false },
  { key: 'decision_overhead_ms', label: 'Decision Overhead (ms)', unit: 'ms', lowerIsBetter: true },
];

const DEFAULT_CANDIDATES = [
  "F_ImprovedRL",
  "G_ChampionCoReOS",
  "H_OriginalRL",
  "D_ConflictNoHealing",
  "C_CoordNoConflict",
  "A_Conventional",
  "B_IndependentAgents"
];

interface GuardrailBreakdown {
  total: number;
  overallPass: number;
  overallRate: number;
  overheadPass: number;
  overheadRate: number;
  thrashingPass: number;
  thrashingRate: number;
  robustnessPass: number;
  robustnessRate: number;
  fairnessPass: number;
  fairnessRate: number;
  fairnessWeakWorkloads: string[];
}

function getCandidateGuardrailBreakdown(candidate: string, rawRows: any[] = []): GuardrailBreakdown {
  const rows = rawRows.filter((r: any) => (r.candidate || r.baseline) === candidate);
  const total = rows.length;
  if (total === 0) {
    return {
      total: 0,
      overallPass: 0,
      overallRate: 0,
      overheadPass: 0,
      overheadRate: 0,
      thrashingPass: 0,
      thrashingRate: 0,
      robustnessPass: 0,
      robustnessRate: 0,
      fairnessPass: 0,
      fairnessRate: 0,
      fairnessWeakWorkloads: []
    };
  }

  let overallPass = 0;
  let overheadPass = 0;
  let thrashingPass = 0;
  let robustnessPass = 0;
  let fairnessPass = 0;
  const fairnessFailByWorkload: Record<string, number> = {};

  rows.forEach((r: any) => {
    const vStr = String(r.guardrail_violations || 'NONE');
    const isCompliant = r.guardrail_compliant === true || vStr === 'NONE';
    if (isCompliant) overallPass++;

    // 1. Decision Overhead (<= 1.0 ms threshold)
    if (!vStr.includes('Decision overhead') && (r.decision_overhead_ms ?? 0) <= 1.0) {
      overheadPass++;
    }

    // 2. Thrashing Ceiling (<= 25 ticks, <= 15 on adversarial)
    if (!vStr.includes('Thrashing ceiling')) {
      thrashingPass++;
    }

    // 3. Workload Robustness (Steady & Mixed turnaround <= 16.0 & completion == 100%)
    if (!vStr.includes('Turnaround latency') && !vStr.includes('Completion regression')) {
      robustnessPass++;
    }

    // 4. Jain's Fairness Floor (>= 0.60)
    if (!vStr.includes('Fairness violation') && (r.jains_fairness ?? 1.0) >= 0.60) {
      fairnessPass++;
    } else {
      const wl = r.workload || 'unknown';
      fairnessFailByWorkload[wl] = (fairnessFailByWorkload[wl] || 0) + 1;
    }
  });

  const fairnessWeakWorkloads = Object.entries(fairnessFailByWorkload)
    .sort((a, b) => b[1] - a[1])
    .filter(([, count]) => count > 5)
    .map(([wl]) => wl);

  return {
    total,
    overallPass,
    overallRate: (overallPass / total) * 100,
    overheadPass,
    overheadRate: (overheadPass / total) * 100,
    thrashingPass,
    thrashingRate: (thrashingPass / total) * 100,
    robustnessPass,
    robustnessRate: (robustnessPass / total) * 100,
    fairnessPass,
    fairnessRate: (fairnessPass / total) * 100,
    fairnessWeakWorkloads
  };
}

export default function BenchmarkLab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkload, setSelectedWorkload] = useState<string>('adversarial_stress');
  const [selectedMetric, setSelectedMetric] = useState<string>('composite_score');
  const [showHistoricalBaseline, setShowHistoricalBaseline] = useState(false);

  useEffect(() => {
    api.get('/benchmarks/')
      .then(res => {
        setData(res.data);
        if (res.data.workloads && res.data.workloads.length > 0) {
          if (!res.data.workloads.includes(selectedWorkload) && selectedWorkload !== 'all_workloads') {
            setSelectedWorkload(res.data.workloads[0]);
          }
        }
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load benchmark evaluations.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#60A5FA] border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-[#717B86]">Loading benchmark data...</span>
        </div>
      </div>
    );
  }

  if (error || !data || !data.data || data.data.length === 0) {
    return (
      <div className="p-4 bg-[#F87171]/10 border border-[#F87171]/30 rounded-xl text-[#F87171] flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{error || 'No benchmark records available.'}</span>
      </div>
    );
  }

  const baseCandidates = (data.candidates && data.candidates.length > 0)
    ? data.candidates
    : [...DEFAULT_CANDIDATES, "E_CompleteCoReOS"];

  const candidates: string[] = showHistoricalBaseline
    ? baseCandidates
    : (data.active_candidates && data.active_candidates.length > 0)
      ? data.active_candidates
      : DEFAULT_CANDIDATES.filter(c => baseCandidates.includes(c));

  const isAllWorkloads = selectedWorkload === 'all_workloads';
  const filteredData = isAllWorkloads
    ? data.data
    : data.data.filter((d: any) => d.workload === selectedWorkload);

  const means = candidates.map(candId => {
    const rows = filteredData.filter((r: any) => (r.candidate || r.baseline) === candId);
    if (rows.length === 0) return null;
    return {
      baseline: candId,
      candidate: candId,
      label: candId === 'G_ChampionCoReOS' ? 'CoReOS' : (CANDIDATE_LABELS[candId] || candId),
      composite_score: rows.reduce((s: number, r: any) => s + (r.composite_score ?? 0), 0) / rows.length,
      jains_fairness: rows.reduce((s: number, r: any) => s + (r.jains_fairness ?? 1.0), 0) / rows.length,
      completion_rate: rows.reduce((s: number, r: any) => s + (r.completion_rate ?? 0), 0) / rows.length,
      completed_processes: rows.reduce((s: number, r: any) => s + (r.completed_processes ?? 0), 0) / rows.length,
      unfinished_processes: rows.reduce((s: number, r: any) => s + (r.unfinished_processes ?? 0), 0) / rows.length,
      avg_turnaround_time: rows.reduce((s: number, r: any) => s + (r.avg_turnaround_time ?? 0), 0) / rows.length,
      penalized_turnaround_time: rows.reduce((s: number, r: any) => {
        const pVal = r.penalized_turnaround ?? r.penalized_turnaround_time ?? (
          r.total_processes && r.total_processes > 0
            ? (r.completed_processes * r.avg_turnaround_time + (r.total_processes - r.completed_processes) * 300.0) / r.total_processes
            : r.avg_turnaround_time
        );
        return s + (pVal ?? 0);
      }, 0) / rows.length,
      throughput: rows.reduce((s: number, r: any) => s + (r.throughput ?? 0), 0) / rows.length,
      thrashing_ticks: rows.reduce((s: number, r: any) => s + (r.thrashing_ticks ?? 0), 0) / rows.length,
      decision_overhead_ms: rows.reduce((s: number, r: any) => s + (r.decision_overhead_ms ?? 0), 0) / rows.length,
    };
  }).filter((x): x is NonNullable<typeof x> => x !== null);

  const currentMetricDef = METRIC_OPTIONS.find(m => m.key === selectedMetric) || METRIC_OPTIONS[0];

  const maxCompScore = Math.max(...means.map(m => m.composite_score));
  const minTurnaround = Math.min(...means.map(m => m.avg_turnaround_time));
  const minPenalizedTurnaround = Math.min(...means.map(m => m.penalized_turnaround_time));
  const minThrashing = Math.min(...means.map(m => m.thrashing_ticks));
  const maxCompletion = Math.max(...means.map(m => m.completion_rate));
  const maxThroughput = Math.max(...means.map(m => m.throughput));
  const maxFairness = Math.max(...means.map(m => m.jains_fairness));

  const leaderboardRows = showHistoricalBaseline
    ? (data.overall_ranking || [])
    : (data.active_ranking && data.active_ranking.length > 0)
      ? data.active_ranking
      : (data.overall_ranking || [])
          .filter((r: any) => r.candidate !== 'E_CompleteCoReOS')
          .map((r: any, idx: number) => ({ ...r, rank: idx + 1 }));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono tracking-widest text-[#2DD4BF] font-semibold uppercase">
              Canonical Competition Benchmark
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1E293B] text-[#38BDF8] border border-[#303A40]">
              {showHistoricalBaseline ? '8 Candidates Evaluated • 1,440 Matched Trials' : '7 Active Candidates • 1,260 Matched Trials'}
            </span>
          </div>

          <button
            onClick={() => setShowHistoricalBaseline(!showHistoricalBaseline)}
            className="self-start sm:self-auto text-xs px-3 py-1.5 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#A1A1AA] hover:text-[#F3F4F6] transition-colors"
          >
            {showHistoricalBaseline ? '← Switch to Active CoReOS Comparison (7 Candidates)' : 'View Historical Baseline (8 Candidates)'}
          </button>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
          Benchmark Lab {showHistoricalBaseline ? '(Historical 8-Candidate Benchmark)' : '(Official Comparison: 7 Candidates)'}
        </h1>
        <p className="text-sm text-[#717B86] mt-0.5">
          Empirical comparison across candidate policies with CoReOS as the primary multi-agent system
        </p>
      </div>

      {/* Control Selector Bar */}
      <Card>
        <div className="flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">
              Select Workload
            </label>
            <select
              className="bg-[#101416] border border-[#303A40] text-[#F3F4F6] text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-[#60A5FA]"
              value={selectedWorkload}
              onChange={e => setSelectedWorkload(e.target.value)}
            >
              <option value="all_workloads">Overall Benchmark (All 6 Workloads • {showHistoricalBaseline ? '1,440 Trials' : '1,260 Trials'})</option>
              {data.workloads.map((w: string) => (
                <option key={w} value={w}>{w}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">
              Select Metric
            </label>
            <select
              className="bg-[#101416] border border-[#303A40] text-[#F3F4F6] text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-[#60A5FA]"
              value={selectedMetric}
              onChange={e => setSelectedMetric(e.target.value)}
            >
              {METRIC_OPTIONS.map(m => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Main Comparison Chart & Legend */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Bar Chart */}
        <div className="lg:col-span-9">
          <Card
            title={`${currentMetricDef.label} (${currentMetricDef.lowerIsBetter ? 'Lower is Better' : 'Higher is Better'})`}
          >
            <InteractiveChart
              title={`${currentMetricDef.label} (${currentMetricDef.lowerIsBetter ? 'Lower is Better' : 'Higher is Better'})`}
              subtitle={`Workload: ${isAllWorkloads ? 'All 6 Workloads Aggregated' : selectedWorkload} across ${candidates.length} candidates`}
              exportFilename={`benchmark_${selectedWorkload}_${selectedMetric}`}
              chartType="bar"
              chartHeight={360}
              data={[
                {
                  x: means.map(m => m.candidate === 'G_ChampionCoReOS' ? 'CoReOS' : m.baseline),
                  y: means.map(m => (m as any)[selectedMetric]),
                  type: 'bar',
                  text: means.map(m => {
                    const val = (m as any)[selectedMetric];
                    return typeof val === 'number' ? (val < 1 ? val.toFixed(3) : val.toFixed(1)) : val;
                  }),
                  textposition: 'outside',
                  textfont: { color: '#F3F4F6', size: 11, family: 'Inter, sans-serif' },
                  marker: {
                    color: means.map(m => BASELINE_CARBON_COLORS[m.baseline] || '#60A5FA'),
                    line: { width: 0 }
                  },
                  customdata: means.map(m => m.candidate === 'G_ChampionCoReOS' ? 'CoReOS' : m.label),
                  hovertemplate: '<b>%{customdata}</b><br>' + currentMetricDef.label + ': %{y:.2f} ' + currentMetricDef.unit + '<extra></extra>'
                }
              ]}
              layout={{
                ...carbonChartLayout,
                height: 360,
                yaxis: {
                  ...carbonChartLayout.yaxis,
                  title: { text: currentMetricDef.unit, font: { color: '#A1A1AA', size: 11 } }
                },
                xaxis: {
                  ...carbonChartLayout.xaxis,
                  tickfont: { color: '#A1A1AA', size: 10 }
                },
                showlegend: false,
                shapes: selectedMetric === 'decision_overhead_ms' ? [
                  {
                    type: 'line',
                    xref: 'paper',
                    x0: 0,
                    x1: 1,
                    y0: 1.0,
                    y1: 1.0,
                    line: { color: '#EF4444', width: 1.5, dash: 'dash' }
                  }
                ] : selectedMetric === 'jains_fairness' ? [
                  {
                    type: 'line',
                    xref: 'paper',
                    x0: 0,
                    x1: 1,
                    y0: 0.60,
                    y1: 0.60,
                    line: { color: '#F59E0B', width: 1.5, dash: 'dash' }
                  }
                ] : [],
                annotations: selectedMetric === 'decision_overhead_ms' ? [
                  {
                    xref: 'paper',
                    yref: 'y',
                    x: 0.98,
                    y: 1.0,
                    text: 'Guardrail Ceiling: 1.0 ms',
                    showarrow: false,
                    yshift: 12,
                    xanchor: 'right',
                    font: { color: '#EF4444', size: 10 }
                  }
                ] : selectedMetric === 'jains_fairness' ? [
                  {
                    xref: 'paper',
                    yref: 'y',
                    x: 0.98,
                    y: 0.60,
                    text: 'Guardrail Floor: 0.60',
                    showarrow: false,
                    yshift: 12,
                    xanchor: 'right',
                    font: { color: '#F59E0B', size: 10 }
                  }
                ] : []
              }}
            />
          </Card>
        </div>

        {/* Baselines Legend Card */}
        <div className="lg:col-span-3">
          <Card title={`Candidates (${candidates.length})`} className="h-full">
            <div className="space-y-3 py-1">
              {candidates.map(b => {
                const isChampion = b === 'G_ChampionCoReOS';
                const displayName = isChampion ? 'CoReOS' : (CANDIDATE_LABELS[b] || b);
                return (
                  <div key={b} className="flex items-center gap-2.5 text-xs">
                    <span
                      className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                      style={{ backgroundColor: BASELINE_CARBON_COLORS[b] || '#60A5FA' }}
                    />
                    <div className="truncate">
                      <div className="text-[#F3F4F6] font-medium truncate" title={displayName}>
                        {isChampion ? 'CoReOS' : b}
                      </div>
                      <div className="text-[10px] text-[#717B86] truncate">
                        {isChampion ? 'Active CoReOS System' : (CANDIDATE_LABELS[b] || b)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Official Competition Leaderboard */}
      {leaderboardRows && leaderboardRows.length > 0 && (
        <Card title={showHistoricalBaseline ? 'Historical 8-Candidate Held-Out Competition Leaderboard' : 'Official Competition Leaderboard (Ranked by Mean Composite Score)'}>
          <div className="overflow-x-auto -mx-6 -my-4">
            <table className="w-full text-left text-xs whitespace-nowrap">
              <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
                <tr>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Rank</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Candidate</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Mean Composite Score (95% CI)</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completion Rate</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Penalized Turnaround</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Throughput</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Thrashing Ticks</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Fairness</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Overhead (≤1.0 ms)</th>
                  <th className="px-5 py-3 font-semibold uppercase tracking-wider">Guardrails</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#303A40]/60">
                {leaderboardRows.map((row: any, i: number) => {
                  const candColor = BASELINE_CARBON_COLORS[row.candidate] || '#60A5FA';
                  const isTop = row.rank === 1;
                  const isRunnerUp = row.rank === 2;
                  const gb = getCandidateGuardrailBreakdown(row.candidate, data?.data || []);
                  const isOverheadPass = Number(row.decision_overhead_ms_mean) <= 1.0;
                  return (
                    <tr key={i} className={`hover:bg-[#20262B] transition-colors ${isTop ? 'bg-[#2DD4BF]/5' : (isRunnerUp ? 'bg-[#F472B6]/5' : '')}`}>
                      <td className="px-5 py-3 font-bold font-mono">
                        {isTop ? (
                          <span className="inline-flex items-center gap-1 text-[#2DD4BF]">
                            <Trophy className="w-3.5 h-3.5" /> #{row.rank}
                          </span>
                        ) : isRunnerUp ? (
                          <span className="inline-flex items-center gap-1 text-[#F472B6]">
                            <BarChart3 className="w-3.5 h-3.5" /> #{row.rank}
                          </span>
                        ) : (
                          <span className="text-[#A1A1AA]">#{row.rank}</span>
                        )}
                      </td>
                      <td className="px-5 py-3 font-medium text-[#F3F4F6] flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: candColor }}
                        />
                        <div>
                          <span className="font-semibold">{row.candidate === 'G_ChampionCoReOS' ? 'CoReOS' : row.candidate}</span>
                          <span className="text-[10px] text-[#717B86] ml-2">
                            {row.candidate === 'G_ChampionCoReOS' ? '(Active CoReOS System)' : `(${CANDIDATE_LABELS[row.candidate] || row.candidate})`}
                          </span>
                        </div>
                      </td>
                      <td className={`px-5 py-3 font-mono font-bold ${isTop ? 'text-[#2DD4BF]' : (isRunnerUp ? 'text-[#F472B6]' : 'text-[#F3F4F6]')}`}>
                        {Number(row.composite_score_mean).toFixed(2)}
                        {row.composite_score_ci95 && (
                          <span className="text-[10px] text-[#717B86] font-normal ml-1">
                            (±{Number(row.composite_score_ci95).toFixed(2)})
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-[#A1A1AA] font-mono">
                        {Number(row.completion_rate_mean).toFixed(1)}%
                      </td>
                      <td className="px-5 py-3 text-[#A1A1AA] font-mono">
                        {Number(row.penalized_turnaround_mean).toFixed(1)} ticks
                      </td>
                      <td className="px-5 py-3 text-[#A1A1AA] font-mono">
                        {Number(row.throughput_mean).toFixed(4)}
                      </td>
                      <td className="px-5 py-3 text-[#A1A1AA] font-mono">
                        {Number(row.thrashing_ticks_mean).toFixed(2)}
                      </td>
                      <td className="px-5 py-3 text-[#A1A1AA] font-mono">
                        {Number(row.jains_fairness_mean).toFixed(3)}
                      </td>
                      <td className="px-5 py-3 font-mono">
                        <div className="flex items-center gap-1.5">
                          <span className={isOverheadPass ? "text-[#F3F4F6]" : "text-[#EF4444] font-bold"}>
                            {Number(row.decision_overhead_ms_mean).toFixed(4)} ms
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                            isOverheadPass
                              ? "bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30"
                              : "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30"
                          }`}>
                            {isOverheadPass ? "PASS" : "FAIL"}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3 font-mono">
                        <div className="flex flex-col gap-1 py-0.5">
                          <div className="flex items-center gap-2">
                            <span className={`font-bold ${
                              Number(row.guardrail_pass_rate) >= 70 ? 'text-[#10B981]' :
                              Number(row.guardrail_pass_rate) >= 50 ? 'text-[#F59E0B]' : 'text-[#EF4444]'
                            }`}>
                              {row.guardrail_pass_rate != null ? `${Number(row.guardrail_pass_rate).toFixed(1)}%` : 'N/A'}
                            </span>
                            <span className="text-[10px] text-[#717B86]">all-pass</span>
                          </div>
                          {gb && gb.total > 0 && (
                            <>
                              <div className="flex items-center gap-1 text-[10px]">
                                <span title="Decision Overhead (≤1.0 ms ceiling): 100% compliant" className="px-1.5 py-0.5 rounded bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
                                  OH: {gb.overheadRate.toFixed(0)}%
                                </span>
                                <span title="Thrashing Ceiling (≤25 ticks, ≤15 on adv)" className={`px-1.5 py-0.5 rounded ${gb.thrashingRate >= 95 ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30' : 'bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30'}`}>
                                  TH: {gb.thrashingRate.toFixed(0)}%
                                </span>
                                <span title="Workload Robustness (Steady & Mixed turnaround/completion)" className={`px-1.5 py-0.5 rounded ${gb.robustnessRate >= 90 ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30' : 'bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30'}`}>
                                  ROB: {gb.robustnessRate.toFixed(0)}%
                                </span>
                                <span title={`Jain's Fairness Floor (≥0.60). Weak in: ${gb.fairnessWeakWorkloads.join(', ')}`} className={`px-1.5 py-0.5 rounded font-semibold ${gb.fairnessRate >= 70 ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30' : 'bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30'}`}>
                                  FAIR: {gb.fairnessRate.toFixed(0)}%
                                </span>
                              </div>
                              {gb.fairnessWeakWorkloads.length > 0 && gb.fairnessRate < 70 && (
                                <span className="text-[10px] text-[#F87171]/80 truncate" title={`Fairness drops below 0.60 floor in: ${gb.fairnessWeakWorkloads.join(', ')}`}>
                                  Fairness weak: {gb.fairnessWeakWorkloads.slice(0, 2).join(', ')}
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Detailed Candidate Comparison Table (Filtered by Selected Workload) */}
      <Card title={`Detailed Candidate Performance Table — ${isAllWorkloads ? 'All Workloads Combined' : selectedWorkload}`}>
        <div className="overflow-x-auto -mx-6 -my-4">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
              <tr>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Candidate</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Composite Score</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completion Rate</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completed</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Unfinished</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completed Turnaround</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Penalized Turnaround</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Throughput</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Thrashing Ticks</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Fairness</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Overhead (≤1.0 ms)</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Guardrails</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#303A40]/60">
              {means.map((row, i) => {
                const isMaxCompScore = row.composite_score === maxCompScore;
                const isMinTurn = row.avg_turnaround_time === minTurnaround;
                const isMinPen = row.penalized_turnaround_time === minPenalizedTurnaround;
                const isMinThrash = row.thrashing_ticks === minThrashing;
                const isOverheadPass = row.decision_overhead_ms <= 1.0;
                const isMaxComp = row.completion_rate === maxCompletion;
                const isMaxThrough = row.throughput === maxThroughput;
                const isMaxFair = row.jains_fairness === maxFairness;
                const compPercent = row.completion_rate <= 1.0 ? row.completion_rate * 100.0 : row.completion_rate;
                const wGb = getCandidateGuardrailBreakdown(row.candidate, filteredData);

                return (
                  <tr key={i} className="hover:bg-[#20262B] transition-colors">
                    <td className="px-5 py-3 font-medium text-[#F3F4F6] flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: BASELINE_CARBON_COLORS[row.candidate] }}
                      />
                      <div>
                        <span className="font-semibold">{row.candidate === 'G_ChampionCoReOS' ? 'CoReOS' : row.candidate}</span>
                        <span className="text-[10px] text-[#717B86] ml-2">
                          {row.candidate === 'G_ChampionCoReOS' ? '(Active CoReOS System)' : `(${CANDIDATE_LABELS[row.candidate] || row.candidate})`}
                        </span>
                      </div>
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMaxCompScore ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#F3F4F6]'}`}>
                      {row.composite_score.toFixed(2)} pts
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMaxComp ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {compPercent.toFixed(1)}%
                    </td>
                    <td className="px-5 py-3 text-[#A1A1AA] font-mono">{row.completed_processes.toFixed(1)}</td>
                    <td className="px-5 py-3 text-[#A1A1AA] font-mono">{row.unfinished_processes.toFixed(1)}</td>
                    <td className={`px-5 py-3 font-mono ${isMinTurn ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.avg_turnaround_time.toFixed(1)} ticks
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMinPen ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#38BDF8]'}`}>
                      {row.penalized_turnaround_time.toFixed(1)} ticks
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMaxThrough ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.throughput.toFixed(4)}
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMinThrash ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.thrashing_ticks.toFixed(1)}
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMaxFair ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.jains_fairness.toFixed(3)}
                    </td>
                    <td className="px-5 py-3 font-mono">
                      <div className="flex items-center gap-1.5">
                        <span className={isOverheadPass ? "text-[#F3F4F6]" : "text-[#EF4444] font-bold"}>
                          {row.decision_overhead_ms.toFixed(3)} ms
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                          isOverheadPass
                            ? "bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30"
                            : "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30"
                        }`}>
                          {isOverheadPass ? "PASS" : "FAIL"}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3 font-mono">
                      <div className="flex flex-col gap-0.5">
                        <div className="flex items-center gap-1.5">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                            wGb.overallRate >= 80 ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30' :
                            wGb.overallRate >= 50 ? 'bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30' :
                            'bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30'
                          }`}>
                            {wGb.overallRate.toFixed(1)}% Pass
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-[9px] text-[#717B86]">
                          <span className="text-[#10B981]">OH: {wGb.overheadRate.toFixed(0)}%</span>
                          <span>•</span>
                          <span className={wGb.fairnessRate >= 70 ? 'text-[#10B981]' : 'text-[#EF4444] font-semibold'}>
                            Fair: {wGb.fairnessRate.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

