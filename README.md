# mclimate-lorawan

Read MClimate devices through ChirpStack or The Things Stack using
[`lorawan-connection`](https://github.com/home-assistant-libs/lorawan-connection).

| Model | Readings | Automatic discovery |
| --- | --- | --- |
| Vicki | Target temperature, air temperature, humidity, battery, valve opening, child lock | ChirpStack, TTS |
| T-Valve | Water temperature, ambient temperature, valve state, battery | TTS |
| Wireless Thermostat | Target temperature, air temperature, humidity, battery, light, PIR | TTS |
| Fan Coil Thermostat | Target temperature, humidity, operational mode | TTS |
| Melissa | Air temperature, humidity, battery, light | Explicit Python use |
| Thermostat | Temperature, target temperature, battery status, relay status | Explicit Python use |

Coverage follows MClimate's TypeScript payload parsers
([mclimate-payload-helper](https://github.com/MClimateSolutions/mclimate-payload-helper)),
with test vectors pinned to their Jest suite. Melissa and the Thermostat have no
automatic discovery identifiers: they are absent from the checked catalogs. Use
their `decode()` methods directly, or subclass them with your deployment's model
identity. Thermostatic uplinks arrive on different FPorts per family; each model
filters its own. This library decodes uplinks and does not implement device
configuration commands.

Raw payloads are decoded locally; a server-side payload formatter is not required.

## Command-line reader

The `mclimate-lorawan` command lists devices or prints readings as they arrive.
Install [uv](https://docs.astral.sh/uv/getting-started/installation/) to run it
with `uvx`, or use `pip install "mclimate-lorawan[chirpstack]"` for ChirpStack
and `pip install "mclimate-lorawan[tts]"` for The Things Stack.

### ChirpStack

Use a ChirpStack v4 gRPC endpoint, an API key, and the tenant UUID.

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

Use the Application Server gRPC endpoint and an application API key with device
read and application traffic read rights. Specify each application explicitly.

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
from lorawan_connection.backend.tts import TTSConnection
from mclimate_lorawan import MClimateDeviceCollection


async def list_devices(endpoint: str, api_key: str, application: str) -> None:
    connection = TTSConnection(
        endpoint,
        api_key,
        identity_server=endpoint,
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

The collection also accepts a `ChirpStackConnection`. Subscribe with
`devices.subscribe_device_added(listener)` and `device.add_update_listener(listener)`
to receive live readings. Values remain `None` until the device reports them.

### Reading measurements

Existing properties such as `Vicki.target_temperature`,
`Vicki.relative_humidity`, and `WirelessThermostat.illuminance` remain available.
All models also expose `measurements[name]`, whose `Measurement` contains `value`
and `timestamp`. Use `device.measurement_value(name)` for direct access.

```python
from mclimate_lorawan import Vicki

payload = Vicki.decode(bytes.fromhex("811BAF4BAB2A129030"))
for measurement in payload.measurements:
    print(measurement.name, measurement.value)
# target_temperature 27
# sensor_temperature 25.88238397927527
# ...
```

Uplinks that answer a downlink command carry a keepalive at the end; the
command-response prefix is ignored per the keepalive-only scope. Direct decoding
raises `ValueError` for malformed frames. Live models discard those payloads
atomically. Partial updates retain other readings; older readings cannot replace
newer values of the same measurement.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
```

Tests include reference outputs for every decoder family, pinned to MClimate's
upstream Jest vectors, plus malformed and out-of-order message coverage.

## Releases

The source version stays `0.0.0`. Publishing a GitHub release named `0.1.0`, for
example, builds that version and publishes it to PyPI through Trusted Publishing.
See [RELEASING.md](RELEASING.md) for the one-time publisher setup.

## License

Apache-2.0. Ported from MClimate's
[mclimate-payload-helper](https://github.com/MClimateSolutions/mclimate-payload-helper)
TypeScript decoders.
