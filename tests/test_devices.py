"""Feed keepalives through live device models and verify merged state."""

from datetime import UTC, datetime, timedelta

from lorawan_connection import DeviceDescriptor, UplinkEvent

from mclimate_lorawan import (
    FanCoilThermostat,
    Melissa,
    Thermostat,
    TValve,
    Vicki,
    WirelessThermostat,
)


def make_device(model, stack: str = "tts"):
    brand_id, model_id = model.identifiers.get(stack, ("mclimate", "unknown"))
    descriptor = DeviceDescriptor(
        network_id="network",
        dev_eui="0201010101010101",
        name="Device",
        application_id="application",
        profile_id="profile",
        stack=stack,
        brand_id=brand_id,
        model_id=model_id,
    )
    return model(descriptor)


def uplink(device, data: bytes, port: int = 1, received_at=None):
    device._receive_event(
        UplinkEvent(
            descriptor=device.descriptor,
            received_at=received_at or datetime(2026, 10, 8, tzinfo=UTC),
            f_port=port,
            data=data,
        )
    )


def test_vicki_updates():
    device = make_device(Vicki)
    uplink(device, bytes.fromhex("811BAF4BAB2A129030"))
    assert device.sensor_temperature == 25.88238397927527
    assert device.target_temperature == 27
    assert device.valve_openness == 23
    assert device.battery_voltage == 2.9

    # stale reading does not replace newer value
    uplink(
        device,
        bytes.fromhex("811BAF4BAB2A129030"),
        received_at=device._times["sensor_temperature"] - timedelta(seconds=1),
    )
    assert device.sensor_temperature == 25.88238397927527

    # wrong port is ignored
    uplink(device, bytes.fromhex("811BAF4BAB2A129030"), port=99)

    # malformed frame is discarded atomically
    uplink(device, b"\x81")
    assert device.sensor_temperature == 25.88238397927527

    device.close()
    uplink(device, bytes.fromhex("811BAF4BAB2A129030"))


def test_t_valve_updates():
    device = make_device(TValve)
    uplink(device, bytes.fromhex("2c40"), port=2)
    assert device.water_temperature == 22
    assert device.valve_state is False
    uplink(device, bytes.fromhex("646304089f"), port=2)
    assert device.battery == 2.872
    device.close()


def test_wireless_thermostat_updates():
    device = make_device(WirelessThermostat)
    uplink(device, bytes.fromhex("81027f880db4011d00000000"), port=2)
    assert device.sensor_temperature == 23.9
    assert device.target_temperature == 28.5
    assert device.illuminance == 0
    uplink(device, bytes.fromhex("120A04271481027f880db4011d00000000"), port=2)
    assert device.sensor_temperature == 23.9
    device.close()


def test_fan_coil_thermostat_updates():
    device = make_device(FanCoilThermostat)
    uplink(device, bytes.fromhex("01026A4C00DC0100070001"), port=2)
    assert device.sensor_temperature == 21.8
    assert device.target_temperature == 22
    assert device.operational_mode == 1
    device.close()


def test_melissa_updates():
    device = make_device(Melissa)
    uplink(device, bytes.fromhex("0102B253E005FA012371"), port=1)
    assert device.sensor_temperature == 29
    assert device.relative_humidity == 32.42
    assert device.illuminance == 1530
    uplink(device, bytes.fromhex("0102B253E005FA012371"), port=2)
    assert device.sensor_temperature == 29
    device.close()


def test_thermostat_updates():
    device = make_device(Thermostat)
    uplink(device, bytes.fromhex("002901005A0064"), port=1)
    assert device.temperature == 29.7
    assert device.target_temperature == 9
    assert device.relay_status is True
    assert device.battery_status == 100
    device.close()
