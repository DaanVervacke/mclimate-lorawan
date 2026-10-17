"""Discover MClimate devices and print their readings."""

from lorawan_connection.cli_helper import run

from . import MClimateDeviceCollection


def main() -> None:
    """Run the MClimate command-line interface."""
    run(MClimateDeviceCollection.DEVICES)


if __name__ == "__main__":
    main()
