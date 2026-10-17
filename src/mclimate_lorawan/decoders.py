"""Keepalive decoders for the MClimate thermostatic device families.

Every decoder is ported from MClimate's upstream TypeScript parsers
(mclimate-payload-helper, src/decoders/payloadParsers) and verified
against their Jest test vectors. Malformed frames raise ValueError.
Uplinks that answer a downlink command carry a keepalive at the end;
the command-response prefix is ignored per the keepalive-only scope.
"""

import math

from .payload import DecodedPayload, Measurement

_KEEPALIVE_VICKI = 9
_KEEPALIVE_WIRELESS_THERMOSTAT = 11
_KEEPALIVE_WIRELESS_THERMOSTAT_EXT = 12
_KEEPALIVE_FAN_COIL = 11
_KEEPALIVE_MELISSA = 10
_KEEPALIVE_THERMOSTAT = 7


def _round(value: float, digits: int) -> float:
    """Round half away from zero, matching the upstream toFixed output."""
    scale = 10**digits
    sign: float = 1.0 if value >= 0 else -1.0
    scaled: float = math.floor(abs(value) * scale + 0.5) / scale
    return sign * scaled


def _tail_keepalive(data: bytes, length: int) -> bytes:
    """Extract the keepalive appended after a command-response prefix."""
    if len(data) < length:
        raise ValueError(f"Keepalive requires {length} bytes, got {len(data)}")
    return data[-length:]


def decode_vicki(data: bytes) -> DecodedPayload:
    """Decode a Vicki keepalive, ignoring any command-response prefix."""
    if data[0] not in (0x01, 0x81):
        data = _tail_keepalive(data, _KEEPALIVE_VICKI)
    elif len(data) != _KEEPALIVE_VICKI:
        raise ValueError(f"Vicki keepalive requires 9 bytes, got {len(data)}")
    reason = data[0]
    if reason == 0x01:
        sensor_temperature = (data[2] * 165) / 256 - 40
    else:
        sensor_temperature = (data[2] - 28.33333) / 5.66666
    motor_range = ((data[6] & 0x0F) << 8) | data[5]
    motor_position = (data[6] >> 4) << 8 | data[4]
    battery_voltage = 2 + (data[7] >> 4) * 0.1
    valve_openness = (
        int((1 - motor_position / motor_range) * 100 + 0.5) if motor_range else 0
    )
    return DecodedPayload(
        measurements=[
            Measurement("reason", reason),
            Measurement("target_temperature", data[1]),
            Measurement("sensor_temperature", sensor_temperature),
            Measurement("relative_humidity", (data[3] * 100) / 256),
            Measurement("motor_range", motor_range),
            Measurement("motor_position", motor_position),
            Measurement("battery_voltage", battery_voltage),
            Measurement("open_window", bool(data[7] & 0x08)),
            Measurement("high_motor_consumption", bool(data[7] & 0x04)),
            Measurement("low_motor_consumption", bool(data[7] & 0x02)),
            Measurement("broken_sensor", bool(data[7] & 0x01)),
            Measurement("child_lock", bool(data[8] & 0x80)),
            Measurement("calibration_failed", bool(data[8] & 0x40)),
            Measurement("attached_backplate", bool(data[8] & 0x20)),
            Measurement("perceive_as_online", bool(data[8] & 0x10)),
            Measurement("anti_freeze_protection", bool(data[8] & 0x08)),
            Measurement("d2d_communication_reliable", bool(data[8] & 0x04)),
            Measurement("battery_too_low", bool(data[8] & 0x02)),
            Measurement("valve_openness", valve_openness),
        ]
    )


def decode_t_valve(data: bytes) -> DecodedPayload:
    """Decode a T-Valve keepalive: short (2 bytes) or long (5 bytes).

    Long frames carry the keepalive in the first five bytes; any command
    answer appended after it is ignored.
    """
    if len(data) == 2:
        return DecodedPayload(
            measurements=[
                Measurement("reason", "keepalive"),
                Measurement("water_temperature", data[0] / 2),
                Measurement("valve_state", bool(data[1] & 0x80)),
                Measurement("ambient_temperature", ((data[1] & 0x7F) - 20) / 2),
            ]
        )
    if len(data) < 5:
        raise ValueError(f"T-Valve keepalive requires 2 or 5 bytes, got {len(data)}")
    data = data[:5]
    reasons = (
        "keepalive",
        "test_button_pressed",
        "flood_detected",
        "control_button_pressed",
        "fraud_detected",
    )
    reason = (data[0] >> 5) & 0x07
    if reason >= len(reasons):
        raise ValueError(f"T-Valve keepalive reason {reason} out of range")
    return DecodedPayload(
        measurements=[
            Measurement("reason", reasons[reason]),
            Measurement("battery_too_low", bool(data[0] & 0x10)),
            Measurement("box_tamper", bool(data[0] & 0x08)),
            Measurement("flood_detection_wire_state", bool(data[0] & 0x04)),
            Measurement("flood", bool(data[0] & 0x02)),
            Measurement("magnet", bool(data[0] & 0x01)),
            Measurement("alarm_validated", bool(data[1] & 0x80)),
            Measurement("manual_open_indicator", bool(data[1] & 0x40)),
            Measurement("manual_close_indicator", bool(data[1] & 0x20)),
            Measurement("close_time", data[2]),
            Measurement("open_time", data[3]),
            Measurement("battery", (data[4] * 8 + 1600) / 1000),
        ],
        metadata={"software_version": data[1] & 0x1F},
    )


def decode_wireless_thermostat(data: bytes) -> DecodedPayload:
    """Decode a Wireless Thermostat keepalive, ignoring command answers."""
    expected = (
        _KEEPALIVE_WIRELESS_THERMOSTAT_EXT
        if data[0] == 0x81
        else _KEEPALIVE_WIRELESS_THERMOSTAT
    )
    if data[0] in (0x01, 0x81):
        keepalive = _tail_keepalive(data, expected)
    else:
        keepalive = _tail_keepalive(
            data,
            _KEEPALIVE_WIRELESS_THERMOSTAT_EXT
            if data[-_KEEPALIVE_WIRELESS_THERMOSTAT_EXT] == 0x81
            else _KEEPALIVE_WIRELESS_THERMOSTAT,
        )
    temperature = ((keepalive[1] << 8 | keepalive[2]) - 400) / 10
    humidity = (keepalive[3] * 100) / 256
    battery_voltage = (keepalive[4] << 8 | keepalive[5]) / 1000
    if keepalive[0] == 0x01:
        target_temperature: float = float(keepalive[6])
        power_source_status = keepalive[7]
        lux = keepalive[8] << 8 | keepalive[9]
        pir = bool(keepalive[10])
    else:
        target_temperature = (keepalive[6] << 8 | keepalive[7]) / 10
        power_source_status = keepalive[8]
        lux = keepalive[9] << 8 | keepalive[10]
        pir = bool(keepalive[11])
    return DecodedPayload(
        measurements=[
            Measurement("target_temperature", target_temperature),
            Measurement("sensor_temperature", _round(temperature, 2)),
            Measurement("relative_humidity", _round(humidity, 2)),
            Measurement("battery_voltage", _round(battery_voltage, 2)),
            Measurement("power_source_status", power_source_status),
            Measurement("lux", lux),
            Measurement("pir", pir),
        ]
    )


def decode_fan_coil_thermostat(data: bytes) -> DecodedPayload:
    """Decode a Fan Coil Thermostat keepalive, ignoring command answers."""
    if data[0] == 0x01:
        keepalive = data
    else:
        keepalive = _tail_keepalive(data, _KEEPALIVE_FAN_COIL)
    temperature = ((keepalive[1] << 8 | keepalive[2]) - 400) / 10
    humidity = (keepalive[3] * 100) / 256
    return DecodedPayload(
        measurements=[
            Measurement("sensor_temperature", _round(temperature, 2)),
            Measurement("relative_humidity", _round(humidity, 2)),
            Measurement(
                "target_temperature",
                (keepalive[4] << 8 | keepalive[5]) / 10,
            ),
            Measurement("operational_mode", keepalive[6]),
            Measurement("displayed_fan_speed", keepalive[7]),
            Measurement("actual_fan_speed", keepalive[8]),
            Measurement("valve_status", keepalive[9]),
            Measurement("device_status", keepalive[10]),
        ]
    )


def decode_melissa(data: bytes) -> DecodedPayload:
    """Decode a Melissa LoRaWAN keepalive, ignoring command answers."""
    if data[0] == 0x01:
        keepalive = data
    else:
        keepalive = _tail_keepalive(data, _KEEPALIVE_MELISSA)
    on_batteries = bool(keepalive[4] & 0x20)
    return DecodedPayload(
        measurements=[
            Measurement(
                "sensor_temperature",
                _round((((keepalive[1] << 8) | keepalive[2]) - 400) / 10, 2),
            ),
            Measurement("relative_humidity", _round((keepalive[3] * 100) / 256, 2)),
            Measurement("ir_code_recording_requested", bool(keepalive[4] & 0x80)),
            Measurement("occupied", bool(keepalive[4] & 0x40)),
            Measurement("power_source", "battery" if on_batteries else "usb"),
            Measurement("lorawan_class", "A" if on_batteries else "C"),
            Measurement("lux", keepalive[5] << 8 | keepalive[6]),
            Measurement("pir_trigger_count", keepalive[7] << 8 | keepalive[8]),
            Measurement(
                "battery_voltage",
                _round((keepalive[9] * 16 + 1600) / 1000, 3),
            ),
        ]
    )


def decode_thermostat(data: bytes) -> DecodedPayload:
    """Decode a LoRaWAN Thermostat keepalive or first-data report."""
    if data[0] == 0xFF:
        if len(data) != _KEEPALIVE_THERMOSTAT:
            raise ValueError(f"Thermostat first data requires 7 bytes, got {len(data)}")
        return DecodedPayload(
            measurements=[
                Measurement("reason", data[0]),
                Measurement("keep_alive_time", data[1]),
                Measurement("temp_span", data[2]),
                Measurement("temp_sampling", data[3]),
                Measurement(
                    "target_temperature",
                    (data[4] + 256) / 10 if data[5] > 0 else data[4] / 10,
                ),
                Measurement("battery_status", data[6]),
            ]
        )
    if data[0] not in (0x00, 0x01):
        raise ValueError(f"Unknown Thermostat frame type {data[0]}")
    if len(data) != _KEEPALIVE_THERMOSTAT:
        raise ValueError(f"Thermostat keepalive requires 7 bytes, got {len(data)}")
    return DecodedPayload(
        measurements=[
            Measurement("reason", data[0]),
            Measurement("temperature", (data[2] * 256 + data[1]) / 10),
            Measurement("relay_status", data[2] == 1),
            Measurement("target_temperature", (data[5] * 256 + data[4]) / 10),
            Measurement("battery_status", data[6]),
        ]
    )
