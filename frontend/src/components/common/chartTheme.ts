export const carbonChartLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: {
    color: '#F3F4F6',
    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif',
    size: 11,
  },
  xaxis: {
    gridcolor: '#303A40',
    linecolor: '#303A40',
    tickfont: { color: '#A1A1AA', size: 10 },
    zerolinecolor: '#303A40',
  },
  yaxis: {
    gridcolor: '#303A40',
    linecolor: '#303A40',
    tickfont: { color: '#A1A1AA', size: 10 },
    zerolinecolor: '#303A40',
  },
  legend: {
    font: { color: '#A1A1AA', size: 11 },
    bgcolor: 'rgba(26, 31, 35, 0.6)',
    bordercolor: '#303A40',
    borderwidth: 1,
  },
  margin: { l: 45, r: 25, t: 35, b: 35 },
};

export const CARBON_COLORS = {
  blue: '#60A5FA',
  cyan: '#34D3E9',
  green: '#34D399',
  amber: '#FBBF24',
  red: '#F87171',
  purple: '#A78BFA',
  pink: '#F472B6',
  muted: '#717B86',
};

export const BASELINE_CARBON_COLORS: Record<string, string> = {
  'A_Conventional': '#60A5FA',       // Blue
  'B_IndependentAgents': '#34D399',   // Green
  'C_CoordNoConflict': '#FBBF24',     // Amber
  'D_ConflictNoHealing': '#F87171',   // Red/coral
  'E_CompleteCoReOS': '#A78BFA',      // Purple
  'F_LearningRL': '#34D3E9',          // Cyan
};
