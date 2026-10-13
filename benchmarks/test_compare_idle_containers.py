"""Regression tests for benchmark profile metadata and container configuration."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("compare-idle-containers.py")
SPEC = importlib.util.spec_from_file_location("compare_idle_containers", SCRIPT)
benchmark = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(benchmark)


def environment_values(command):
    return [
        command[index + 1]
        for index, value in enumerate(command[:-1])
        if value == "-e"
    ]


class ShareScanConfigurationTests(unittest.TestCase):
    def test_disconnected_slskd_metadata_matches_container_configuration(self):
        metadata = benchmark.share_scan_metadata(["slskd"], live_session=False)
        command = benchmark.run_command("slskd", "test", live_session=False)

        self.assertTrue(metadata["share_scan_disabled"])
        self.assertEqual({"slskd": True}, metadata["share_scan_disabled_by_profile"])
        self.assertEqual(
            1, environment_values(command).count("SLSKD_NO_SHARE_SCAN=true")
        )

    def test_disconnected_slskr_profiles_keep_scanning_enabled(self):
        metadata = benchmark.share_scan_metadata(["slskr", "slskr-dht"], live_session=False)
        command = benchmark.run_command("slskr", "test", live_session=False)

        self.assertFalse(metadata["share_scan_disabled"])
        self.assertEqual(
            {"slskr": False, "slskr-dht": False},
            metadata["share_scan_disabled_by_profile"],
        )
        self.assertNotIn("SLSKD_NO_SHARE_SCAN=true", environment_values(command))

    def test_live_profiles_disable_scanning_and_record_each_profile(self):
        profiles = ["slskr", "slskd", "slskr-dht"]
        metadata = benchmark.share_scan_metadata(profiles, live_session=True)

        self.assertTrue(metadata["share_scan_disabled"])
        self.assertEqual(
            {profile: True for profile in profiles},
            metadata["share_scan_disabled_by_profile"],
        )
        for profile in profiles:
            command = benchmark.run_command(profile, "test", live_session=True)
            self.assertIn("SLSKD_NO_SHARE_SCAN=true", environment_values(command))


if __name__ == "__main__":
    unittest.main()
