import { useEffect, useState } from 'react';
import api from '../api/client';
import InteractiveChart from '../components/common/InteractiveChart';
import Card from '../components/common/Card';
import MetricCard from '../components/common/MetricCard';
import { carbonChartLayout } from '../components/common/chartTheme';
import { AlertTriangle, Percent, CheckCircle, Clock, AlertCircle, RotateCcw, Cpu } from 'lucide-react';

export default function ConflictAnalysis() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConflicts = (isManual = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);
    setError(null);

    api.get('/conflicts/')
      .then(res => setData(res.data))
      .catch(err => {
        console.error(err);
        setError('Failed to fetch conflict analytics.');
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    fetchConflicts();

    const onSimDone = () => {
      fetchConflicts(true);
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
          <span className="text-sm text-[#717B86]">Loading conflict diagnostics...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 bg-[#F87171]/10 border border-[#F87171]/30 rounded-xl text-[#F87171] flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{error || 'No conflict analytics available.'}</span>
      </div>
    );
  }

  const totalConflicts = data.total_conflicts ?? 0;
  const hasConflicts = totalConflicts > 0 && Array.isArray(data.distribution) && data.distribution.length > 0;
  const recentList = Array.isArray(data.recent_conflicts) ? data.recent_conflicts : [];

  return (
    <div className="space-y-6">
      {/* Page Header with Workload Context & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
              Conflict Analysis & Diagnostics
            </h1>
            {data.workload_info && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#101416] text-[#60A5FA] border border-[#303A40]">
                <Cpu className="w-3.5 h-3.5 text-[#60A5FA]" />
                <span>{data.workload_info.workload_type} ({data.workload_info.num_processes} procs, seed {data.workload_info.seed})</span>
              </span>
            )}
          </div>
          <p className="text-sm text-[#717B86] mt-0.5">
            Identify, visualize and analyze resource conflicts across agents
          </p>
        </div>

        <button
          onClick={() => fetchConflicts(true)}
          disabled={refreshing}
          className="self-start sm:self-auto flex items-center gap-2 px-3 py-1.5 bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#F3F4F6] text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-[#60A5FA] ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Telemetry'}</span>
        </button>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Conflicts"
          value={totalConflicts}
          subtitle="Identified across run"
          icon={AlertTriangle}
          iconColor="text-[#60A5FA]"
        />
        <MetricCard
          title="Conflict Rate"
          value={data.conflict_rate ?? '0.0%'}
          subtitle="Of total agent actions"
          icon={Percent}
          iconColor="text-[#FBBF24]"
        />
        <MetricCard
          title="Resolved by Self-Healing"
          value={data.resolved_by_healing ?? 0}
          subtitle="Mitigated autonomously"
          icon={CheckCircle}
          iconColor="text-[#34D399]"
        />
        <MetricCard
          title="Avg Resolution Time"
          value={data.avg_resolution_time ?? '0.00 ms'}
          subtitle="Arbitration latency"
          icon={Clock}
          iconColor="text-[#34D3E9]"
        />
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Conflict Type Distribution Donut Chart */}
        <div className="lg:col-span-5">
          <Card title="Conflict Type Distribution" className="h-full">
            {hasConflicts ? (
              <div className="relative">
                <InteractiveChart
                  title="Conflict Type Distribution"
                  subtitle="Proportion of detected cross-agent resource conflicts"
                  exportFilename="conflict_type_distribution"
                  chartType="pie"
                  chartHeight={240}
                  data={[
                    {
                      values: data.distribution.map((d: any) => d.percentage),
                      labels: data.distribution.map((d: any) => d.type),
                      type: 'pie',
                      hole: 0.65,
                      textinfo: 'none',
                      hoverinfo: 'label+percent+value',
                      marker: {
                        colors: data.distribution.map((d: any) => d.color)
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
                        text: `<b>${totalConflicts}</b>`,
                        x: 0.5,
                        y: 0.54
                      },
                      {
                        font: { size: 11, color: '#717B86', family: 'Inter, sans-serif' },
                        showarrow: false,
                        text: 'Conflicts',
                        x: 0.5,
                        y: 0.42
                      }
                    ]
                  }}
                />

                {/* Legend List */}
                <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-[#303A40]/40 text-xs">
                  {data.distribution.map((d: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between px-2 py-1 bg-[#101416]/50 rounded">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                        <span className="text-[#A1A1AA] truncate">{d.type}</span>
                      </div>
                      <span className="font-semibold text-[#F3F4F6] ml-2">{d.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-center p-6 bg-[#101416]/30 rounded-lg">
                <CheckCircle className="w-10 h-10 text-[#34D399] mb-2" />
                <span className="text-sm font-semibold text-[#F3F4F6]">Zero Conflicts Detected</span>
                <span className="text-xs text-[#717B86] mt-1 max-w-xs">
                  The active workload executed under nominal conditions without triggering cross-resource arbitration hazards.
                </span>
              </div>
            )}
          </Card>
        </div>

        {/* Conflict Trend Over Time */}
        <div className="lg:col-span-7">
          <Card title="Conflict Trend Over Time" className="h-full">
            <InteractiveChart
              title="Conflict Trend Over Time"
              subtitle="Detected conflict occurrences across execution window ticks"
              exportFilename="conflict_trend_over_time"
              chartType="cartesian"
              chartHeight={310}
              data={[
                {
                  x: data.trends.map((t: any) => t.time),
                  y: data.trends.map((t: any) => t.cpu_memory),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'CPU-Memory',
                  line: { color: '#60A5FA', width: 2 }
                },
                {
                  x: data.trends.map((t: any) => t.time),
                  y: data.trends.map((t: any) => t.memory_io),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Memory-I/O',
                  line: { color: '#34D3E9', width: 2 }
                },
                {
                  x: data.trends.map((t: any) => t.time),
                  y: data.trends.map((t: any) => t.cpu_queue),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Other Hazards',
                  line: { color: '#FBBF24', width: 2 }
                }
              ]}
              layout={{
                ...carbonChartLayout,
                height: 310,
                yaxis: {
                  ...carbonChartLayout.yaxis,
                  title: { text: 'Events / Window', font: { color: '#A1A1AA', size: 11 } }
                },
                xaxis: {
                  ...carbonChartLayout.xaxis,
                  title: { text: 'Execution Ticks', font: { color: '#A1A1AA', size: 11 } }
                },
                legend: {
                  orientation: 'h',
                  x: 0.5,
                  y: 1.15,
                  font: { color: '#A1A1AA', size: 11 }
                }
              }}
            />
          </Card>
        </div>
      </div>

      {/* Recent Conflicts Table */}
      <Card title={`Recent Conflicts (${recentList.length} recorded events)`}>
        <div className="overflow-x-auto -mx-6 -my-4">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
              <tr>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">ID</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Time</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Agents</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Type</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Resource</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Severity</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Status</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Resolution / Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#303A40]/60">
              {recentList.length > 0 ? (
                recentList.map((c: any, i: number) => {
                  const isHigh = c.severity === 'High';
                  const isMed = c.severity === 'Medium';
                  const isResolved = c.status === 'Resolved';
                  return (
                    <tr key={i} className="hover:bg-[#20262B] transition-colors">
                      <td className="px-5 py-2.5 font-medium text-[#60A5FA] font-mono">{c.id || `CONF-${String(i+1).padStart(3, '0')}`}</td>
                      <td className="px-5 py-2.5 font-medium text-[#F3F4F6] font-mono">{c.time} ticks</td>
                      <td className="px-5 py-2.5 text-[#34D3E9] font-medium">{c.agents}</td>
                      <td className="px-5 py-2.5 text-[#F3F4F6]">{c.type}</td>
                      <td className="px-5 py-2.5 text-[#A1A1AA]">{c.resource}</td>
                      <td className="px-5 py-2.5">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[11px] font-medium border ${
                            isHigh
                              ? 'bg-[#F87171]/10 text-[#F87171] border-[#F87171]/30'
                              : isMed
                              ? 'bg-[#FBBF24]/10 text-[#FBBF24] border-[#FBBF24]/30'
                              : 'bg-[#60A5FA]/10 text-[#60A5FA] border-[#60A5FA]/30'
                          }`}
                        >
                          {c.severity}
                        </span>
                      </td>
                      <td className="px-5 py-2.5">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[11px] font-medium border ${
                            isResolved
                              ? 'bg-[#34D399]/10 text-[#34D399] border-[#34D399]/30'
                              : 'bg-[#717B86]/10 text-[#A1A1AA] border-[#303A40]'
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="px-5 py-2.5">
                        {c.resolved_by_healing ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#34D3E9]/10 text-[#34D3E9] border border-[#34D3E9]/30">
                            Self-Healing {c.linked_healing_id ? `(${c.linked_healing_id})` : ''}
                          </span>
                        ) : c.resolved_by === 'Coordinator Arbitration' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#60A5FA]/10 text-[#60A5FA] border border-[#60A5FA]/30">
                            Coordinator Arbitration
                          </span>
                        ) : (
                          <span className="text-[#717B86] text-[11px]">Unarbitrated</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-[#717B86]">
                    No conflict events logged for this workload run.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Conflict Rule Taxonomy */}
      <Card title="Conflict Rule Taxonomy & Predictive Evaluation">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 p-3 bg-[#101416] rounded-lg border border-[#303A40]/60">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-[#717B86]">Precision</div>
            <div className="text-base font-bold text-[#F3F4F6]">{(data.metrics.precision * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-[#717B86]">Recall</div>
            <div className="text-base font-bold text-[#34D399]">{(data.metrics.recall * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-[#717B86]">F1 Score</div>
            <div className="text-base font-bold text-[#60A5FA]">{(data.metrics.f1 * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-[#717B86]">False Positive Rate</div>
            <div className="text-base font-bold text-[#F87171]">{(data.metrics.fpr * 100).toFixed(1)}%</div>
          </div>
        </div>

        <div className="overflow-x-auto -mx-6 -my-4">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
              <tr>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Conflict Type</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Interacting Subsystems</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Mechanism</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#303A40]/60">
              {data.taxonomy.map((row: any, i: number) => (
                <tr key={i} className="hover:bg-[#20262B] transition-colors">
                  <td className="px-5 py-3 font-semibold text-[#F87171]">{row["Conflict Type"]}</td>
                  <td className="px-5 py-3 font-medium text-[#34D3E9]">{row["Interacting Subsystems"]}</td>
                  <td className="px-5 py-3 text-[#A1A1AA] whitespace-normal max-w-xl">{row["Mechanism"]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
