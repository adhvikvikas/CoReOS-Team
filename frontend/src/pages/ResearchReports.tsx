import { useEffect, useState, useMemo } from 'react';
import api from '../api/client';
import Card from '../components/common/Card';
import { FileText, Table as TableIcon, Archive, AlertCircle, CheckCircle2 } from 'lucide-react';
import { marked } from 'marked';

const TABS = [
  'Executive Summary',
  'Detailed Analysis',
  'Statistical Results',
  'Discussion & Conclusions'
] as const;

type TabType = typeof TABS[number];

export default function ResearchReports() {
  const [activeTab, setActiveTab] = useState<TabType>('Executive Summary');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analysisContent, setAnalysisContent] = useState<string>('');
  const [researchContent, setResearchContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/reports/ablation_summary')
      .then(res => setData(res.data))
      .catch(err => {
        console.warn('Optional ablation telemetry not available:', err);
      })
      .finally(() => setLoading(false));

    api.get('/reports/content/final_canonical_optimization_report.md')
      .then(res => {
        if (res.data && res.data.content) {
          setAnalysisContent(res.data.content);
        } else {
          api.get('/reports/content/phase8_final_competition_report.md')
            .then(r => setAnalysisContent(r.data.content || ''))
            .catch(() => setError('Failed to load canonical analysis report.'));
        }
      })
      .catch(() => {
        api.get('/reports/content/phase8_final_competition_report.md')
          .then(r => setAnalysisContent(r.data.content || ''))
          .catch(() => setError('Failed to load canonical analysis report.'));
      });

    api.get('/reports/content/final_canonical_reproducibility.md')
      .then(res => {
        if (res.data && res.data.content) {
          setResearchContent(res.data.content);
        } else {
          api.get('/reports/content/phase9_final_audit_report.md').then(r => setResearchContent(r.data.content || ''));
        }
      })
      .catch(() => {
        api.get('/reports/content/phase9_final_audit_report.md').then(r => setResearchContent(r.data.content || ''));
      });
  }, []);

  const renderedAnalysis = useMemo(() => {
    if (!analysisContent) return '';
    return marked.parse(analysisContent) as string;
  }, [analysisContent]);

  const renderedResearch = useMemo(() => {
    if (!researchContent) return '';
    return marked.parse(researchContent) as string;
  }, [researchContent]);

  const handleDownload = (filename: string) => {
    window.open(`${api.defaults.baseURL}/reports/download/${filename}`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
          Research Report
        </h1>
        <p className="text-sm text-[#717B86] mt-0.5">
          Empirical analysis, statistical findings and downloadable reports
        </p>
      </div>

      {error && (
        <div className="p-3 bg-[#F87171]/10 border border-[#F87171]/30 rounded-lg flex items-center gap-2 text-[#F87171] text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Navigation Tabs Bar */}
      <div className="flex border-b border-[#303A40] space-x-2">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 px-4 text-xs font-semibold uppercase tracking-wider transition-colors relative ${
              activeTab === tab
                ? 'text-[#60A5FA]'
                : 'text-[#717B86] hover:text-[#A1A1AA]'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#60A5FA]" />
            )}
          </button>
        ))}
      </div>

      {/* Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (Document Content) */}
        <div className="lg:col-span-9 space-y-6">
          <Card>
            {activeTab === 'Executive Summary' && (
              <div className="space-y-6 text-xs leading-relaxed text-[#A1A1AA]">
                <div>
                  <h2 className="text-lg font-bold text-[#F3F4F6] mb-3">
                    1. Executive Summary & Core Findings
                  </h2>
                  <p className="text-[#A1A1AA] text-sm leading-relaxed mb-4">
                    This report presents an empirical, statistically grounded evaluation of all eight candidates across 6 workloads and 30 fresh held-out seeds (1,440 total trials): Conventional (A), Independent Agents (B), Coord No-Conflict (C), Conflict No-Healing (D), Complete CoReOS (E), Phase 7 Improved RL (F), CoReOS (G), and Original RL (H). To uphold rigorous scientific integrity, metrics account transparently for unfinished processes via penalized turnaround, standardized random seeds ensure paired workload equivalence, and statistical uncertainty is reported with 95% confidence intervals.
                  </p>
                </div>

                {/* Key Empirical Takeaways Card */}
                <div className="p-4 bg-[#101416] rounded-xl border border-[#303A40]/80 space-y-3">
                  <h3 className="text-sm font-semibold text-[#60A5FA] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[#60A5FA]" />
                    <span>Key Empirical Takeaways (Canonical Evaluation)</span>
                  </h3>
                  <ul className="space-y-2 text-xs text-[#F3F4F6]">
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] mt-1.5 shrink-0" />
                      <span><strong>Rank 1 — Improved RL (Candidate F):</strong> Achieves highest overall composite score (85.81 ± 0.98) with 95.3% completion rate and 39.8 ticks penalized turnaround across all 6 workloads.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#F472B6] mt-1.5 shrink-0" />
                      <span><strong>Rank 2 — CoReOS (Candidate G):</strong> Achieves 84.87 ± 0.98 composite score, 95.9% completion rate, and lowest overall thrashing (0.13 ticks mean, 99.7% reduction under adversarial stress).</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#94A3B8] mt-1.5 shrink-0" />
                      <span><strong>Rank 3 — Original RL (Candidate H):</strong> Achieves 82.26 ± 1.10 composite score with 90.8% completion rate.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#A78BFA] mt-1.5 shrink-0" />
                      <span><strong>Baselines A–E:</strong> ConflictNoHealing (80.89), CoordNoConflict (80.82), Conventional (80.60), Independent Agents (79.79), and Baseline CoReOS (80.84).</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#34D399] mt-1.5 shrink-0" />
                      <span><strong>Evaluation Protocol:</strong> Exactly 1,440 trials (8 candidates × 6 workloads × 30 seeds) with 300-tick evaluation horizon, zero seed overlap, and frozen composite scoring formula.</span>
                    </li>
                  </ul>
                </div>

                {/* Research Questions & Method Overview */}
                <div className="space-y-3 pt-2">
                  <h3 className="text-sm font-semibold text-[#F3F4F6]">
                    Research Questions & Evaluation Framework
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-3 bg-[#101416]/60 rounded-lg border border-[#303A40]/40">
                      <div className="font-semibold text-[#34D3E9] mb-1">RQ1: Feature Predictive Power</div>
                      <div>Evaluates whether cross-resource telemetry improves the detection of impending system failure.</div>
                    </div>
                    <div className="p-3 bg-[#101416]/60 rounded-lg border border-[#303A40]/40">
                      <div className="font-semibold text-[#34D399] mb-1">RQ2: Conflict Coordination</div>
                      <div>Assesses if predictive arbitration outperforms uncoordinated independent agents.</div>
                    </div>
                    <div className="p-3 bg-[#101416]/60 rounded-lg border border-[#303A40]/40">
                      <div className="font-semibold text-[#FBBF24] mb-1">RQ3: Self-Healing Recovery</div>
                      <div>Measures regression duration reduction via automated cooling-off periods and overrides.</div>
                    </div>
                    <div className="p-3 bg-[#101416]/60 rounded-lg border border-[#303A40]/40">
                      <div className="font-semibold text-[#60A5FA] mb-1">RQ4: Computational Overhead</div>
                      <div>Confirms decision overhead remains well below real-time operational boundaries across all candidates.</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'Detailed Analysis' && (
              <div className="space-y-4">
                <h2 className="text-lg font-bold text-[#F3F4F6]">
                  Phase 8 Final Benchmark Competition Report
                </h2>
                {analysisContent ? (
                  <div
                    className="markdown-content text-xs text-[#A1A1AA] overflow-y-auto max-h-[700px] pr-2"
                    dangerouslySetInnerHTML={{ __html: renderedAnalysis }}
                  />
                ) : (
                  <div className="text-xs text-[#717B86] py-6">
                    Benchmark analysis document is loading...
                  </div>
                )}
              </div>
            )}

            {activeTab === 'Statistical Results' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-bold text-[#F3F4F6] mb-1">
                    Component Ablation & Statistical Comparison
                  </h2>
                  <p className="text-xs text-[#717B86]">
                    Measured variance and performance changes across isolated architectural features
                  </p>
                </div>

                {loading ? (
                  <div className="text-center py-8 text-xs text-[#717B86]">
                    Loading statistical results...
                  </div>
                ) : data && data.data && data.data.length > 0 ? (
                  <div className="overflow-x-auto -mx-6 -my-2">
                    <table className="w-full text-left text-xs whitespace-nowrap">
                      <thead className="bg-[#101416] text-[#A1A1AA] border-b border-[#303A40]">
                        <tr>
                          <th className="px-5 py-3 font-semibold uppercase tracking-wider">Workload</th>
                          <th className="px-5 py-3 font-semibold uppercase tracking-wider">Configuration</th>
                          <th className="px-5 py-3 font-semibold uppercase tracking-wider">Completion Rate</th>
                          <th className="px-5 py-3 font-semibold uppercase tracking-wider">Avg Turnaround</th>
                          <th className="px-5 py-3 font-semibold uppercase tracking-wider">Throughput</th>
                          <th className="px-5 py-3 font-semibold uppercase tracking-wider">Thrashing Ticks</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#303A40]/60">
                        {data.data.map((row: any, i: number) => (
                          <tr key={i} className="hover:bg-[#20262B] transition-colors">
                            <td className="px-5 py-2.5 font-medium text-[#60A5FA]">{row.workload}</td>
                            <td className="px-5 py-2.5 text-[#F3F4F6]">{row.configuration}</td>
                            <td className="px-5 py-2.5 text-[#34D399] font-mono">{row.completion_rate?.toFixed(1)}%</td>
                            <td className="px-5 py-2.5 text-[#A1A1AA] font-mono">{row.avg_turnaround_time?.toFixed(2)}</td>
                            <td className="px-5 py-2.5 text-[#A1A1AA] font-mono">{row.throughput?.toFixed(3)}</td>
                            <td className="px-5 py-2.5 text-[#FBBF24] font-mono">{row.thrashing_ticks?.toFixed(1)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-xs text-[#717B86] py-6">
                    Ablation telemetry not available for this evaluation.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'Discussion & Conclusions' && (
              <div className="space-y-4">
                <h2 className="text-lg font-bold text-[#F3F4F6]">
                  Phase 9 Independent Final Audit Report
                </h2>
                {researchContent ? (
                  <div
                    className="markdown-content text-xs text-[#A1A1AA] overflow-y-auto max-h-[700px] pr-2"
                    dangerouslySetInnerHTML={{ __html: renderedResearch }}
                  />
                ) : (
                  <div className="text-xs text-[#717B86] py-6">
                    Research findings document is loading...
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column (Download Cards & Metadata) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Final Canonical Datasets Card */}
          <Card title="Final Canonical Datasets">
            <div className="space-y-2.5 py-1">
              <button
                onClick={() => handleDownload('final_canonical_optimization_report.md')}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white transition-colors text-xs font-medium text-left shadow-sm"
              >
                <FileText className="w-4 h-4 shrink-0 text-white" />
                <span className="truncate">Final Optimization Report (MD)</span>
              </button>

              <button
                onClick={() => handleDownload('final_canonical_benchmark_results.csv')}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#F3F4F6] transition-colors text-xs font-medium text-left"
              >
                <TableIcon className="w-4 h-4 shrink-0 text-[#2DD4BF]" />
                <span className="truncate">Canonical Results (1,440 Trials CSV)</span>
              </button>

              <button
                onClick={() => handleDownload('final_canonical_ranking_summary.csv')}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#F3F4F6] transition-colors text-xs font-medium text-left"
              >
                <TableIcon className="w-4 h-4 shrink-0 text-[#60A5FA]" />
                <span className="truncate">Canonical Ranking Summary (CSV)</span>
              </button>

              <button
                onClick={() => handleDownload('final_canonical_per_workload_summary.csv')}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#F3F4F6] transition-colors text-xs font-medium text-left"
              >
                <TableIcon className="w-4 h-4 shrink-0 text-[#F472B6]" />
                <span className="truncate">Per-Workload Summary (CSV)</span>
              </button>

              <button
                onClick={() => handleDownload('final_canonical_statistical_comparisons.csv')}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40] text-[#F3F4F6] transition-colors text-xs font-medium text-left"
              >
                <TableIcon className="w-4 h-4 shrink-0 text-[#34D399]" />
                <span className="truncate">Statistical Comparisons (CSV)</span>
              </button>

              <button
                onClick={() => handleDownload('final_canonical_reproducibility.md')}
                className="w-full flex items-center gap-2.5 p-2 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40]/80 text-[#A1A1AA] transition-colors text-[11px] font-medium text-left"
              >
                <FileText className="w-3.5 h-3.5 shrink-0 text-[#A78BFA]" />
                <span className="truncate">Reproducibility Record (MD)</span>
              </button>
            </div>
          </Card>

          {/* Historical Datasets Card */}
          <Card title="Historical Experiments (Phases 1–9)">
            <div className="space-y-2 py-1">
              <button
                onClick={() => handleDownload('phase8_final_benchmark_results.csv')}
                className="w-full flex items-center gap-2.5 p-2 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40]/60 text-[#A1A1AA] transition-colors text-[11px] font-medium text-left"
              >
                <Archive className="w-3.5 h-3.5 shrink-0 text-[#717B86]" />
                <span className="truncate">Phase 8 Trials (1,440 CSV)</span>
              </button>

              <button
                onClick={() => handleDownload('phase9_final_audit_report.md')}
                className="w-full flex items-center gap-2.5 p-2 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40]/60 text-[#A1A1AA] transition-colors text-[11px] font-medium text-left"
              >
                <FileText className="w-3.5 h-3.5 shrink-0 text-[#717B86]" />
                <span className="truncate">Phase 9 Audit Report (MD)</span>
              </button>

              <button
                onClick={() => handleDownload('phase3_benchmark_results.csv')}
                className="w-full flex items-center gap-2.5 p-2 rounded-lg bg-[#101416] hover:bg-[#20262B] border border-[#303A40]/60 text-[#A1A1AA] transition-colors text-[11px] font-medium text-left"
              >
                <Archive className="w-3.5 h-3.5 shrink-0 text-[#717B86]" />
                <span className="truncate">Phase 3 Raw Results (CSV)</span>
              </button>
            </div>
          </Card>

          {/* Report Metadata Card */}
          <Card title="Competition Metadata">
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-[#303A40]/40">
                <span className="text-[#717B86]">Completed On</span>
                <span className="text-[#F3F4F6] font-medium">Oct 13, 2026</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-[#303A40]/40">
                <span className="text-[#717B86]">Evaluation Phase</span>
                <span className="text-[#34D399] font-medium font-mono">Final Canonical</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-[#303A40]/40">
                <span className="text-[#717B86]">Candidates</span>
                <span className="text-[#F3F4F6] font-medium">8 Evaluated</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-[#303A40]/40">
                <span className="text-[#717B86]">Total Trials</span>
                <span className="text-[#F3F4F6] font-medium">1,440 Matched</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-[#717B86]">Top 2 Standings</span>
                <span className="text-[#2DD4BF] font-semibold text-right">#1 F_ImprovedRL (85.81)<br />#2 CoReOS (84.87)</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
