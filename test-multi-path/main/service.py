"""
Main service component.

This is the primary service that uses helper utilities from the deps package.
"""

from deps.helper import process_data, validate_input


class MainService:
    """Main service class for the application."""

    def __init__(self, name: str):
        """Initialize the service.

        Args:
            name: Service name
        """
        self.name = name
        self.active = False

    def start(self, config: dict) -> bool:
        """Start the service with configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if started successfully
        """
        if not validate_input(config):
            return False

        self.active = True
        return True

    def process_request(self, data: dict) -> dict:
        """Process incoming request data.

        Args:
            data: Request data to process

        Returns:
            Processed response data
        """
        if not self.active:
            raise RuntimeError("Service not started")

        # Use helper from deps package
        processed = process_data(data)

        return {
            "status": "success",
            "service": self.name,
            "result": processed
        }

    def stop(self):
        """Stop the service."""
        self.active = False
