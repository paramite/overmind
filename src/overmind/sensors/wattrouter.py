"""Wattrouter device interface for configuration control."""

from typing import Dict, Optional
from xml.etree import ElementTree as ET

import requests


class WattrouterClient:
    """Client for communicating with Wattrouter device to control heating."""

    def __init__(self, base_url: str, username: str = "admin", password: str = "",
                 output_id: str = "O5"):
        """
        Initialize Wattrouter client.

        Args:
            base_url: Base URL of Wattrouter device (e.g., http://192.168.1.1)
            username: Authentication username
            password: Authentication password
            output_id: Output ID controlling the boiler (default: O5 - Bojler)
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.output_id = output_id
        self.session = requests.Session()

        if username and password:
            self.session.auth = (username, password)

    def get_measurements(self) -> Dict[str, float]:
        """
        Fetch current measurements from Wattrouter.

        Returns:
            Dictionary with measurement values

        Raises:
            requests.RequestException: On communication error
        """
        url = f"{self.base_url}/meas.xml"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        return self._parse_measurements(response.text)

    def get_configuration(self) -> Dict[str, any]:
        """
        Fetch configuration from Wattrouter.

        Returns:
            Dictionary with configuration values

        Raises:
            requests.RequestException: On communication error
        """
        url = f"{self.base_url}/conf_get.xml"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        return self._parse_configuration(response.text)

    def set_configuration(self, config: Dict[str, any]) -> bool:
        """
        Update Wattrouter configuration.

        Args:
            config: Configuration dictionary to send

        Returns:
            True if successful

        Raises:
            requests.RequestException: On communication error
        """
        url = f"{self.base_url}/conf_post.xml"
        xml_data = self._build_configuration_xml(config)

        response = self.session.post(url, data=xml_data, timeout=10)
        response.raise_for_status()

        return response.status_code == 200

    def _parse_measurements(self, xml_text: str) -> Dict[str, float]:
        """Parse XML measurement response."""
        root = ET.fromstring(xml_text)
        measurements = {}

        # Parse XML structure - adapt based on actual Wattrouter XML format
        for elem in root.iter():
            if elem.text and elem.tag not in ["root", "meas"]:
                try:
                    measurements[elem.tag] = float(elem.text)
                except (ValueError, TypeError):
                    measurements[elem.tag] = elem.text

        return measurements

    def _parse_configuration(self, xml_text: str) -> Dict[str, any]:
        """Parse XML configuration response."""
        root = ET.fromstring(xml_text)
        config = {}

        for elem in root.iter():
            if elem.text and elem.tag not in ["root", "conf"]:
                try:
                    config[elem.tag] = float(elem.text)
                except (ValueError, TypeError):
                    config[elem.tag] = elem.text

        return config

    def _build_configuration_xml(self, config: Dict[str, any]) -> str:
        """Build XML configuration request."""
        root = ET.Element("conf")

        for key, value in config.items():
            elem = ET.SubElement(root, key)
            elem.text = str(value)

        return ET.tostring(root, encoding="unicode")

    def get_output_power(self, output_id: Optional[str] = None) -> Optional[float]:
        """
        Get current power for specific output.

        Args:
            output_id: Output identifier (e.g., 'O5'), uses self.output_id if None

        Returns:
            Power in kW or None if not available
        """
        output_id = output_id or self.output_id
        measurements = self.get_measurements()

        # Navigate to output data: measurements[output_id]['P']
        output_data = measurements.get(output_id, {})
        if isinstance(output_data, dict):
            power_str = output_data.get("P")
            if power_str:
                try:
                    return float(power_str)
                except ValueError:
                    return None
        return None

    def is_heating_enabled(self) -> bool:
        """
        Check if heating output is currently enabled.

        Returns:
            True if heating is enabled, False otherwise
        """
        try:
            config = self.get_configuration()
            output_config = config.get(self.output_id, {})

            # Check if output is active (M=0 means auto mode)
            if isinstance(output_config, dict):
                # Priority > 0 means output can receive power
                priority = output_config.get("Pr", "0")
                try:
                    return int(priority) > 0
                except (ValueError, TypeError):
                    return False

            return False
        except requests.RequestException:
            return False

    def enable_heating(self) -> bool:
        """
        Enable heating by setting output priority.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Set priority to enable heating (Pr=1 or higher)
            config = {self.output_id: {"Pr": "1"}}
            return self.set_configuration(config)
        except requests.RequestException:
            return False

    def disable_heating(self) -> bool:
        """
        Disable heating by setting output priority to 0.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Set priority to 0 to disable heating
            config = {self.output_id: {"Pr": "0"}}
            return self.set_configuration(config)
        except requests.RequestException:
            return False

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"WattrouterClient(base_url={self.base_url}, output={self.output_id})"
