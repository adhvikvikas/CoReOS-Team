import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Overview from './pages/Overview';
import DatasetExplorer from './pages/DatasetExplorer';
import SimulationLab from './pages/SimulationLab';
import AgentControl from './pages/AgentControl';
import ConflictAnalysis from './pages/ConflictAnalysis';
import SelfHealing from './pages/SelfHealing';
import BenchmarkLab from './pages/BenchmarkLab';
import ResearchReports from './pages/ResearchReports';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/dataset" element={<DatasetExplorer />} />
          <Route path="/simulation" element={<SimulationLab />} />
          <Route path="/agents" element={<AgentControl />} />
          <Route path="/conflicts" element={<ConflictAnalysis />} />
          <Route path="/healing" element={<SelfHealing />} />
          <Route path="/benchmarks" element={<BenchmarkLab />} />
          <Route path="/reports" element={<ResearchReports />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
