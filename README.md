# MClimate LoRaWAN

Read MClimate thermostatic devices through ChirpStack or The Things Stack using
`lorawan-connection`.

| Model                 | Readings                                                              | Automatic discovery |
| --------------------- | --------------------------------------------------------------------- | ------------------- |
| Vicki                 | Target/sensor temperature, humidity, valve openness, motor, battery   | ChirpStack, TTS     |
| T-Valve               | Water/ambient temperature, valve state, flood and tamper flags        | TTS                 |
| Wireless Thermostat   | Target/sensor temperature, humidity, lux, PIR, battery                 | TTS                 |
| Fan Coil Thermostat   | Target/sensor temperature, humidity, fan speeds, valve, device status | TTS                 |
| Melissa LoRaWAN       | Temperature, humidity, lux, PIR count, occupancy, power source        | Explicit Python use |
| Thermostat            | Temperature, target temperature, relay status, battery                | Explicit Python use |

Coverage follows the thermostatic device families in MClimate's
`mclimate-payload-helper`. Melissa LoRaWAN and the LoRaWAN Thermostat have no
automatic discovery identifiers: they are absent from the TTN and ChirpStack
catalogs checked for this release. Use their `decode()` methods directly, or
subclass them with your deployment's model identity.

This library decodes uplink keepalives and does not implement device
configuration commands. Uplinks that answer a downlink command carry a
keepalive at the end; the command-response prefix is ignored and only the
keepalive readings are exposed.

Raw payloads are decoded locally; a server-side payload formatter is not
required.

## Command-line reader

The `mclimate-lorawan` command lists devices or prints readings as they
arrive. Install uv to run it with `uvx`, or use
`pip install "mclimate-lorawan[chirpstack]"` for ChirpStack and
`pip install "mclimate-lorawan[tts]"` for The Things Stack.

### ChirpStack

Use a ChirpStack v4 gRPC endpoint, an API key, and the tenant UUID. The
endpoint must expose the gRPC API; forwarding only the web interface is not
sufficient.

```sh
export CHIRPSTACK_API_KEY="your-api-key"
uvx --from "mclimate-lorawan[chirpstack]" mclimate-lorawan \
  --backend chirpstack \
  --server https://chirpstack.example.com:8080 \
  --tenant YOUR_TENANT_UUID \
  --application YOUR_APPLICATION_UUID
```

Repeat `--application` to select more applications. If omitted, all accessible
applications in the selected tenant are used. A global key can omit `--tenant`
to discover its accessible tenants.

### The Things Stack

Use the Application Server gRPC endpoint and an application API key with
device read and application traffic read rights. Specify each application
explicitly.

```sh
export TTS_API_KEY="your-api-key"
uvx --from "mclimate-lorawan[tts]" mclimate-lorawan \
  --backend tts \
  --server https://eu1.cloud.thethings.network:8884 \
  --identity-server https://eu1.cloud.thethings.network:8884 \
  --application YOUR_APPLICATION_ID
```

Set `--identity-server` to your deployment's Identity Server if it differs from
the Application Server. Repeat `--application` for multiple applications.

Add `--list` to print the current devices and exit, or `--json` for
newline-delimited JSON output. Use `--api-key-file /path/to/key` instead of an
environment variable if preferred. Stop watching with Ctrl+C. Run
`mclimate-lorawan --help` for all options.

With a pip installation, use `mclimate-lorawan` directly in place of the
`uvx --from ... mclimate-lorawan` prefix. `python -m mclimate_lorawan` also
works.

## Python

```python
from lorawan_connection.backend.chirpstack import ChirpStackConnection
from mclimate_lorawan import MClimateDeviceCollection


async def list_sensors(
    endpoint: str, api_key: str, tenant: str, application: str
) -> None:
    connection = ChirpStackConnection(
        endpoint,
        api_key,
        tenant_id=tenant,
        application_ids=[application],
        network_id=endpoint,
    )
    devices = MClimateDeviceCollection(connection)
    try:
        await connection.async_connect()
        await devices.async_setup()
        for device in devices.devices.values():
            print(device.descriptor.name, type(device).__name__)
    finally:
        devices.close()
        await connection.close()
```

The collection also accepts a `TTSConnection`. Subscribe with
`devices.subscribe_device_added(listener)` and `device.add_update_listener(listener)`
to receive live readings. Values remain `None` until the device reports them.

### Reading measurements

Each model exposes typed properties such as `Vicki.target_temperature`,
`Vicki.sensor_temperature`, and `Vicki.valve_openness`. All models also expose
`measurements[name]`, whose `Measurement` contains `value` and the keepalive
structure. Direct decoding raises `ValueError` for malformed frames; live
models discard those payloads atomically. Older readings cannot replace newer
values of the same measurement.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
```

Tests include keepalive vectors pinned from MClimate's
`mclimate-payload-helper` Jest suite, live device models fed with those
payloads, and malformed or stale message handling.

## License

Apache-2.0. Wire formats derived from MClimate's `mclimate-payload-helper`.
