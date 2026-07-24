from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend.analyzers.fireworks import FireworksAnalyzer


class FireworksConfigurationTests(unittest.TestCase):
    def test_current_vision_default_and_base_url_are_resolved(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FIREWORKS_MODEL": "",
                "FIREWORKS_BASE_URL": "https://api.fireworks.ai/inference/v1/",
            },
            clear=True,
        ):
            analyzer = FireworksAnalyzer(api_key="real-key-placeholder")
        self.assertEqual(analyzer.model, "accounts/fireworks/models/kimi-k2p5")
        self.assertEqual(
            analyzer.endpoint,
            "https://api.fireworks.ai/inference/v1/chat/completions",
        )


if __name__ == "__main__":
    unittest.main()
