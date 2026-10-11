import { useState, useEffect } from 'react';
import api from '../api/client';
import InteractiveChart from '../components/common/InteractiveChart';
import Card from '../components/common/Card';
import MetricCard from '../components/common/MetricCard';
import { carbonChartLayout } from '../components/common/chartTheme';
import { Play, RotateCcw, Cpu, Clock, Layers, Activity, AlertCircle } from 'lucide-react';

export default function SimulationLab() {
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [config, setConfig] = useState({
    workload_type: 'adversarial_stress',
    num_processes: 40,
    policy_mode: 'Complete CoReOS',
    seed: 42,
    sim_quantum: 4.0
  });

  const runSimulation = () => {
    setLoading(true);
    setError(null);
    api.post('/simulation/run', config)
      .then(response => {
        setRes(response.data);
        window.dispatchEvent(new CustomEvent('coreos:simulationCompleted', { 
          detail: { result: response.data, config } 
        }));
      })
      .catch(err => {
        console.error(err);
        setError('Simulation execution failed. Please verify engine parameters.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    api.get('/simulation/latest')
      .then(response => {
        if (!isMounted) return;
        if (response.data && response.data.result) {
          setRes(response.data.result);
          if (response.data.config) {
            setConfig({
              workload_type: response.data.config.workload_type || 'adversarial_stress',
              num_processes: response.data.config.num_processes || 40,
              policy_mode: response.data.config.policy_mode || 'Complete CoReOS',
              seed: response.data.config.seed ?? 42,
              sim_quantum: response.data.config.sim_quantum || 4.0
            });
          }
        } else {
          runSimulation();
        }
      })
      .catch(err => {
        if (!isMounted) return;
        console.error('Failed to load latest simulation state:', err);
        runSimulation();
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
              Simulation Lab & System Monitor
            </h1>
            {config.workload_type && (
              <span className="px-2.5 py-0.5 rounded text-xs font-mono bg-[#1E293B] text-[#60A5FA] border border-[#303A40]">
                Active Workload: {config.workload_type}
              </span>
            )}
          </div>
          <p className="text-sm text-[#717B86] mt-0.5">
            Run the multi-agent operating system simulation in real-time
          </p>
        </div>
      </div>

      {/* Simulation Configuration Card */}
      <Card title="Simulation Configuration">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-[#717B86] mb-1.5">
                Workload Profile
              </label>
              <select
                className="w-full bg-[#101416] border border-[#303A40] rounded-lg px-3 py-2 text-sm text-[#F3F4F6] focus:outline-none focus:border-[#60A5FA] transition-colors"
                value={config.workload_type}
                onChange={e => setConfig({ ...config, workload_type: e.target.value })}
              >
                {["adversarial_stress", "steady_state", "cpu_spike", "memory_thrashing", "io_bottleneck", "mixed"].map(w => (
                  <option key={w} value={w}>{w}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-[#717B86] mb-1.5">
                Target Policy / Baseline
              </label>
              <select
                className="w-full bg-[#101416] border border-[#303A40] rounded-lg px-3 py-2 text-sm text-[#F3F4F6] focus:outline-none focus:border-[#60A5FA] transition-colors"
                value={config.policy_mode}
                onChange={e => setConfig({ ...config, policy_mode: e.target.value })}
              >
                {["Complete CoReOS", "Conventional (Static RR)", "Independent Agents", "Coordinated (No Conflict)"].map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-[#717B86]">
                  Number of Processes
                </label>
                <span className="text-xs font-semibold text-[#60A5FA]">({config.num_processes})</span>
              </div>
              <input
                type="range"
                min="10"
                max="80"
                className="w-full h-1.5 bg-[#303A40] rounded-lg appearance-none cursor-pointer accent-[#60A5FA]"
                value={config.num_processes}
                onChange={e => setConfig({ ...config, num_processes: parseInt(e.target.value) })}
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-[#717B86]">
                  Base CPU Quantum (ms)
                </label>
                <span className="text-xs font-semibold text-[#60A5FA]">({config.sim_quantum.toFixed(1)})</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="16.0"
                step="0.5"
                className="w-full h-1.5 bg-[#303A40] rounded-lg appearance-none cursor-pointer accent-[#60A5FA]"
                value={config.sim_quantum}
                onChange={e => setConfig({ ...config, sim_quantum: parseFloat(e.target.value) })}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-[#717B86] mb-1.5">
                Random Seed
              </label>
              <input
                type="number"
                className="w-full bg-[#101416] border border-[#303A40] rounded-lg px-3 py-2 text-sm text-[#F3F4F6] focus:outline-none focus:border-[#60A5FA]"
                value={config.seed}
                onChange={e => setConfig({ ...config, seed: parseInt(e.target.value) || 0 })}
              />
            </div>

            <div>
              <button
                onClick={runSimulation}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:bg-[#1E3A8A] text-white font-medium py-2.5 px-6 rounded-lg transition-colors text-sm shadow-sm"
              >
                {loading ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" />
                    <span>Executing simulation (250 ticks)...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Run Simulation (250 ticks)</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </Card>

      {error && (
        <div className="p-3 bg-[#F87171]/10 border border-[#F87171]/30 rounded-lg flex items-center gap-2 text-[#F87171] text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Row */}
      {res?.state && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            title="Turnaround Time"
            value={`${Number(res.state.avg_turnaround_time).toFixed(2)} ticks`}
            subtitle="Average"
            icon={Clock}
            iconColor="text-[#60A5FA]"
          />
          <MetricCard
            title="Waiting Time"
            value={`${Number(res.state.avg_waiting_time).toFixed(2)} ticks`}
            subtitle="Average"
            icon={Activity}
            iconColor="text-[#34D399]"
          />
          <MetricCard
            title="Throughput"
            value={`${Number(res.state.throughput).toFixed(4)} jobs/tick`}
            subtitle="Overall"
            icon={Cpu}
            iconColor="text-[#34D3E9]"
          />
          <MetricCard
            title="Context Switches"
            value={res.state.total_context_switches}
            subtitle="Total"
            icon={Layers}
            iconColor="text-[#FBBF24]"
          />
        </div>
      )}

      {/* Live System Resource Usage Chart */}
      {res?.history && (
        <Card title="System Resource Usage (Live)">
          <InteractiveChart
            title="System Resource Usage (Live)"
            subtitle="CPU, Memory and I/O Saturation over simulation ticks"
            exportFilename="system_resource_usage"
            chartType="cartesian"
            chartHeight={320}
            data={[
              {
                x: res.history.map((h: any) => h.time),
                y: res.history.map((h: any) => h.cpu_utilization),
                type: 'scatter',
                mode: 'lines',
                name: 'CPU',
                line: { color: '#60A5FA', width: 2 }
              },
              {
                x: res.history.map((h: any) => h.time),
                y: res.history.map((h: any) => h.memory_utilization),
                type: 'scatter',
                mode: 'lines',
                name: 'Memory',
                line: { color: '#34D399', width: 2 }
              },
              {
                x: res.history.map((h: any) => h.time),
                y: res.history.map((h: any) => h.io_saturation),
                type: 'scatter',
                mode: 'lines',
                name: 'I/O Saturation',
                line: { color: '#FBBF24', width: 2 }
              }
            ]}
            layout={{
              ...carbonChartLayout,
              height: 320,
              yaxis: {
                ...carbonChartLayout.yaxis,
                title: { text: 'Utilization (%)', font: { color: '#A1A1AA', size: 11 } },
                range: [0, 105]
              },
              xaxis: {
                ...carbonChartLayout.xaxis,
                title: { text: 'Simulation Time (ticks)', font: { color: '#A1A1AA', size: 11 } }
              },
              legend: {
                orientation: 'h',
                x: 0.7,
                y: 1.15,
                font: { color: '#A1A1AA', size: 11 }
              }
            }}
          />
        </Card>
      )}

      {/* Queue Backlog Dynamics Chart */}
      {res?.history && (
        <Card title="Process Queue Dynamics">
          <InteractiveChart
            title="Process Queue Dynamics"
            subtitle="Ready queue and I/O queue lengths over simulation ticks"
            exportFilename="process_queue_dynamics"
            chartType="cartesian"
            chartHeight={260}
            data={[
              {
                x: res.history.map((h: any) => h.time),
                y: res.history.map((h: any) => h.ready_queue_length),
                type: 'scatter',
                mode: 'lines',
                name: 'CPU Queue',
                line: { color: '#60A5FA', width: 2 }
              },
              {
                x: res.history.map((h: any) => h.time),
                y: res.history.map((h: any) => h.io_queue_length),
                type: 'scatter',
                mode: 'lines',
                name: 'I/O Queue',
                line: { color: '#FBBF24', width: 2 }
              }
            ]}
            layout={{
              ...carbonChartLayout,
              height: 260,
              yaxis: {
                ...carbonChartLayout.yaxis,
                title: { text: 'Queue Length (jobs)', font: { color: '#A1A1AA', size: 11 } }
              },
              xaxis: {
                ...carbonChartLayout.xaxis,
                title: { text: 'Simulation Time (ticks)', font: { color: '#A1A1AA', size: 11 } }
              },
              legend: {
                orientation: 'h',
                x: 0.75,
                y: 1.15,
                font: { color: '#A1A1AA', size: 11 }
              }
            }}
          />
        </Card>
      )}
    </div>
  );
}
