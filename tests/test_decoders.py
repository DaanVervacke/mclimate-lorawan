"""Decode keepalives against vectors pinned from MClimate's TypeScript tests."""

import pytest

from mclimate_lorawan.decoders import (
    decode_fan_coil_thermostat,
    decode_melissa,
    decode_t_valve,
    decode_thermostat,
    decode_vicki,
    decode_wireless_thermostat,
)


def values(data: bytes, decoder):
    return {item.name: item.value for item in decoder(data).measurements}


class TestVicki:
    """Vectors from src/test/payloadDecoders.test.ts, Vicki payload decoder."""

    def test_simple_keepalive(self):
        result = values(bytes.fromhex("811BAF4BAB2A129030"), decode_vicki)
        assert result["reason"] == 129
        assert result["target_temperature"] == 27
        assert result["sensor_temperature"] == pytest.approx(25.88238397927527)
        assert result["relative_humidity"] == pytest.approx(29.296875)
        assert result["motor_range"] == 554
        assert result["motor_position"] == 427
        assert result["battery_voltage"] == pytest.approx(2.9)
        assert result["open_window"] is False
        assert result["child_lock"] is False
        assert result["attached_backplate"] is True
        assert result["perceive_as_online"] is True
        assert result["anti_freeze_protection"] is False
        assert result["battery_too_low"] is False
        assert result["valve_openness"] == 23

    def test_keepalive_with_command_response_prefix(self):
        result = values(
            bytes.fromhex("56011203042643811BAF4BAB2A129030"), decode_vicki
        )
        assert result["target_temperature"] == 27
        assert result["sensor_temperature"] == pytest.approx(25.88238397927527)
        assert result["motor_range"] == 554
        assert result["motor_position"] == 427
        assert result["battery_voltage"] == pytest.approx(2.9)
        assert result["valve_openness"] == 23

    def test_firmware_1_keepalive(self):
        result = values(bytes.fromhex("011D5A78FA2C01F080"), decode_vicki)
        assert result["reason"] == 1
        assert result["target_temperature"] == 29
        assert result["sensor_temperature"] == pytest.approx(18.0078125)
        assert result["relative_humidity"] == pytest.approx(46.875)
        assert result["motor_range"] == 300
        assert result["motor_position"] == 250
        assert result["battery_voltage"] == pytest.approx(3.5)
        assert result["child_lock"] is True
        assert result["valve_openness"] == 17

    def test_short_frame_rejected(self):
        with pytest.raises(ValueError):
            decode_vicki(bytes.fromhex("81"))


class TestTValve:
    """Vectors from the T-Valve payload decoder suite."""

    def test_short_keepalive(self):
        result = values(bytes.fromhex("2c40"), decode_t_valve)
        assert result["reason"] == "keepalive"
        assert result["water_temperature"] == 22
        assert result["valve_state"] is False
        assert result["ambient_temperature"] == 22

    def test_long_keepalive(self):
        result = values(bytes.fromhex("646304089f"), decode_t_valve)
        assert result["reason"] == "control_button_pressed"
        assert result["battery_too_low"] is False
        assert result["flood_detection_wire_state"] is True
        assert result["alarm_validated"] is False
        assert result["manual_open_indicator"] is True
        assert result["manual_close_indicator"] is True
        assert result["close_time"] == 4
        assert result["open_time"] == 8
        assert result["battery"] == pytest.approx(2.872)

    def test_long_keepalive_battery_low(self):
        result = values(bytes.fromhex("746304089f"), decode_t_valve)
        assert result["battery_too_low"] is True
        assert result["battery"] == pytest.approx(2.872)

    def test_long_keepalive_with_command_answer(self):
        result = values(bytes.fromhex("10620000A4111C"), decode_t_valve)
        assert result["reason"] == "keepalive"
        assert result["battery_too_low"] is True
        assert result["battery"] == pytest.approx(2.912)

    def test_short_frame_rejected(self):
        with pytest.raises(ValueError):
            decode_t_valve(bytes.fromhex("2c"))


class TestWirelessThermostat:
    """Vectors from the Wireless Thermostat payload decoder suite."""

    def test_simple_keepalive(self):
        result = values(
            bytes.fromhex("81027f880db4011d00000000"),
            decode_wireless_thermostat,
        )
        assert result["target_temperature"] == 28.5
        assert result["sensor_temperature"] == 23.9
        assert result["relative_humidity"] == 53.13
        assert result["battery_voltage"] == 3.51
        assert result["power_source_status"] == 0
        assert result["lux"] == 0
        assert result["pir"] is False

    def test_keepalive_with_command_response_prefix(self):
        result = values(
            bytes.fromhex("120A04271481027f880db4011d00000000"),
            decode_wireless_thermostat,
        )
        assert result["target_temperature"] == 28.5
        assert result["sensor_temperature"] == 23.9
        assert result["relative_humidity"] == 53.13
        assert result["battery_voltage"] == 3.51


class TestFanCoilThermostat:
    """Vectors from the FCT payload decoder suite."""

    def test_simple_keepalive(self):
        result = values(
            bytes.fromhex("01026A4C00DC0100070001"),
            decode_fan_coil_thermostat,
        )
        assert result["sensor_temperature"] == 21.8
        assert result["relative_humidity"] == 29.69
        assert result["target_temperature"] == 22
        assert result["operational_mode"] == 1
        assert result["displayed_fan_speed"] == 0
        assert result["actual_fan_speed"] == 7
        assert result["valve_status"] == 0
        assert result["device_status"] == 1

    def test_keepalive_with_command_response_prefix(self):
        result = values(
            bytes.fromhex("7F0101026A4C00DC0100070001"),
            decode_fan_coil_thermostat,
        )
        assert result["sensor_temperature"] == 21.8
        assert result["target_temperature"] == 22


class TestMelissa:
    """Vectors from the Melissa payload decoder suite."""

    def test_keepalive_batteries(self):
        result = values(bytes.fromhex("0102B253E005FA012371"), decode_melissa)
        assert result["sensor_temperature"] == 29
        assert result["relative_humidity"] == 32.42
        assert result["ir_code_recording_requested"] is True
        assert result["occupied"] is True
        assert result["power_source"] == "battery"
        assert result["lorawan_class"] == "A"
        assert result["lux"] == 1530
        assert result["pir_trigger_count"] == 291
        assert result["battery_voltage"] == 3.408

    def test_keepalive_usb(self):
        result = values(bytes.fromhex("01027E460000000000E6"), decode_melissa)
        assert result["sensor_temperature"] == 23.8
        assert result["relative_humidity"] == 27.34
        assert result["power_source"] == "usb"
        assert result["lorawan_class"] == "C"
        assert result["lux"] == 0
        assert result["pir_trigger_count"] == 0
        assert result["battery_voltage"] == 5.28

    def test_keepalive_with_command_response_prefix(self):
        result = values(
            bytes.fromhex("06002F" + "0102B253E005FA012371"), decode_melissa
        )
        assert result["sensor_temperature"] == 29
        assert result["power_source"] == "battery"


class TestThermostat:
    """Wire format from ThermostatPayloadParser.ts; no upstream vectors."""

    def test_keepalive(self):
        result = values(bytes.fromhex("002901005A0064"), decode_thermostat)
        assert result["reason"] == 0
        assert result["temperature"] == 29.7
        assert result["relay_status"] is True
        assert result["target_temperature"] == 9
        assert result["battery_status"] == 100

    def test_first_data(self):
        result = values(bytes.fromhex("FF0A053C1E0164"), decode_thermostat)
        assert result["reason"] == 255
        assert result["keep_alive_time"] == 10
        assert result["temp_span"] == 5
        assert result["temp_sampling"] == 60
        assert result["target_temperature"] == 28.6
        assert result["battery_status"] == 100

    def test_unknown_frame_rejected(self):
        with pytest.raises(ValueError):
            decode_thermostat(bytes.fromhex("420102"))
