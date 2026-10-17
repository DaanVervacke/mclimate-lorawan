"""MClimate models and official ChirpStack/TTS catalog identities."""

from typing import ClassVar

from .decoders import (
    decode_fan_coil_thermostat,
    decode_melissa,
    decode_t_valve,
    decode_thermostat,
    decode_vicki,
    decode_wireless_thermostat,
)
from .device import Decoder, MClimateDevice

VENDOR_ID = 824


class Vicki(MClimateDevice):
    """Smart radiator thermostat with motor-driven valve."""

    identifiers = {
        "chirpstack": (VENDOR_ID, "c521e66f-5745-45a0-b483-00fe1db8eaac"),
        "tts": ("mclimate", "vicki"),
    }
    _decoder: ClassVar[Decoder] = decode_vicki
    _ports = (1,)

    @property
    def target_temperature(self) -> float | None:
        """Target temperature in degrees Celsius."""
        return self._number("target_temperature")

    @property
    def relative_humidity(self) -> float | None:
        """Relative humidity in percent."""
        return self._number("relative_humidity")

    @property
    def battery_voltage(self) -> float | None:
        """Battery voltage in volts."""
        return self._number("battery_voltage")

    @property
    def valve_openness(self) -> float | None:
        """Valve openness in percent."""
        return self._number("valve_openness")

    @property
    def child_lock(self) -> bool | None:
        """Whether the child lock is active."""
        value = self.measurement_value("child_lock")
        return value if isinstance(value, bool) else None


class TValve(MClimateDevice):
    """Motorized valve with flood detection for water metering."""

    identifiers = {
        "tts": ("mclimate", "t-valve"),
    }
    _decoder: ClassVar[Decoder] = decode_t_valve
    _ports = (2,)

    @property
    def water_temperature(self) -> float | None:
        """Water temperature in degrees Celsius."""
        return self._number("water_temperature")

    @property
    def ambient_temperature(self) -> float | None:
        """Ambient temperature in degrees Celsius."""
        return self._number("ambient_temperature")

    @property
    def valve_state(self) -> bool | None:
        """Whether the valve is open."""
        value = self.measurement_value("valve_state")
        return value if isinstance(value, bool) else None

    @property
    def battery(self) -> float | None:
        """Battery voltage in volts."""
        return self._number("battery")


class WirelessThermostat(MClimateDevice):
    """Battery-powered thermostat with temperature, humidity, and PIR."""

    identifiers = {
        "tts": ("mclimate", "wireless-thermostat"),
    }
    _decoder: ClassVar[Decoder] = decode_wireless_thermostat
    _ports = (2,)

    @property
    def target_temperature(self) -> float | None:
        """Target temperature in degrees Celsius."""
        return self._number("target_temperature")

    @property
    def relative_humidity(self) -> float | None:
        """Relative humidity in percent."""
        return self._number("relative_humidity")

    @property
    def battery_voltage(self) -> float | None:
        """Battery voltage in volts."""
        return self._number("battery_voltage")

    @property
    def illuminance(self) -> float | None:
        """Light intensity in lux."""
        return self._number("lux")


class FanCoilThermostat(MClimateDevice):
    """Fan coil thermostat with fan speed and valve control."""

    identifiers = {
        "tts": ("mclimate", "fan-coil-thermostat"),
    }
    _decoder: ClassVar[Decoder] = decode_fan_coil_thermostat
    _ports = (2,)

    @property
    def target_temperature(self) -> float | None:
        """Target temperature in degrees Celsius."""
        return self._number("target_temperature")

    @property
    def relative_humidity(self) -> float | None:
        """Relative humidity in percent."""
        return self._number("relative_humidity")

    @property
    def operational_mode(self) -> int | None:
        """Operational mode code."""
        value = self.measurement_value("operational_mode")
        return value if isinstance(value, int) else None


class Melissa(MClimateDevice):
    """IR thermostat controller with temperature, humidity, and PIR."""

    identifiers = {}
    _decoder: ClassVar[Decoder] = decode_melissa
    _ports = (1, 2)

    @property
    def relative_humidity(self) -> float | None:
        """Relative humidity in percent."""
        return self._number("relative_humidity")

    @property
    def battery_voltage(self) -> float | None:
        """Supply voltage in volts."""
        return self._number("battery_voltage")

    @property
    def illuminance(self) -> float | None:
        """Light intensity in lux."""
        return self._number("lux")


class Thermostat(MClimateDevice):
    """LoRaWAN room thermostat with relay status."""

    identifiers = {}
    _decoder: ClassVar[Decoder] = decode_thermostat
    _ports = (1, 2)

    @property
    def temperature(self) -> float | None:
        """Current temperature in degrees Celsius."""
        return self._number("temperature")

    @property
    def target_temperature(self) -> float | None:
        """Target temperature in degrees Celsius."""
        return self._number("target_temperature")

    @property
    def battery_status(self) -> int | None:
        """Battery charge in percent."""
        value = self.measurement_value("battery_status")
        return value if isinstance(value, int) else None

    @property
    def relay_status(self) -> bool | None:
        """Whether the relay is energized."""
        value = self.measurement_value("relay_status")
        return value if isinstance(value, bool) else None
