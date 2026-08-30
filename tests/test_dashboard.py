"""Smoke tests for every Streamlit dashboard section."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DashboardChecks(unittest.TestCase):
    def _open_page(self, page_name: str) -> AppTest:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception, f"Command Center failed: {app.exception}")
        app.sidebar.radio[0].set_value(page_name).run()
        self.assertFalse(app.exception, f"{page_name} failed: {app.exception}")
        return app

    def test_command_center(self) -> None:
        app = self._open_page("Command Center")
        self.assertTrue(any("AquaGuard AI" in title.value for title in app.title))
        self.assertEqual(app.select_slider[0].label, "DMA snapshot hour")
        self.assertTrue(any("Inlet volume" in item.value for item in app.markdown))
        self.assertTrue(any("Metered consumption" in item.value for item in app.markdown))
        self.assertTrue(any("What-if Scenario Lab" in item.value for item in app.markdown))
        self.assertEqual(len(app.number_input), 4)

    def test_network_map(self) -> None:
        app = self._open_page("Network Map")
        self.assertTrue(any("Conceptual DMA Sensor Network" in title.value for title in app.title))

    def test_city_overview(self) -> None:
        app = self._open_page("Meter Sites")
        self.assertTrue(any("Meter Site Overview" in title.value for title in app.title))
        self.assertEqual(app.select_slider[0].label, "Site inspection hour")
        self.assertEqual(app.selectbox[0].label, "Meter location")

    def test_zone_intelligence(self) -> None:
        app = self._open_page("DMA Intelligence")
        self.assertTrue(any("DMA Intelligence" in title.value for title in app.title))
        self.assertTrue(any("DMA observation history" in item.value for item in app.markdown))
        self.assertIn("Date", app.dataframe[0].value.columns)
        self.assertIn("Time", app.dataframe[0].value.columns)

    def test_alerts(self) -> None:
        app = self._open_page("Alerts")
        self.assertTrue(any("Alerts" in title.value for title in app.title))

    def test_model_validation(self) -> None:
        app = self._open_page("Model Validation")
        self.assertTrue(any("Controlled-Test Validation" in title.value for title in app.title))

if __name__ == "__main__":
    unittest.main()
