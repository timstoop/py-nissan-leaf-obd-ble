# py-nissan-leaf-obd-ble

Python hardware API for Nissan Leaf OBD-II over BLE dongles.

This library encapsulates the low-level BLE, ELM327 and CAN protocol handling
used by the Home Assistant `nissan_leaf_obd_ble` integration, and exposes a
simple async API for querying vehicle data from a `BLEDevice`.

It has **no Home Assistant dependency** and can be used in other Python
applications that talk to the same BLE OBD dongle.

## Installation

Once published on PyPI:

```bash
pip install py-nissan-leaf-obd-ble
```

## Quickstart

```python
import asyncio
from bleak import BleakScanner

from py_nissan_leaf_obd_ble import NissanLeafObdBleApiClient


async def main() -> None:
    # Discover your OBDBLE device with bleak, or obtain a BLEDevice from elsewhere
    device = await BleakScanner.find_device_by_address("AA:BB:CC:DD:EE:FF", timeout=10.0)
    if device is None:
        raise RuntimeError("Could not find OBDBLE device")

    client = NissanLeafObdBleApiClient(device)
    data = await client.async_get_data()
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
```

## Configurable BLE UUIDs

The default GATT service and characteristic UUIDs match the LeLink OBD BLE dongle. When used with the Home Assistant integration, the service and read/write characteristic UUIDs are configurable per device in the UI. For custom use, `async_get_data(options=None)` accepts an optional `options` dict with keys `service_uuid`, `characteristic_uuid_read`, and `characteristic_uuid_write`; omit keys to use the library defaults.

## License

This package includes code derived from **python-OBD (a derivative of pyOBD)**,
licensed under the GNU General Public License, version 2 or later.

See `LICENSE` for full terms.

