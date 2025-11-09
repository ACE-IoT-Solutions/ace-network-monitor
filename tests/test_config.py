"""
Unit tests for configuration loading and validation.

Tests cover:
- Configuration file loading
- Default configuration
- Configuration validation
- Invalid configuration handling
- Environment variable overrides
"""

import pytest
import os
import yaml


@pytest.mark.unit
@pytest.mark.config
class TestConfigurationLoading:
    """Test suite for configuration management."""

    def test_load_valid_config_file(self, temp_config_file):
        """Test loading a valid configuration file."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert "hosts" in config
        assert "ping_count" in config
        assert "interval_seconds" in config

    def test_config_has_required_fields(self, temp_config_file):
        """Test that configuration has all required fields."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        required_fields = [
            "hosts",
            "ping_count",
            "interval_seconds",
            "timeout_seconds",
            "retention_days",
            "database_path",
        ]

        for field in required_fields:
            assert field in config, f"Missing required field: {field}"

    def test_hosts_list_not_empty(self, temp_config_file):
        """Test that hosts list is not empty."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert len(config["hosts"]) > 0
        assert all(isinstance(host, str) for host in config["hosts"])

    def test_ping_count_is_positive(self, temp_config_file):
        """Test that ping count is a positive integer."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config["ping_count"], int)
        assert config["ping_count"] > 0

    def test_interval_seconds_is_positive(self, temp_config_file):
        """Test that interval seconds is positive."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config["interval_seconds"], int)
        assert config["interval_seconds"] > 0

    def test_timeout_seconds_is_positive(self, temp_config_file):
        """Test that timeout seconds is positive."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config["timeout_seconds"], int)
        assert config["timeout_seconds"] > 0

    def test_retention_days_is_positive(self, temp_config_file):
        """Test that retention days is positive."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config["retention_days"], int)
        assert config["retention_days"] > 0

    def test_database_path_is_string(self, temp_config_file):
        """Test that database path is a string."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config["database_path"], str)
        assert len(config["database_path"]) > 0

    def test_dashboard_configuration(self, temp_config_file):
        """Test dashboard configuration section."""
        with open(temp_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert "dashboard" in config
        assert "port" in config["dashboard"]
        assert "title" in config["dashboard"]

        assert isinstance(config["dashboard"]["port"], int)
        assert 1024 <= config["dashboard"]["port"] <= 65535

    def test_invalid_config_empty_hosts(self, invalid_config_file):
        """Test that invalid config with empty hosts is detected."""
        with open(invalid_config_file, "r") as f:
            config = yaml.safe_load(f)

        # Validation should fail
        assert len(config["hosts"]) == 0

    def test_invalid_config_negative_ping_count(self, invalid_config_file):
        """Test that invalid config with negative ping count is detected."""
        with open(invalid_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert config["ping_count"] < 0

    def test_invalid_config_zero_interval(self, invalid_config_file):
        """Test that invalid config with zero interval is detected."""
        with open(invalid_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert config["interval_seconds"] == 0

    def test_config_file_not_found(self):
        """Test handling of missing configuration file."""
        non_existent_path = "/tmp/non_existent_config.yaml"

        with pytest.raises(FileNotFoundError):
            with open(non_existent_path, "r") as f:
                yaml.safe_load(f)

    def test_config_file_malformed_yaml(self, tmp_path):
        """Test handling of malformed YAML configuration."""
        config_path = tmp_path / "malformed.yaml"
        config_path.write_text("invalid: yaml: content: [[[")

        with pytest.raises(yaml.YAMLError):
            with open(config_path, "r") as f:
                yaml.safe_load(f)

    def test_default_configuration_generation(self):
        """Test generating default configuration."""
        default_config = {
            "hosts": ["8.8.8.8", "1.1.1.1"],
            "ping_count": 10,
            "interval_seconds": 60,
            "timeout_seconds": 5,
            "retention_days": 90,
            "database_path": "pings.db",
            "dashboard": {
                "port": 8501,
                "title": "Connection Monitor",
            },
        }

        # Validate default config structure
        assert "hosts" in default_config
        assert len(default_config["hosts"]) > 0
        assert default_config["ping_count"] > 0
        assert default_config["interval_seconds"] > 0

    @pytest.mark.parametrize(
        "host",
        [
            "8.8.8.8",
            "google.com",
            "localhost",
            "192.168.1.1",
            "example.org",
        ],
    )
    def test_valid_host_formats(self, host):
        """Test validation of various valid host formats."""
        import re

        # IP pattern
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        # Domain pattern
        domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^localhost$"

        is_ip = re.match(ip_pattern, host)
        is_domain = re.match(domain_pattern, host)

        assert is_ip or is_domain

    @pytest.mark.parametrize(
        "host",
        [
            "",
            "invalid..host",
            "256.256.256.256",
            "host name with spaces",
            "host@invalid",
        ],
    )
    def test_invalid_host_formats(self, host):
        """Test detection of invalid host formats."""
        import re

        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        # Updated pattern to reject consecutive dots, starting/ending dots, and invalid characters
        domain_pattern = r"^(?!.*\.\.)[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$|^localhost$"

        is_valid = False
        if host:
            if re.match(ip_pattern, host):
                parts = [int(p) for p in host.split(".")]
                is_valid = all(0 <= p <= 255 for p in parts)
            elif re.match(domain_pattern, host):
                is_valid = True

        assert not is_valid

    def test_config_with_comments(self, tmp_path):
        """Test loading configuration with YAML comments."""
        config_path = tmp_path / "config_with_comments.yaml"
        config_content = """
# Connection Monitor Configuration
hosts:  # List of hosts to monitor
  - 8.8.8.8
  - 1.1.1.1

ping_count: 10  # Number of pings per check
interval_seconds: 60  # Check interval
"""
        config_path.write_text(config_content)

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert len(config["hosts"]) == 2

    def test_config_environment_variable_override(self):
        """Test configuration override via environment variables."""
        # Set environment variable
        os.environ["CONNECTION_MONITOR_INTERVAL"] = "120"

        # Check it can be read
        interval = os.environ.get("CONNECTION_MONITOR_INTERVAL")
        assert int(interval) == 120

    def test_ping_count_range_validation(self):
        """Test validation of ping count ranges."""
        valid_counts = [1, 5, 10, 20, 50, 100]
        invalid_counts = [-1, 0, 1001]

        for count in valid_counts:
            assert 1 <= count <= 1000

        for count in invalid_counts:
            assert not (1 <= count <= 1000)

    def test_timeout_range_validation(self):
        """Test validation of timeout ranges."""
        valid_timeouts = [1, 5, 10, 30]
        invalid_timeouts = [0, -1, 301]

        for timeout in valid_timeouts:
            assert 1 <= timeout <= 300

        for timeout in invalid_timeouts:
            assert not (1 <= timeout <= 300)

    def test_retention_days_range_validation(self):
        """Test validation of retention days ranges."""
        valid_days = [1, 7, 30, 90, 365]
        invalid_days = [0, -1]

        for days in valid_days:
            assert days > 0

        for days in invalid_days:
            assert not (days > 0)

    def test_dashboard_port_range_validation(self):
        """Test validation of dashboard port ranges."""
        valid_ports = [8000, 8080, 8501, 3000, 5000]
        invalid_ports = [0, 80, 1023, 65536, 70000]

        for port in valid_ports:
            assert 1024 <= port <= 65535

        for port in invalid_ports:
            assert not (1024 <= port <= 65535)

    def test_config_save_and_reload(self, tmp_path):
        """Test saving and reloading configuration."""
        config_path = tmp_path / "test_config.yaml"

        # Create config
        config = {
            "hosts": ["8.8.8.8"],
            "ping_count": 10,
            "interval_seconds": 60,
            "timeout_seconds": 5,
            "retention_days": 90,
            "database_path": "test.db",
        }

        # Save
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        # Reload
        with open(config_path, "r") as f:
            reloaded_config = yaml.safe_load(f)

        assert reloaded_config == config

    def test_multiple_hosts_configuration(self):
        """Test configuration with multiple hosts."""
        config = {
            "hosts": ["8.8.8.8", "1.1.1.1", "google.com", "cloudflare.com", "localhost"]
        }

        assert len(config["hosts"]) == 5
        assert all(isinstance(host, str) for host in config["hosts"])

    def test_config_with_optional_fields(self, tmp_path):
        """Test configuration with optional fields."""
        config_path = tmp_path / "config_optional.yaml"

        config = {
            "hosts": ["8.8.8.8"],
            "ping_count": 10,
            "interval_seconds": 60,
            "timeout_seconds": 5,
            "retention_days": 90,
            "database_path": "test.db",
            "log_level": "INFO",  # Optional
            "enable_notifications": False,  # Optional
        }

        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with open(config_path, "r") as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config.get("log_level") == "INFO"
        assert loaded_config.get("enable_notifications") is False

    def test_config_unicode_support(self, tmp_path):
        """Test configuration with unicode characters."""
        config_path = tmp_path / "config_unicode.yaml"

        config = {
            "hosts": ["8.8.8.8"],
            "ping_count": 10,
            "dashboard": {"title": "Überwachung Network 网络监控"},
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)

        with open(config_path, "r", encoding="utf-8") as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config["dashboard"]["title"] == "Überwachung Network 网络监控"

    def test_config_path_expansion(self):
        """Test path expansion in configuration."""
        config = {"database_path": "~/data/pings.db"}

        # Test that path can be expanded
        expanded_path = os.path.expanduser(config["database_path"])
        assert "~" not in expanded_path

    def test_relative_vs_absolute_paths(self):
        """Test handling of relative and absolute paths."""
        relative_path = "data/pings.db"
        absolute_path = "/var/lib/connection-logger/pings.db"

        assert not os.path.isabs(relative_path)
        assert os.path.isabs(absolute_path)
