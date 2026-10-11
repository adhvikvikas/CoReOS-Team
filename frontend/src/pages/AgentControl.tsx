import { useEffect, useState } from 'react';
import api from '../api/client';
import InteractiveChart from '../components/common/InteractiveChart';
import Card from '../components/common/Card';
import { carbonChartLayout } from '../components/common/chartTheme';
import { CheckCircle2, XCircle, AlertCircle, RotateCcw } from 'lucide-react';

export default function AgentControl() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgentData = () => {
    setLoading(true);
    api.get('/agents/')
      .then(res => {
        setData(res.data);
        setError(null);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to fetch agent decision telemetry.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAgentData();

    const handleSimCompleted = () => {
      fetchAgentData();
    };
    window.addEventListener('coreos:simulationCompleted', handleSimCompleted);
    return () => {
      window.removeEventListener('coreos:simulationCompleted', handleSimCompleted);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#60A5FA] border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-[#717B86]">Loading agent telemetry...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 bg-[#F87171]/10 border border-[#F87171]/30 rounded-xl text-[#F87171] flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{error || 'No agent records found.'}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
              Agent Control Center
            </h1>
            {data?.workload_info?.workload_type && (
              <span className="px-2.5 py-0.5 rounded text-xs font-mono bg-[#1E293B] text-[#60A5FA] border border-[#303A40]">
                Active Workload: {data.workload_info.workload_type}
              </span>
            )}
          </div>
          <p className="text-sm text-[#717B86] mt-0.5">
            Audit trail of individual agent proposals and coordinator overrides
          </p>
        </div>
        <button
          onClick={fetchAgentData}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-[#A1A1AA] hover:text-[#F3F4F6] bg-[#1A1F23] hover:bg-[#22282F] border border-[#303A40] rounded-lg transition-colors shadow-sm"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Refresh Decisions
        </button>
      </div>

      {/* Proposed vs Coordinated Quantum Chart */}
      <Card title="Proposed vs Coordinated Quantum">
        <InteractiveChart
          title="Proposed vs Coordinated Quantum"
          subtitle="Agent proposals compared against coordinator arbitrated quantum"
          exportFilename="proposed_vs_coordinated_quantum"
          chartType="cartesian"
          chartHeight={280}
          data={[
            {
              x: data.records.map((r: any) => r.step),
              y: data.records.map((r: any) => r.cpu_proposed_quantum),
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Proposed Quantum',
              line: { color: '#C084FC', width: 2, dash: 'dot' },
              marker: { size: 5, color: '#C084FC' }
            },
            {
              x: data.records.map((r: any) => r.step),
              y: data.records.map((r: any) => r.coordinated_quantum),
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Coordinated Quantum',
              line: { color: '#34D399', width: 2.5 },
              marker: { size: 6, color: '#34D399' }
            }
          ]}
          layout={{
            ...carbonChartLayout,
            height: 280,
            yaxis: {
              ...carbonChartLayout.yaxis,
              title: { text: 'Quantum (ms)', font: { color: '#A1A1AA', size: 11 } },
              dtick: 1
            },
            xaxis: {
              ...carbonChartLayout.xaxis,
              title: { text: 'Coordination Step', font: { color: '#A1A1AA', size: 11 } }
            },
            legend: {
              orientation: 'h',
              x: 0.65,
              y: 1.15,
              font: { color: '#A1A1AA', size: 11 }
            }
          }}
        />
      </Card>

      {/* Decision Audit Log Table */}
      <Card title={`Decision Audit Log (${data?.workload_info?.workload_type ? data.workload_info.workload_type.replace(/_/g, ' ') : 'Active Simulation'})`}>
        <div className="overflow-x-auto -mx-6 -my-4">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
              <tr>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Step</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Time</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">CPU Proposed Q</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Coordinated Q</th>
                <th className="px-5 py-3 font-semibold tracking-wider">Mem Target (MB)</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">I/O Policy</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Conflict Type</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider text-center">Arbitration</th>
                <th className="px-5 py-3 font-semibold uppercase tracking-wider">Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#303A40]/60">
              {data.records.map((row: any, i: number) => {
                const isArbitrated = Boolean(row.arbitration_applied);
                const hasConflict = row.conflict_type && row.conflict_type !== 'None';
                return (
                  <tr key={i} className="hover:bg-[#20262B] transition-colors">
                    <td className="px-5 py-2.5 font-medium text-[#F3F4F6]">{row.step}</td>
                    <td className="px-5 py-2.5 text-[#A1A1AA]">{row.time}</td>
                    <td className="px-5 py-2.5 text-[#F3F4F6] font-mono">{Number(row.cpu_proposed_quantum).toFixed(1)}</td>
                    <td className="px-5 py-2.5 text-[#34D399] font-mono font-medium">{Number(row.coordinated_quantum).toFixed(1)}</td>
                    <td className="px-5 py-2.5 text-[#A1A1AA] font-mono">{row.mem_reclaim_target}</td>
                    <td className="px-5 py-2.5 text-[#A1A1AA]">{row.io_policy}</td>
                    <td className="px-5 py-2.5">
                      {hasConflict ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-[#34D3E9]/10 text-[#34D3E9] border border-[#34D3E9]/30">
                          {row.conflict_type}
                        </span>
                      ) : (
                        <span className="text-[#717B86]">None</span>
                      )}
                    </td>
                    <td className="px-5 py-2.5 text-center">
                      {isArbitrated ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#34D399]/10 text-[#34D399] border border-[#34D399]/30">
                          <CheckCircle2 className="w-3 h-3 text-[#34D399]" />
                          <span>Yes</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#F87171]/10 text-[#F87171] border border-[#F87171]/30">
                          <XCircle className="w-3 h-3 text-[#F87171]" />
                          <span>No</span>
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-2.5 text-[#A1A1AA] max-w-xs truncate" title={row.explanation || row.cpu_reason}>
                      {row.explanation || row.cpu_reason || 'Nominal execution'}
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
