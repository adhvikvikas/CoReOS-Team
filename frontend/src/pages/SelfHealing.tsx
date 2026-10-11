import { useEffect, useState } from 'react';
import api from '../api/client';
import InteractiveChart from '../components/common/InteractiveChart';
import Card from '../components/common/Card';
import MetricCard from '../components/common/MetricCard';
import { carbonChartLayout } from '../components/common/chartTheme';
import { ShieldCheck, CheckCircle2, Clock, GitFork, AlertCircle, RotateCcw, Cpu } from 'lucide-react';

export default function SelfHealing() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealing = (isManual = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);
    setError(null);

    api.get('/healing/')
      .then(res => setData(res.data))
      .catch(err => {
        console.error(err);
        setError('Failed to fetch self-healing telemetry.');
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    fetchHealing();

    const onSimDone = () => {
      fetchHealing(true);
    };
    window.addEventListener('coreos:simulationCompleted', onSimDone);
    return () => {
      window.removeEventListener('coreos:simulationCompleted', onSimDone);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#60A5FA] border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-[#717B86]">Loading self-healing metrics...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 bg-[#F87171]/10 border border-[#F87171]/30 rounded-xl text-[#F87171] flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{error || 'No self-healing data available.'}</span>
      </div>
    );
  }

  const healingActions = data.healing_actions ?? data.total_recoveries ?? 0;
  const hasActions = healingActions > 0 && Array.isArray(data.strategy_usage) && data.strategy_usage.length > 0;
  const recentList = Array.isArray(data.recent_actions) ? data.recent_actions : [];

  return (
    <div className="space-y-6">
      {/* Page Header with Workload Context & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
              Self-Healing Center
            </h1>
            {data.workload_info && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#101416] text-[#34D399] border border-[#303A40]">
                <Cpu className="w-3.5 h-3.5 text-[#34D399]" />
                <span>{data.workload_info.workload_type} ({data.workload_info.num_processes} procs, seed {data.workload_info.seed})</span>
              </span>
            )}
          </div>
          <p className="text-sm text-[#717B86] mt-0.5">
            Monitor and evaluate self-healing mechanisms
          </p>
        </div>

        <button
          onClick={() => fetchHealing(true)}
          disabled={refreshing}
          className="self-start sm:self-auto flex items-center gap-2 px-3 py-1.5 bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#F3F4F6] text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-[#34D399] ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Telemetry'}</span>
        </button>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Healing Actions"
          value={healingActions}
          subtitle="Autonomous corrections"
          icon={ShieldCheck}
          iconColor="text-[#60A5FA]"
        />
        <MetricCard
          title="Success Rate"
          value={`${Number(data.success_rate ?? 0).toFixed(1)}%`}
          subtitle="Stabilized throughput"
          icon={CheckCircle2}
          iconColor="text-[#34D399]"
        />
        <MetricCard
          title="Avg Healing Time"
          value={data.avg_healing_time ?? '0.00 ticks'}
          subtitle="Latency per recovery"
          icon={Clock}
          iconColor="text-[#FBBF24]"
        />
        <MetricCard
          title="Active Strategies"
          value={data.active_strategies ?? 0}
          subtitle="Heuristic recovery rules"
          icon={GitFork}
          iconColor="text-[#34D3E9]"
        />
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Strategy Usage Donut */}
        <div className="lg:col-span-5">
          <Card title="Self-Healing Strategy Usage" className="h-full">
            {hasActions ? (
              <div className="relative">
                <InteractiveChart
                  title="Self-Healing Strategy Usage"
                  subtitle="Proportion of applied heuristic recovery strategies"
                  exportFilename="self_healing_strategy_usage"
                  chartType="pie"
                  chartHeight={240}
                  data={[
                    {
                      values: data.strategy_usage.map((s: any) => s.percentage),
                      labels: data.strategy_usage.map((s: any) => s.strategy),
                      type: 'pie',
                      hole: 0.65,
                      textinfo: 'none',
                      hoverinfo: 'label+percent+value',
                      marker: {
                        colors: data.strategy_usage.map((s: any) => s.color)
                      }
                    }
                  ]}
                  layout={{
                    ...carbonChartLayout,
                    height: 240,
                    margin: { l: 20, r: 20, t: 10, b: 10 },
                    showlegend: false,
                    annotations: [
                      {
                        font: { size: 22, color: '#F3F4F6', family: 'Inter, sans-serif' },
                        showarrow: false,
                        text: `<b>${healingActions}</b>`,
                        x: 0.5,
                        y: 0.54
                      },
                      {
                        font: { size: 11, color: '#717B86', family: 'Inter, sans-serif' },
                        showarrow: false,
                        text: 'Actions',
                        x: 0.5,
                        y: 0.42
                      }
                    ]
                  }}
                />

                {/* Legend List */}
                <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-[#303A40]/40 text-xs">
                  {data.strategy_usage.map((s: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between px-2 py-1 bg-[#101416]/50 rounded">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
                        <span className="text-[#A1A1AA] truncate">{s.strategy}</span>
                      </div>
                      <span className="font-semibold text-[#F3F4F6] ml-2">{s.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-center p-6 bg-[#101416]/30 rounded-lg">
                <CheckCircle2 className="w-10 h-10 text-[#34D399] mb-2" />
                <span className="text-sm font-semibold text-[#F3F4F6]">Zero Regressions Detected</span>
                <span className="text-xs text-[#717B86] mt-1 max-w-xs">
                  The active workload operated within nominal thresholds. No Pareto-optimal emergency overrides were required.
                </span>
              </div>
            )}
          </Card>
        </div>

        {/* Healing Success Rate Over Time */}
        <div className="lg:col-span-7">
          <Card title="Healing Success Rate Over Time" className="h-full">
            <InteractiveChart
              title="Healing Success Rate Over Time"
              subtitle="Resolution success percentage and failed attempts across execution ticks"
              exportFilename="healing_success_rate_over_time"
              chartType="cartesian"
              chartHeight={310}
              data={[
                {
                  x: data.trends.map((t: any) => t.time),
                  y: data.trends.map((t: any) => t.success_rate),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Success Rate',
                  line: { color: '#34D399', width: 2 }
                },
                {
                  x: data.trends.map((t: any) => t.time),
                  y: data.trends.map((t: any) => t.failed_attempts),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Failed Attempts',
                  line: { color: '#F87171', width: 2 }
                }
              ]}
              layout={{
                ...carbonChartLayout,
                height: 310,
                yaxis: {
                  ...carbonChartLayout.yaxis,
                  title: { text: 'Rate (%)', font: { color: '#A1A1AA', size: 11 } },
                  range: [0, 105]
                },
                xaxis: {
                  ...carbonChartLayout.xaxis,
                  title: { text: 'Execution Ticks', font: { color: '#A1A1AA', size: 11 } }
                },
                legend: {
                  orientation: 'h',
                  x: 0.6,
                  y: 1.15,
                  font: { color: '#A1A1AA', size: 11 }
                }
              }}
            />
          </Card>
        </div>
      </div>

      {/* Recent Self-Healing Actions Table */}
      <Card title={`Recent Self-Healing Actions (${recentList.length} recorded interventions)`}>
        <div className="overflow-x-auto -mx-6 -my-4">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
              <tr>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">ID</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Time</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Issue Detected</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Strategy</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Target</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Result</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Latency</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Linked Conflict(s)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#303A40]/60">
              {recentList.length > 0 ? (
                recentList.map((a: any, i: number) => {
                  const isSuccess = a.result === 'Success';
                  const linkedConflicts = Array.isArray(a.linked_conflicts) ? a.linked_conflicts : [];
                  return (
                    <tr key={i} className="hover:bg-[#20262B] transition-colors">
                      <td className="px-5 py-2.5 font-medium text-[#34D399] font-mono">{a.id || `HEAL-${String(i+1).padStart(3, '0')}`}</td>
                      <td className="px-5 py-2.5 font-medium text-[#F3F4F6] font-mono">{a.time} ticks</td>
                      <td className="px-5 py-2.5 text-[#F87171] font-medium">{a.issue}</td>
                      <td className="px-5 py-2.5 text-[#60A5FA]">{a.strategy}</td>
                      <td className="px-5 py-2.5 text-[#34D3E9]">{a.target}</td>
                      <td className="px-5 py-2.5">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[11px] font-medium border ${
                            isSuccess
                              ? 'bg-[#34D399]/10 text-[#34D399] border-[#34D399]/30'
                              : 'bg-[#F87171]/10 text-[#F87171] border-[#F87171]/30'
                          }`}
                        >
                          {a.result}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 text-[#A1A1AA] font-mono">{a.latency}</td>
                      <td className="px-5 py-2.5">
                        {linkedConflicts.length > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#60A5FA]/10 text-[#60A5FA] border border-[#60A5FA]/30">
                            {linkedConflicts.join(', ')}
                          </span>
                        ) : (
                          <span className="text-[#717B86] text-[11px]">Autonomous Safeguard</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-[#717B86]">
                    No recovery interventions triggered for this workload run.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* How Self-Healing Works */}
      <Card title="How Self-Healing Works & Subsystem Architecture">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs leading-relaxed text-[#A1A1AA]">
          <div className="p-3.5 bg-[#101416] rounded-lg border border-[#303A40]/60 space-y-2">
            <h4 className="text-sm font-semibold text-[#F3F4F6]">Performance Regression Detector</h4>
            <p>
              Even with predictive conflict arbitration, severe adversarial workloads can cause live-lock or thrashing collapse. The <code className="text-[#60A5FA]">PerformanceRegressionDetector</code> continuously evaluates system throughput over rolling windows.
            </p>
            <p>
              When throughput drops below nominal baselines while resource queues remain saturated, an emergency regression condition is flagged to trigger the recovery engine.
            </p>
          </div>
          <div className="p-3.5 bg-[#101416] rounded-lg border border-[#303A40]/60 space-y-2">
            <h4 className="text-sm font-semibold text-[#F3F4F6]">Pareto-Optimal Recovery Engine</h4>
            <p>
              The <code className="text-[#34D399]">RecoveryEngine</code> applies decisive overrides (such as freezing non-essential I/O or temporarily expanding the CPU quantum) to clear resource deadlocks and restore optimal scheduling flow.
            </p>
            <p>
              A mandatory cooling-off interval prevents policy flapping, ensuring system stability before returning full autonomous control to individual agents.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
