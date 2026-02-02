"""
External plugin module.

This is from a third package that should also be analyzed.
"""


class PluginInterface:
    """Base interface for plugins."""

    def initialize(self) -> bool:
        """Initialize the plugin.

        Returns:
            True if successful
        """
        raise NotImplementedError("Subclasses must implement initialize()")

    def execute(self, context: dict) -> dict:
        """Execute plugin logic.

        Args:
            context: Execution context

        Returns:
            Result data
        """
        raise NotImplementedError("Subclasses must implement execute()")


class DataPlugin(PluginInterface):
    """Plugin for data processing."""

    def __init__(self, name: str):
        """Initialize data plugin.

        Args:
            name: Plugin name
        """
        self.name = name
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize the plugin."""
        self.initialized = True
        return True

    def execute(self, context: dict) -> dict:
        """Execute data processing.

        Args:
            context: Execution context with 'data' key

        Returns:
            Processed result
        """
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")

        data = context.get("data", {})
        return {
            "plugin": self.name,
            "result": f"Processed: {data}"
        }
