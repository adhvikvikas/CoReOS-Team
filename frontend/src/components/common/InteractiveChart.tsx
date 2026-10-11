import React, { useState, useRef, useEffect, useCallback } from 'react';
import Plot from 'react-plotly.js';
// @ts-ignore
import Plotly from 'plotly.js/dist/plotly';
import {
  ZoomIn,
  ZoomOut,
  Move,
  RotateCcw,
  Maximize2,
  Camera,
  FileCode,
  FileSpreadsheet,
  X
} from 'lucide-react';

export interface InteractiveChartProps {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  style?: React.CSSProperties;
  className?: string;
  title?: string;
  subtitle?: string;
  chartHeight?: number | string;
  chartType?: 'cartesian' | 'pie' | 'heatmap' | 'bar';
  exportFilename?: string;
  headerAction?: React.ReactNode;
}

export default function InteractiveChart({
  data,
  layout,
  config,
  style,
  className = '',
  title = 'Chart',
  subtitle,
  chartHeight = 320,
  chartType,
  exportFilename,
  headerAction,
}: InteractiveChartProps) {
  const [graphDiv, setGraphDiv] = useState<any>(null);
  const [modalGraphDiv, setModalGraphDiv] = useState<any>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const modalContainerRef = useRef<HTMLDivElement>(null);
  const initialLayoutRef = useRef<Partial<Plotly.Layout>>(layout);

  useEffect(() => {
    initialLayoutRef.current = layout;
  }, [layout]);

  const resolveTarget = (targetDiv: any, isModal = false) => {
    if (targetDiv && targetDiv._fullLayout) return targetDiv;
    if (isModal) {
      return modalContainerRef.current?.querySelector('.js-plotly-plot') || modalGraphDiv;
    }
    return containerRef.current?.querySelector('.js-plotly-plot') || graphDiv;
  };

  // Infer chart type if not explicitly provided
  const detectedType = chartType || (
    data?.[0]?.type === 'pie' ? 'pie' :
    data?.[0]?.type === 'heatmap' ? 'heatmap' :
    'cartesian'
  );

  const isCartesian = detectedType !== 'pie';

  const getCleanFilename = () => {
    return (exportFilename || title || 'coreos_chart')
      .toLowerCase()
      .replace(/[^a-z0-9_-]/g, '_')
      .replace(/_+/g, '_');
  };

  // Zoom In
  const handleZoomIn = (target?: any, isModal = false) => {
    const targetDiv = resolveTarget(target, isModal);
    if (!targetDiv || !targetDiv._fullLayout) return;
    try {
      const fl = targetDiv._fullLayout;
      const xR = fl.xaxis?.range;
      const yR = fl.yaxis?.range;
      if (xR && yR && typeof xR[0] === 'number' && typeof xR[1] === 'number') {
        const xSpan = (xR[1] - xR[0]) * 0.75;
        const xMid = (xR[0] + xR[1]) / 2;
        const ySpan = (yR[1] - yR[0]) * 0.75;
        const yMid = (yR[0] + yR[1]) / 2;
        Plotly.relayout(targetDiv, {
          'xaxis.range': [xMid - xSpan / 2, xMid + xSpan / 2],
          'yaxis.range': [yMid - ySpan / 2, yMid + ySpan / 2],
          'xaxis.autorange': false,
          'yaxis.autorange': false,
        } as any);
      }
    } catch (err) {
      console.error('Zoom in failed:', err);
    }
  };

  // Zoom Out
  const handleZoomOut = (target?: any, isModal = false) => {
    const targetDiv = resolveTarget(target, isModal);
    if (!targetDiv || !targetDiv._fullLayout) return;
    try {
      const fl = targetDiv._fullLayout;
      const xR = fl.xaxis?.range;
      const yR = fl.yaxis?.range;
      if (xR && yR && typeof xR[0] === 'number' && typeof xR[1] === 'number') {
        const xSpan = (xR[1] - xR[0]) / 0.75;
        const xMid = (xR[0] + xR[1]) / 2;
        const ySpan = (yR[1] - yR[0]) / 0.75;
        const yMid = (yR[0] + yR[1]) / 2;
        Plotly.relayout(targetDiv, {
          'xaxis.range': [xMid - xSpan / 2, xMid + xSpan / 2],
          'yaxis.range': [yMid - ySpan / 2, yMid + ySpan / 2],
          'xaxis.autorange': false,
          'yaxis.autorange': false,
        } as any);
      }
    } catch (err) {
      console.error('Zoom out failed:', err);
    }
  };

  // Pan toggle
  const handleTogglePan = (target?: any, isModal = false) => {
    const targetDiv = resolveTarget(target, isModal);
    if (!targetDiv || !targetDiv._fullLayout) return;
    try {
      const currentMode = targetDiv._fullLayout.dragmode;
      const nextMode = currentMode === 'pan' ? 'zoom' : 'pan';
      Plotly.relayout(targetDiv, { dragmode: nextMode });
      setIsPanning(nextMode === 'pan');
    } catch (err) {
      console.error('Pan toggle failed:', err);
    }
  };

  // Reset View
  const handleReset = (target?: any, isModal = false) => {
    const targetDiv = resolveTarget(target, isModal);
    if (!targetDiv) return;
    try {
      const init = initialLayoutRef.current;
      const update: any = {
        'xaxis.autorange': true,
        'yaxis.autorange': true,
        dragmode: 'zoom'
      };
      if (init?.xaxis?.range) {
        update['xaxis.range'] = [...(init.xaxis.range as any)];
        update['xaxis.autorange'] = false;
      }
      if (init?.yaxis?.range) {
        update['yaxis.range'] = [...(init.yaxis.range as any)];
        update['yaxis.autorange'] = false;
      }
      Plotly.relayout(targetDiv, update);
      setIsPanning(false);
    } catch (err) {
      console.error('Reset view failed:', err);
    }
  };

  // Download PNG
  const handleDownloadPNG = async (target?: any, isModal = false) => {
    const targetDiv = resolveTarget(target, isModal);
    if (!targetDiv) return;
    try {
      setErrorMsg(null);
      await Plotly.downloadImage(targetDiv, {
        format: 'png',
        filename: getCleanFilename(),
        width: 1200,
        height: 700,
      });
    } catch (err) {
      console.error('Download PNG failed:', err);
      setErrorMsg('Failed to export PNG image.');
    }
  };

  // Download SVG
  const handleDownloadSVG = async (target?: any, isModal = false) => {
    const targetDiv = resolveTarget(target, isModal);
    if (!targetDiv) return;
    try {
      setErrorMsg(null);
      await Plotly.downloadImage(targetDiv, {
        format: 'svg',
        filename: getCleanFilename(),
        width: 1200,
        height: 700,
      });
    } catch (err) {
      console.error('Download SVG failed:', err);
      setErrorMsg('Failed to export SVG vector.');
    }
  };

  // Download CSV
  const handleDownloadCSV = () => {
    try {
      setErrorMsg(null);
      let csvContent = '';

      if (detectedType === 'heatmap') {
        // Heatmap Matrix export
        const heatTrace = data[0] as any;
        if (heatTrace && heatTrace.z) {
          const xCols = heatTrace.x || [];
          const yRows = heatTrace.y || [];
          csvContent = 'Feature,' + xCols.join(',') + '\n';
          yRows.forEach((rowLabel: string, rIdx: number) => {
            const rowValues = heatTrace.z[rIdx] || [];
            csvContent += `"${rowLabel}",` + rowValues.join(',') + '\n';
          });
        }
      } else if (detectedType === 'pie') {
        // Pie / Donut export
        const pieTrace = data[0] as any;
        if (pieTrace && pieTrace.labels) {
          csvContent = 'Category,Value,Percentage\n';
          pieTrace.labels.forEach((label: string, idx: number) => {
            const val = pieTrace.values?.[idx] ?? '';
            csvContent += `"${label}",${val}\n`;
          });
        }
      } else {
        // Line / Scatter / Bar export
        if (data.length > 0) {
          const firstTrace = data[0] as any;
          const xPoints = firstTrace.x || [];
          const header = ['x', ...data.map((t: any) => `"${t.name || 'Series'}"`)].join(',');
          const rows = [header];
          for (let i = 0; i < xPoints.length; i++) {
            const row = [xPoints[i], ...data.map((t: any) => t.y?.[i] ?? '')];
            rows.push(row.join(','));
          }
          csvContent = rows.join('\n');
        }
      }

      if (!csvContent) {
        setErrorMsg('No exportable data points available.');
        return;
      }

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `${getCleanFilename()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download CSV failed:', err);
      setErrorMsg('Failed to export CSV data.');
    }
  };

  // Close modal on Esc
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && isExpanded) {
      setIsExpanded(false);
    }
  }, [isExpanded]);

  useEffect(() => {
    if (isExpanded) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isExpanded, handleKeyDown]);

  // Recalculate dimensions on modal open
  useEffect(() => {
    if (isExpanded && modalGraphDiv) {
      const timer = setTimeout(() => {
        try {
          Plotly.Plots.resize(modalGraphDiv);
        } catch (_) {}
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isExpanded, modalGraphDiv]);

  // Render the unified Toolbar
  const renderToolbar = (targetDiv: any, isModal = false) => (
    <div className="inline-flex items-center gap-0.5 bg-[#101416]/90 border border-[#263038] rounded-lg p-0.5 shadow-sm text-xs select-none">
      {/* Cartesian Interaction Tools: Zoom In, Zoom Out, Pan, Reset */}
      {isCartesian && (
        <>
          <button
            type="button"
            onClick={() => handleZoomIn(targetDiv, isModal)}
            className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
            title="Zoom In"
            aria-label="Zoom in"
          >
            <ZoomIn className="w-3.5 h-3.5" />
            <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
              Zoom In
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleZoomOut(targetDiv, isModal)}
            className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
            title="Zoom Out"
            aria-label="Zoom out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
            <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
              Zoom Out
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleTogglePan(targetDiv, isModal)}
            className={`p-1.5 rounded transition-colors relative group ${
              isPanning
                ? 'bg-[#164E63] text-[#38BDF8] font-semibold'
                : 'text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B]'
            }`}
            title={isPanning ? 'Panning Active (Click for Box Zoom)' : 'Pan tool'}
            aria-label="Toggle pan"
          >
            <Move className="w-3.5 h-3.5" />
            <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
              {isPanning ? 'Pan (Active)' : 'Pan View'}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleReset(targetDiv, isModal)}
            className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
            title="Reset Axes & Zoom"
            aria-label="Reset view"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
              Reset View
            </span>
          </button>

          <span className="w-px h-3.5 bg-[#263038] mx-0.5" />
        </>
      )}

      {/* Export Tools: PNG, SVG, CSV */}
      <button
        type="button"
        onClick={() => handleDownloadPNG(targetDiv, isModal)}
        className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
        title="Download PNG image"
        aria-label="Download PNG image"
      >
        <Camera className="w-3.5 h-3.5" />
        <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
          Export PNG
        </span>
      </button>

      <button
        type="button"
        onClick={() => handleDownloadSVG(targetDiv, isModal)}
        className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
        title="Download SVG vector"
        aria-label="Download SVG vector"
      >
        <FileCode className="w-3.5 h-3.5" />
        <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
          Export SVG
        </span>
      </button>

      <button
        type="button"
        onClick={handleDownloadCSV}
        className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
        title="Download Plotted Data as CSV"
        aria-label="Download CSV data"
      >
        <FileSpreadsheet className="w-3.5 h-3.5" />
        <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
          Export CSV Data
        </span>
      </button>

      {/* Expand / Enlarge tool (only on normal view) */}
      {!isModal && (
        <>
          <span className="w-px h-3.5 bg-[#263038] mx-0.5" />
          <button
            type="button"
            onClick={() => setIsExpanded(true)}
            className="p-1.5 rounded text-[#8A99A8] hover:text-[#F3F4F6] hover:bg-[#1E252B] transition-colors relative group"
            title="Expand graph in enlarged modal"
            aria-label="Expand graph"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span className="opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0F12] border border-[#2D3748] text-[#E2E8F0] rounded shadow-lg whitespace-nowrap z-40">
              Expand Graph
            </span>
          </button>
        </>
      )}
    </div>
  );

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      {/* Top Header / Action Row above Plot */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex-1 min-w-0 pr-2">
          {headerAction}
        </div>
        <div className="shrink-0">
          {renderToolbar(graphDiv, false)}
        </div>
      </div>

      {errorMsg && (
        <div className="mb-2 px-2.5 py-1 text-xs text-[#F87171] bg-[#F87171]/10 border border-[#F87171]/30 rounded">
          {errorMsg}
        </div>
      )}

      {/* Normal Embedded Chart */}
      <div className="w-full">
        <Plot
          data={data}
          layout={{
            ...layout,
            autosize: true,
          }}
          config={{
            displayModeBar: false,
            responsive: true,
            ...config,
          }}
          useResizeHandler
          style={{ width: '100%', height: typeof chartHeight === 'number' ? `${chartHeight}px` : chartHeight, ...style }}
          onInitialized={(_, gd) => setGraphDiv(gd)}
          onUpdate={(_, gd) => setGraphDiv(gd)}
        />
      </div>

      {/* Modal / Fullscreen-style Overlay */}
      {isExpanded && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-chart-title"
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 lg:p-8"
          onClick={() => setIsExpanded(false)}
        >
          <div
            className="bg-[#101416] border border-[#2A343D] rounded-2xl w-full max-w-6xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#22292F] bg-[#131719] shrink-0">
              <div>
                <h2 id="modal-chart-title" className="text-base font-semibold text-[#F3F4F6]">
                  {title}
                </h2>
                {subtitle && (
                  <p className="text-xs text-[#717B86] mt-0.5">{subtitle}</p>
                )}
              </div>

              <div className="flex items-center gap-3">
                {renderToolbar(modalGraphDiv, true)}

                <button
                  type="button"
                  onClick={() => setIsExpanded(false)}
                  className="p-1.5 rounded-lg text-[#717B86] hover:text-[#F3F4F6] hover:bg-[#1E252B] border border-[#263038] transition-colors"
                  title="Close (Esc)"
                  aria-label="Close enlarged chart"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Modal Body with Large Plot */}
            <div ref={modalContainerRef} className="p-6 flex-1 overflow-auto bg-[#0C1012]">
              <Plot
                data={data}
                layout={{
                  ...layout,
                  height: 580,
                  autosize: true,
                  margin: {
                    l: 60,
                    r: 30,
                    t: 30,
                    b: 60,
                    ...(layout.margin || {}),
                  },
                }}
                config={{
                  displayModeBar: false,
                  responsive: true,
                  ...config,
                }}
                useResizeHandler
                style={{ width: '100%', height: '580px' }}
                onInitialized={(_, gd) => setModalGraphDiv(gd)}
                onUpdate={(_, gd) => setModalGraphDiv(gd)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
