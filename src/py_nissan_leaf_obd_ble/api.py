"""API for nissan leaf obd ble."""

import asyncio
from contextlib import suppress
import logging

from bleak.backends.device import BLEDevice

from .commands import leaf_commands
from .obd import OBD

_LOGGER: logging.Logger = logging.getLogger(__package__)

# Hard upper bound on a complete OBD session (connect + query loop + close).
# Sized below the Home Assistant coordinator's typical 90s wait_for so the
# library wins the race and runs its own try/finally cleanup, which is what
# actually releases the BLE proxy slot.
DEFAULT_SESSION_TIMEOUT = 75.0
DEFAULT_CLOSE_TIMEOUT = 5.0


class NissanLeafObdBleApiClient:
    """API for connecting to the Nissan Leaf OBD BLE dongle."""

    def __init__(
        self,
        ble_device: BLEDevice,
    ) -> None:
        """Initialise."""
        self._ble_device = ble_device

    async def async_get_data(self, options=None) -> dict | None:
        """Get data from the API."""

        if self._ble_device is None:
            return {}

        opts = options or {}
        session_timeout = float(
            opts.get("session_timeout", DEFAULT_SESSION_TIMEOUT)
        )
        try:
            return await asyncio.wait_for(
                self._collect(opts), timeout=session_timeout
            )
        except asyncio.TimeoutError:
            _LOGGER.warning(
                "OBD session exceeded %.1fs; aborting to release BLE slot",
                session_timeout,
            )
            raise

    async def _collect(self, opts) -> dict | None:
        """Run a complete OBD session and always close on the way out."""
        api = await OBD.create(
            self._ble_device,
            protocol="6",
            service_uuid=opts.get("service_uuid"),
            characteristic_uuid_read=opts.get("characteristic_uuid_read"),
            characteristic_uuid_write=opts.get("characteristic_uuid_write"),
        )

        if api is None:
            return None

        try:
            data = {}
            for command in leaf_commands.values():
                response = await api.query(command, force=True)
                # the first command is the Mystery command. If this doesn't
                # have a response, then none of the other will.
                if command.name == "unknown" and len(response.messages) == 0:
                    break
                if response.value is not None:
                    data.update(response.value)
            _LOGGER.debug("Returning data: %s", data)
            return data
        finally:
            # Bound the close so a hung disconnect cannot keep the slot held
            # forever; suppress so this finally never masks the real error.
            with suppress(Exception):
                await asyncio.wait_for(api.close(), timeout=DEFAULT_CLOSE_TIMEOUT)

