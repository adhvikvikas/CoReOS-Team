"""
Smoke Test for CoReOS Streamlit Dashboard
Verifies module imports, syntax compilation, and data pipeline integration for the dashboard.
"""

import pytest
import py_compile
from pathlib import Path
from src.coreos.config import load_config
from src.coreos.data.loader import DatasetLoader
from src.coreos.simulation.environment import SystemSimulator


def test_dashboard_syntax_compilation():
    dashboard_path = Path(__file__).resolve().parent.parent / "dashboard" / "app.py"
    assert dashboard_path.exists()
    compiled = py_compile.compile(str(dashboard_path))
    assert compiled is not None


def test_dashboard_backend_integrations():
    config = load_config()
    assert config is not None

    loader = DatasetLoader()
    df = loader.load()
    assert not df.empty

    sim = SystemSimulator()
    state = sim.get_system_state()
    assert "cpu_utilization" in state
    assert "memory_utilization" in state


def test_dashboard_navigation_and_reports_execution():
    from streamlit.testing.v1 import AppTest
    dashboard_path = Path(__file__).resolve().parent.parent / "dashboard" / "app.py"
    at = AppTest.from_file(str(dashboard_path), default_timeout=30)
    at.run()
    assert len(at.exception) == 0, f"Dashboard initial load failed: {at.exception}"

    # Navigate to Research Report & Exports page
    at.sidebar.radio[0].set_value("📑 Research Report & Exports").run()
    assert len(at.exception) == 0, f"Research Report page failed with: {at.exception}"

