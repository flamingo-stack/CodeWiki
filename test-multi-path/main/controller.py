"""
Controller component for handling API requests.
"""

from service import MainService


class APIController:
    """API Controller for routing requests."""

    def __init__(self):
        """Initialize the controller."""
        self.service = MainService("api-service")
        self.request_count = 0

    def handle_request(self, endpoint: str, data: dict) -> dict:
        """Handle API request.

        Args:
            endpoint: API endpoint path
            data: Request data

        Returns:
            Response data
        """
        self.request_count += 1

        if endpoint == "/process":
            return self.service.process_request(data)
        elif endpoint == "/health":
            return {"status": "healthy", "requests": self.request_count}
        else:
            return {"error": "Unknown endpoint"}
