"""Regression tests for benchmark profile metadata and container configuration."""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


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


class LocalApiRequestTests(unittest.TestCase):
    def test_uses_only_a_fixed_loopback_http_endpoint(self):
        with patch.object(
            benchmark, "docker", return_value="127.0.0.1:45678"
        ) as docker_command:
            with patch.object(benchmark.http.client, "HTTPConnection") as factory:
                connection = factory.return_value
                response = connection.getresponse.return_value
                response.status = 200
                response.read.return_value = b'{"connected":true}'

                result = benchmark.local_api_json(
                    "bench-container",
                    "/api/v0/server",
                    ("Authorization", "Bearer test-token"),
                )

        self.assertEqual({"connected": True}, result)
        docker_command.assert_called_once_with(
            "port", "bench-container", "5030/tcp"
        )
        factory.assert_called_once_with("127.0.0.1", 45678, timeout=10)
        connection.request.assert_called_once_with(
            "GET",
            "/api/v0/server",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer test-token",
            },
        )
        connection.close.assert_called_once_with()

    def test_rejects_file_urls_before_contacting_docker_or_http(self):
        with patch.object(benchmark, "docker") as docker_command:
            with patch.object(benchmark.http.client, "HTTPConnection") as factory:
                with self.assertRaisesRegex(
                    ValueError, "unsupported local status API path"
                ):
                    benchmark.local_api_json(
                        "bench-container", "file:///etc/passwd"
                    )

        docker_command.assert_not_called()
        factory.assert_not_called()

    def test_rejects_out_of_range_ports_before_opening_http_connection(self):
        with patch.object(benchmark, "docker", return_value="127.0.0.1:70000"):
            with patch.object(benchmark.http.client, "HTTPConnection") as factory:
                with self.assertRaisesRegex(
                    ValueError, "outside the TCP port range"
                ):
                    benchmark.local_api_json(
                        "bench-container", "/api/dht/status"
                    )

        factory.assert_not_called()


    def test_rejects_http_errors_and_closes_the_connection(self):
        with patch.object(benchmark, "docker", return_value="127.0.0.1:45678"):
            with patch.object(benchmark.http.client, "HTTPConnection") as factory:
                connection = factory.return_value
                connection.getresponse.return_value.status = 401

                with self.assertRaisesRegex(RuntimeError, "returned HTTP 401"):
                    benchmark.local_api_json(
                        "bench-container", "/api/v0/server"
                    )

        connection.close.assert_called_once_with()

    def test_rejects_oversized_status_responses_and_closes_the_connection(self):
        with patch.object(benchmark, "docker", return_value="127.0.0.1:45678"):
            with patch.object(benchmark.http.client, "HTTPConnection") as factory:
                connection = factory.return_value
                response = connection.getresponse.return_value
                response.status = 200
                response.read.return_value = b"x" * (
                    benchmark.MAX_LOCAL_API_RESPONSE_BYTES + 1
                )

                with self.assertRaisesRegex(
                    RuntimeError, "exceeded 65536 bytes"
                ):
                    benchmark.local_api_json(
                        "bench-container", "/api/dht/status"
                    )

        response.read.assert_called_once_with(
            benchmark.MAX_LOCAL_API_RESPONSE_BYTES + 1
        )
        connection.close.assert_called_once_with()


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


class NetworkMetadataTests(unittest.TestCase):
    def test_single_dht_profile_reports_bridge_network(self):
        self.assertEqual(
            {"network": "bridge", "network_by_profile": {"slskr-dht": "bridge"}},
            benchmark.network_metadata(["slskr-dht"], live_session=False),
        )

    def test_uniform_and_mixed_profile_networks_are_accurately_summarized(self):
        self.assertEqual(
            {"network": "none", "network_by_profile": {"slskr": "none"}},
            benchmark.network_metadata(["slskr"], live_session=False),
        )
        self.assertEqual(
            {
                "network": "profile-dependent",
                "network_by_profile": {"slskr": "none", "slskr-dht": "bridge"},
            },
            benchmark.network_metadata(["slskr", "slskr-dht"], live_session=False),
        )
        self.assertEqual(
            {
                "network": "bridge",
                "network_by_profile": {"slskr": "bridge", "slskr-dht": "bridge"},
            },
            benchmark.network_metadata(["slskr", "slskr-dht"], live_session=True),
        )


class BenchmarkReportIntegrityTests(unittest.TestCase):
    def test_live_slskd_report_counts_metadata_only_retry_attempt(self):
        artifacts = SCRIPT.parent / "artifacts"
        primary_path = artifacts / "20261012-live-soulseek-idle-matrix.json"
        replacement_path = artifacts / "20261012-live-soulseek-slskd-retry-2.json"
        metadata_only_path = artifacts / "20261012-live-soulseek-slskd-retry.json"
        primary = json.loads(primary_path.read_text())
        replacement = json.loads(replacement_path.read_text())
        metadata_only = json.loads(metadata_only_path.read_text())

        primary_attempts = [
            trial for trial in primary["trials"] if trial["app"] == "slskd"
        ]
        replacement_attempts = [
            trial for trial in replacement["trials"] if trial["app"] == "slskd"
        ]
        metadata_only_attempt = (
            "slskd" in metadata_only["parameters"]["profiles"]
            and metadata_only["parameters"]["live_soulseek_session"]
            and bool(metadata_only["started_utc"])
            and not metadata_only["trials"]
        )
        valid_attempts = sum(
            trial["session_logged_in_at_measurement_boundaries"]
            for trial in primary_attempts + replacement_attempts
        )
        attempt_count = (
            len(primary_attempts)
            + len(replacement_attempts)
            + int(metadata_only_attempt)
        )

        self.assertEqual((3, 5), (valid_attempts, attempt_count))
        report = (artifacts / "20261012-live-soulseek-idle.md").read_text()
        self.assertIn("3 of 5 attempts", report)
        readme = (SCRIPT.parent.parent / "README.md").read_text()
        self.assertIn("3 of 5 attempts", readme)


if __name__ == "__main__":
    unittest.main()
