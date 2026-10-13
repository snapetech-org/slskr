"""Regression tests for benchmark profile metadata and container configuration."""

import hashlib
import importlib.util
import json
from argparse import Namespace
from os import environ
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from unittest.mock import call, patch


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


class HostCpuAccountingTests(unittest.TestCase):
    def test_guest_ticks_are_not_added_twice_to_host_cpu_total(self):
        ticks = benchmark.parse_host_cpu_ticks(
            "cpu 100 20 30 500 10 5 7 8 900 40"
        )

        self.assertEqual({"total": 680, "idle": 510}, ticks)


class LocalDockerDaemonTests(unittest.TestCase):
    def test_rejects_remote_context_even_when_docker_host_is_local(self):
        with patch.dict(
            environ,
            {
                "DOCKER_CONTEXT": "remote-benchmark",
                "DOCKER_HOST": "unix:///var/run/docker.sock",
            },
        ):
            with patch.object(
                benchmark, "docker", return_value=json.dumps("ssh://docker@example")
            ) as docker_command:
                with self.assertRaisesRegex(RuntimeError, "local Docker daemon"):
                    benchmark.require_local_docker_daemon()

        docker_command.assert_called_once_with(
            "context", "inspect", "remote-benchmark", "--format",
            "{{json .Endpoints.docker.Host}}",
        )

    def test_accepts_a_local_unix_socket_without_context_lookup(self):
        with patch.dict(
            environ,
            {"DOCKER_HOST": "unix:///var/run/docker.sock"},
            clear=False,
        ):
            with patch.dict(environ, {"DOCKER_CONTEXT": ""}):
                with patch.object(benchmark, "docker") as docker_command:
                    self.assertEqual(
                        "unix:///var/run/docker.sock",
                        benchmark.require_local_docker_daemon(),
                    )

        docker_command.assert_not_called()

    def test_resolves_the_active_context_when_no_environment_override_exists(self):
        with patch.dict(environ, {"DOCKER_HOST": "", "DOCKER_CONTEXT": ""}):
            with patch.object(
                benchmark,
                "docker",
                side_effect=["default", json.dumps("unix:///var/run/docker.sock")],
            ) as docker_command:
                self.assertEqual(
                    "unix:///var/run/docker.sock",
                    benchmark.require_local_docker_daemon(),
                )

        self.assertEqual(
            [
                call("context", "show"),
                call(
                    "context", "inspect", "default", "--format",
                    "{{json .Endpoints.docker.Host}}",
                ),
            ],
            docker_command.call_args_list,
        )

    def test_main_rejects_remote_context_before_docker_or_host_counter_reads(self):
        args = Namespace(
            repeats=1,
            warmup_seconds=0,
            duration_seconds=1,
            sample_interval_seconds=1,
            profiles=["slskr"],
            live_session=False,
            login_timeout_seconds=1,
            credential_username_env="USER",
            credential_password_env="PASSWORD",
            output=Path("unused.json"),
        )
        with patch.object(benchmark, "parse_args", return_value=args):
            with patch.object(benchmark.platform, "system", return_value="Linux"):
                with patch.object(Path, "exists", return_value=True):
                    with patch.dict(
                        environ,
                        {"DOCKER_CONTEXT": "remote-benchmark"},
                        clear=False,
                    ):
                        with patch.object(
                            benchmark,
                            "docker",
                            return_value=json.dumps("tcp://remote:2376"),
                        ) as docker_command:
                            with patch.object(benchmark, "host_cpu_ticks") as cpu_ticks:
                                with self.assertRaisesRegex(
                                    RuntimeError, "local Docker daemon"
                                ):
                                    benchmark.main()

        docker_command.assert_called_once_with(
            "context", "inspect", "remote-benchmark", "--format",
            "{{json .Endpoints.docker.Host}}",
        )
        cpu_ticks.assert_not_called()


class ImageAvailabilityTests(unittest.TestCase):
    def test_pulls_selected_unique_images_before_inspecting_them(self):
        events = []

        def pull(*args, **kwargs):
            events.append(("pull", *args))
            return "pulled"

        def inspect(image):
            events.append(("inspect", image))
            return {"requested": image}

        with patch.object(benchmark, "docker", side_effect=pull):
            with patch.object(benchmark, "image_info", side_effect=inspect):
                metadata = benchmark.prepare_image_metadata(
                    ["slskr", "slskd", "slskr-dht"]
                )

        self.assertEqual(
            [
                ("pull", "pull", benchmark.IMAGES["slskr"]),
                ("pull", "pull", benchmark.IMAGES["slskd"]),
                ("inspect", benchmark.IMAGES["slskr"]),
                ("inspect", benchmark.IMAGES["slskd"]),
                ("inspect", benchmark.IMAGES["slskr-dht"]),
            ],
            events,
        )
        self.assertEqual(
            {app: {"requested": benchmark.IMAGES[app]} for app in benchmark.IMAGES},
            metadata,
        )


class ProcessMemoryCompletenessTests(unittest.TestCase):
    def test_reports_complete_rss_and_pss_totals(self):
        def read_text(path, *args, **kwargs):
            if str(path) == "/proc/123/status":
                return "Name:\tdaemon\nVmRSS:\t12 kB\n"
            if str(path) == "/proc/123/smaps_rollup":
                return "Pss: 9 kB\n"
            raise AssertionError(f"unexpected procfs path: {path}")

        with patch.object(benchmark, "docker", return_value="PID\n123\n"):
            with patch.object(Path, "read_text", autospec=True, side_effect=read_text):
                result = benchmark.process_memory("bench-container")

        self.assertEqual(12, result["rss_kib_sum"])
        self.assertTrue(result["rss_complete"])
        self.assertEqual(9, result["pss_kib_sum"])
        self.assertTrue(result["pss_complete"])

    def test_invalidates_rss_when_a_status_read_fails_but_keeps_available_pss(self):
        def read_text(path, *args, **kwargs):
            if str(path) == "/proc/123/status":
                raise PermissionError("status is not readable")
            if str(path) == "/proc/123/smaps_rollup":
                return "Pss: 24 kB\n"
            raise AssertionError(f"unexpected procfs path: {path}")

        with patch.object(benchmark, "docker", return_value="PID\n123\n"):
            with patch.object(Path, "read_text", autospec=True, side_effect=read_text):
                result = benchmark.process_memory("bench-container")

        self.assertEqual(1, result["process_count"])
        self.assertIsNone(result["rss_kib_sum"])
        self.assertFalse(result["rss_complete"])
        self.assertEqual(24, result["pss_kib_sum"])
        self.assertTrue(result["pss_complete"])

    def test_marks_rss_incomplete_when_status_has_no_vm_rss_row(self):
        def read_text(path, *args, **kwargs):
            if str(path) == "/proc/123/status":
                return "Name:\tdaemon\n"
            if str(path) == "/proc/123/smaps_rollup":
                return "Pss: 24 kB\n"
            raise AssertionError(f"unexpected procfs path: {path}")

        with patch.object(benchmark, "docker", return_value="PID\n123\n"):
            with patch.object(Path, "read_text", autospec=True, side_effect=read_text):
                result = benchmark.process_memory("bench-container")

        self.assertIsNone(result["rss_kib_sum"])
        self.assertFalse(result["rss_complete"])
        self.assertTrue(result["pss_complete"])


class FailedTrialPersistenceTests(unittest.TestCase):
    def test_persists_failed_trial_metadata_before_propagating(self):
        failures = (
            RuntimeError("login did not become authenticated before timeout"),
            OSError("cgroup memory.stat disappeared at a sample boundary"),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                with TemporaryDirectory() as directory:
                    output = Path(directory) / "run.json"
                    result = {"trials": []}
                    with patch.object(benchmark, "run_trial", side_effect=failure):
                        with self.assertRaises(type(failure)):
                            benchmark.run_recorded_trial(
                                result,
                                output,
                                "slskd",
                                2,
                                0,
                                60,
                                10,
                                live_session=True,
                                credentials=("test-user", "test-password"),
                                login_timeout=30,
                            )

                    saved_text = output.read_text()
                    saved = json.loads(saved_text)
                    self.assertEqual([], saved["trials"])
                    self.assertEqual(
                        {
                            "app": "slskd",
                            "repetition": 2,
                            "status": "failed",
                            "failure": {
                                "type": type(failure).__name__,
                                "reason": str(failure),
                            },
                        },
                        {
                            key: saved["attempts"][0][key]
                            for key in ("app", "repetition", "status", "failure")
                        },
                    )
                    self.assertTrue(saved["attempts"][0]["started_utc"])
                    self.assertTrue(saved["attempts"][0]["finished_utc"])
                    self.assertEqual("aborted", saved["run_status"])
                    self.assertNotIn("test-password", saved_text)

    def test_saves_completed_trial_and_attempt_together(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "run.json"
            result = {"trials": []}
            trial = {"app": "slskr", "cpu_seconds": 1.25}
            with patch.object(benchmark, "run_trial", return_value=trial):
                self.assertIs(
                    trial,
                    benchmark.run_recorded_trial(
                        result, output, "slskr", 1, 0, 1, 1
                    ),
                )

            saved = json.loads(output.read_text())
            self.assertEqual([trial], saved["trials"])
            self.assertEqual(
                {
                    "app": "slskr",
                    "repetition": 1,
                    "status": "completed",
                },
                {
                    key: saved["attempts"][0][key]
                    for key in ("app", "repetition", "status")
                },
            )
            self.assertTrue(saved["attempts"][0]["started_utc"])
            self.assertTrue(saved["attempts"][0]["finished_utc"])


class RunScopedApiCredentialTests(unittest.TestCase):
    def test_each_trial_gets_a_fresh_token_only_for_profiles_with_an_api(self):
        with patch.object(
            benchmark.secrets,
            "token_urlsafe",
            side_effect=["first-random-token", "second-random-token"],
        ) as token_factory:
            first = benchmark.fresh_api_credentials("slskr-dht", live_session=False)
            second = benchmark.fresh_api_credentials("slskr-dht", live_session=False)

        self.assertEqual(("first-random-token", None), first)
        self.assertEqual(("second-random-token", None), second)
        self.assertEqual(2, token_factory.call_count)
        self.assertIsNone(
            benchmark.fresh_api_credentials("slskr", live_session=False)[0]
        )
        self.assertIsNone(
            benchmark.fresh_api_credentials("slskd", live_session=False)[1]
        )

    def test_container_and_dht_status_request_use_the_same_token(self):
        api_token, _ = benchmark.fresh_api_credentials("slskr-dht", live_session=False)
        command = benchmark.run_command(
            "slskr-dht", "bench-container", api_token=api_token
        )

        self.assertIn("SLSKR_API_TOKEN", environment_values(command))
        self.assertNotIn(api_token, command)
        with patch.object(benchmark, "local_api_json", return_value={}) as request:
            benchmark.dht_runtime_status("bench-container", api_token)

        request.assert_called_once_with(
            "bench-container",
            "/api/dht/status",
            ("Authorization", f"Bearer {api_token}"),
        )

    def test_slskd_live_status_uses_the_same_read_only_per_run_key(self):
        _, api_key = benchmark.fresh_api_credentials("slskd", live_session=True)
        command = benchmark.run_command(
            "slskd", "bench-container", live_session=True, slskd_api_key=api_key
        )

        self.assertIn("SLSKD_API_KEY", environment_values(command))
        self.assertNotIn(api_key, command)
        with patch.object(
            benchmark,
            "local_api_json",
            return_value={"isLoggedIn": True},
        ) as request:
            benchmark.soulseek_runtime_status(
                "bench-container", "slskd", slskd_api_key=api_key
            )

        request.assert_called_once_with(
            "bench-container",
            "/api/v0/server",
            ("X-API-Key", api_key),
        )

    def test_exposed_status_apis_require_a_per_run_credential(self):
        with self.assertRaisesRegex(ValueError, "per-run slskR API token"):
            benchmark.run_command("slskr-dht", "bench-container")
        with self.assertRaisesRegex(ValueError, "per-run API key"):
            benchmark.run_command("slskd", "bench-container", live_session=True)


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
            credential = (
                {"api_token": "test-run-token"}
                if profile in ("slskr", "slskr-dht")
                else {"slskd_api_key": "test-run-api-key"}
            )
            command = benchmark.run_command(
                profile, "test", live_session=True, **credential
            )
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

    def test_retained_dht_only_artifact_matches_its_profile_network(self):
        artifact_path = SCRIPT.parent / "artifacts/20261012-idle-container-slskr-dht.json"
        artifact = json.loads(artifact_path.read_text())
        parameters = artifact["parameters"]

        self.assertEqual(
            benchmark.network_metadata(parameters["profiles"], live_session=False),
            {
                "network": parameters["network"],
                "network_by_profile": parameters["network_by_profile"],
            },
        )


class BenchmarkReportIntegrityTests(unittest.TestCase):
    def test_retained_host_cpu_percentages_are_labeled_as_legacy(self):
        artifacts = SCRIPT.parent / "artifacts"
        for report_path in (
            artifacts / "20261012-idle-container-slskr-slskd.md",
            artifacts / "20261012-live-soulseek-idle.md",
        ):
            report = report_path.read_text()
            self.assertIn("guest and `guest_nice` ticks", report)
            self.assertIn("individual host tick deltas", report)
            self.assertIn("may be overstated", report)
            self.assertIn("reruns use the corrected accounting", report)

    def test_dht_artifact_checksum_matches_report(self):
        artifacts = SCRIPT.parent / "artifacts"
        artifact_path = artifacts / "20261012-idle-container-slskr-dht.json"
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        report = (artifacts / "20261012-idle-container-slskr-slskd.md").read_text()

        self.assertIn(f"`{digest}`", report)

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
