"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic health check response."""

    status: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with dependency status."""

    status: str = Field(..., description="Overall health status: healthy or unhealthy")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current server timestamp")
    checks: dict[str, str] = Field(..., description="Individual health check results")


class DebugInfo(BaseModel):
    """Debug information about application state."""

    system: dict[str, Any] = Field(..., description="System information")
    state: dict[str, Any] = Field(..., description="Application state")
    config: dict[str, Any] = Field(..., description="Configuration (sanitized)")


class TVDevice(BaseModel):
    """Samsung TV device details."""

    EdgeBlendingSupport: str
    EdgeBlendingSupportGroup: str
    FrameTVSupport: str
    GamePadSupport: str
    ImeSyncedSupport: str
    Language: str
    OS: str
    PowerState: str
    TokenAuthSupport: str
    VoiceSupport: str
    WallScreenRatio: str
    WallService: str
    countryCode: str
    description: str
    developerIP: str
    developerMode: str
    duid: str
    firmwareVersion: str
    id: str
    ip: str
    model: str
    modelName: str
    mouseWheelSupport: str
    name: str
    networkType: str
    resolution: str
    smartHubAgreement: str
    ssid: str
    type: str
    udn: str
    wifiMac: str


class TVInfo(BaseModel):
    """Samsung TV device information from REST API."""

    device: TVDevice = Field(..., description="Device information and capabilities")
    id: str = Field(..., description="Device UUID")
    isSupport: str = Field(..., description="Supported features as JSON string")
    name: str = Field(..., description="Device name")
    remote: str = Field(..., description="Remote API version")
    type: str = Field(..., description="Device type")
    uri: str = Field(..., description="API URI")
    version: str = Field(..., description="API version")

    @property
    def power_state(self) -> str:
        """Get TV power state from device info.

        Returns:
            'on', 'standby', or 'unknown'
        """
        return self.device.PowerState.lower()

    @property
    def model_name(self) -> str:
        """Get TV model name.

        Returns:
            Model name
        """
        return self.device.modelName

    @property
    def resolution(self) -> str:
        """Get TV resolution.

        Returns:
            Resolution (e.g., '3840x2160')
        """
        return self.device.resolution

    requests: dict[str, int] = Field(..., description="Request statistics")
