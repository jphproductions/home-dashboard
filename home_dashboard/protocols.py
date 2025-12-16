"""Protocol definitions for dependency injection."""

from typing import Protocol

from home_dashboard.config import Settings
from home_dashboard.state_managers import TVStateManager


class TVServiceProtocol(Protocol):
    """Protocol for TV control services.

    This protocol defines the interface for TV control services,
    allowing for dependency injection and easier testing.
    """

    async def wake(
        self,
        settings: Settings | None = None,
        tv_manager: TVStateManager | None = None,
    ) -> str:
        """Wake the TV.

        Args:
            settings: Application settings
            tv_manager: TV state manager for tracking failures

        Returns:
            Status message
        """
        ...
