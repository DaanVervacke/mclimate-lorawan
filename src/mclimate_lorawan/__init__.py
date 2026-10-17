"""MClimate device models for ChirpStack and The Things Stack."""

from lorawan_connection import DeviceCollection

from .device import MClimateDevice
from .models import (
    VENDOR_ID,
    FanCoilThermostat,
    Melissa,
    Thermostat,
    TValve,
    Vicki,
    WirelessThermostat,
)
from .payload import DecodedPayload, Measurement


def decode_vicki_keepalive(data: bytes) -> dict[str, float | bool | int | str]:
    """Decode a Vicki keepalive into a plain dictionary."""
    result: dict[str, float | bool | int | str] = {}
    value: float | bool | int | str
    for item in Vicki.decode(data).measurements:
        if item.value is not None:
            if isinstance(item.value, (float, bool, int, str)):
                value = item.value
                result[item.name] = value
    return result


class MClimateDeviceCollection(DeviceCollection[MClimateDevice]):
    """Discover MClimate devices using official catalog identities."""

    DEVICES = (
        Vicki,
        TValve,
        WirelessThermostat,
        FanCoilThermostat,
    )


__all__ = [
    "VENDOR_ID",
    "DecodedPayload",
    "FanCoilThermostat",
    "Measurement",
    "Melissa",
    "MClimateDevice",
    "MClimateDeviceCollection",
    "TValve",
    "Thermostat",
    "Vicki",
    "WirelessThermostat",
    "decode_vicki_keepalive",
]
