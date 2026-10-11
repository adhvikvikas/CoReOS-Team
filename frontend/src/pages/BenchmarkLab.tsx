import { useEffect, useState } from 'react';
import api from '../api/client';
import InteractiveChart from '../components/common/InteractiveChart';
import Card from '../components/common/Card';
import { carbonChartLayout, BASELINE_CARBON_COLORS } from '../components/common/chartTheme';
import { AlertCircle } from 'lucide-react';

const METRIC_OPTIONS = [
  { key: 'avg_turnaround_time', label: 'Average Turnaround Time (ticks)', unit: 'ticks', lowerIsBetter: true },
  { key: 'throughput', label: 'Throughput (jobs/tick)', unit: 'jobs/tick', lowerIsBetter: false },
  { key: 'completion_rate', label: 'Completion Rate (%)', unit: '%', lowerIsBetter: false },
  { key: 'thrashing_ticks', label: 'Thrashing Ticks', unit: 'ticks', lowerIsBetter: true },
  { key: 'decision_overhead_ms', label: 'Decision Overhead (ms)', unit: 'ms', lowerIsBetter: true },
];

export default function BenchmarkLab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkload, setSelectedWorkload] = useState<string>('adversarial_stress');
  const [selectedMetric, setSelectedMetric] = useState<string>('avg_turnaround_time');

  useEffect(() => {
    api.get('/benchmarks/')
      .then(res => {
        setData(res.data);
        if (res.data.workloads && res.data.workloads.length > 0) {
          if (!res.data.workloads.includes(selectedWorkload)) {
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

  if (error || !data) {
    return (
      <div className="p-4 bg-[#F87171]/10 border border-[#F87171]/30 rounded-xl text-[#F87171] flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{error || 'No benchmark records available.'}</span>
      </div>
    );
  }

  const filteredData = data.data.filter((d: any) => d.workload === selectedWorkload);
  
  const baselines = [
    "A_Conventional",
    "B_IndependentAgents",
    "C_CoordNoConflict",
    "D_ConflictNoHealing",
    "E_CompleteCoReOS",
    "F_LearningRL"
  ];

  const means = baselines.map(b => {
    const rows = filteredData.filter((r: any) => r.baseline === b);
    if (rows.length === 0) return null;
    return {
      baseline: b,
      completion_rate: rows.reduce((s: number, r: any) => s + (r.completion_rate ?? 0), 0) / rows.length,
      completed_processes: rows.reduce((s: number, r: any) => s + (r.completed_processes ?? 0), 0) / rows.length,
      unfinished_processes: rows.reduce((s: number, r: any) => s + (r.unfinished_processes ?? 0), 0) / rows.length,
      avg_turnaround_time: rows.reduce((s: number, r: any) => s + (r.avg_turnaround_time ?? 0), 0) / rows.length,
      throughput: rows.reduce((s: number, r: any) => s + (r.throughput ?? 0), 0) / rows.length,
      thrashing_ticks: rows.reduce((s: number, r: any) => s + (r.thrashing_ticks ?? 0), 0) / rows.length,
      decision_overhead_ms: rows.reduce((s: number, r: any) => s + (r.decision_overhead_ms ?? 0), 0) / rows.length,
    };
  }).filter((x): x is NonNullable<typeof x> => x !== null);

  const currentMetricDef = METRIC_OPTIONS.find(m => m.key === selectedMetric) || METRIC_OPTIONS[0];

  const minTurnaround = Math.min(...means.map(m => m.avg_turnaround_time));
  const minThrashing = Math.min(...means.map(m => m.thrashing_ticks));
  const minOverhead = Math.min(...means.map(m => m.decision_overhead_ms));
  const maxCompletion = Math.max(...means.map(m => m.completion_rate));
  const maxThroughput = Math.max(...means.map(m => m.throughput));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
          Benchmark Lab (Baselines A–F)
        </h1>
        <p className="text-sm text-[#717B86] mt-0.5">
          Compare the architectural variants across simulated workloads
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
              subtitle={`Workload: ${selectedWorkload} across architectural variants A–F`}
              exportFilename={`benchmark_${selectedWorkload}_${selectedMetric}`}
              chartType="bar"
              chartHeight={340}
              data={[
                {
                  x: means.map(m => m.baseline),
                  y: means.map(m => (m as any)[selectedMetric]),
                  type: 'bar',
                  text: means.map(m => {
                    const val = (m as any)[selectedMetric];
                    return typeof val === 'number' ? (val < 1 ? val.toFixed(3) : val.toFixed(1)) : val;
                  }),
                  textposition: 'outside',
                  textfont: { color: '#F3F4F6', size: 12, family: 'Inter, sans-serif' },
                  marker: {
                    color: means.map(m => BASELINE_CARBON_COLORS[m.baseline] || '#60A5FA'),
                    line: { width: 0 }
                  }
                }
              ]}
              layout={{
                ...carbonChartLayout,
                height: 340,
                yaxis: {
                  ...carbonChartLayout.yaxis,
                  title: { text: currentMetricDef.unit, font: { color: '#A1A1AA', size: 11 } }
                },
                xaxis: {
                  ...carbonChartLayout.xaxis,
                  tickfont: { color: '#A1A1AA', size: 11 }
                },
                showlegend: false
              }}
            />
          </Card>
        </div>

        {/* Baselines Legend Card */}
        <div className="lg:col-span-3">
          <Card title="Baselines" className="h-full">
            <div className="space-y-3 py-1">
              {baselines.map(b => (
                <div key={b} className="flex items-center gap-2.5 text-xs">
                  <span
                    className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                    style={{ backgroundColor: BASELINE_CARBON_COLORS[b] || '#60A5FA' }}
                  />
                  <span className="text-[#F3F4F6] font-medium truncate" title={b}>
                    {b}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Benchmark Comparison Table */}
      <Card title={`Detailed Baseline Comparison — ${selectedWorkload}`}>
        <div className="overflow-x-auto -mx-6 -my-4">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
              <tr>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Baseline</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completion Rate</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completed</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Unfinished</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Avg Turnaround</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Throughput</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Thrashing Ticks</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Overhead (ms)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#303A40]/60">
              {means.map((row, i) => {
                const isMinTurn = row.avg_turnaround_time === minTurnaround;
                const isMinThrash = row.thrashing_ticks === minThrashing;
                const isMinOverhead = row.decision_overhead_ms === minOverhead;
                const isMaxComp = row.completion_rate === maxCompletion;
                const isMaxThrough = row.throughput === maxThroughput;

                return (
                  <tr key={i} className="hover:bg-[#20262B] transition-colors">
                    <td className="px-5 py-3 font-medium text-[#F3F4F6] flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: BASELINE_CARBON_COLORS[row.baseline] }}
                      />
                      <span>{row.baseline}</span>
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMaxComp ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {(row.completion_rate * 100).toFixed(1)}%
                    </td>
                    <td className="px-5 py-3 text-[#A1A1AA] font-mono">{row.completed_processes.toFixed(1)}</td>
                    <td className="px-5 py-3 text-[#A1A1AA] font-mono">{row.unfinished_processes.toFixed(1)}</td>
                    <td className={`px-5 py-3 font-mono ${isMinTurn ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.avg_turnaround_time.toFixed(1)} ticks
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMaxThrough ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.throughput.toFixed(4)}
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMinThrash ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.thrashing_ticks.toFixed(1)}
                    </td>
                    <td className={`px-5 py-3 font-mono ${isMinOverhead ? 'text-[#34D399] font-bold bg-[#34D399]/5' : 'text-[#A1A1AA]'}`}>
                      {row.decision_overhead_ms.toFixed(3)}
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
