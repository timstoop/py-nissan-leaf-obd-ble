"""Tests for the bleserial timeout/cleanup behaviour."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak_retry_connector import BleakOutOfConnectionSlotsError

from py_nissan_leaf_obd_ble.bleserial import bleserial


def _make_serial(connect_timeout=0.05, io_timeout=0.05):
    device = MagicMock()
    device.name = "fake"
    return bleserial(
        device,
        service_uuid="svc",
        characteristic_uuid_read="rd",
        characteristic_uuid_write="wr",
        connect_timeout=connect_timeout,
        io_timeout=io_timeout,
    )


@pytest.mark.asyncio
async def test_open_propagates_out_of_slots():
    """BleakOutOfConnectionSlotsError must reach the caller, not be swallowed."""
    serial = _make_serial()

    async def raise_out_of_slots(*_args, **_kwargs):
        raise BleakOutOfConnectionSlotsError("no slots")

    with patch(
        "py_nissan_leaf_obd_ble.bleserial.establish_connection",
        side_effect=raise_out_of_slots,
    ):
        with pytest.raises(BleakOutOfConnectionSlotsError):
            await serial.open()

    # _force_close ran: no client retained.
    assert serial._client is None


@pytest.mark.asyncio
async def test_open_force_closes_on_timeout():
    """If establish_connection hangs, open() times out and disconnects the client."""
    serial = _make_serial(connect_timeout=0.05)

    fake_client = MagicMock()
    fake_client.disconnect = AsyncMock()
    fake_client.start_notify = AsyncMock()

    async def hang_returning_client(*_args, **_kwargs):
        # Sleep longer than connect_timeout so wait_for times out.
        await asyncio.sleep(1.0)
        return fake_client

    with patch(
        "py_nissan_leaf_obd_ble.bleserial.establish_connection",
        side_effect=hang_returning_client,
    ):
        with pytest.raises(asyncio.TimeoutError):
            await serial.open()

    # establish_connection never returned, so there was no client to disconnect.
    assert serial._client is None
    fake_client.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_open_force_closes_when_start_notify_times_out():
    """If start_notify hangs after connect, the connected client is disconnected."""
    serial = _make_serial(connect_timeout=0.05)

    fake_client = MagicMock()
    fake_client.disconnect = AsyncMock()

    async def hang_notify(*_args, **_kwargs):
        await asyncio.sleep(1.0)

    fake_client.start_notify = AsyncMock(side_effect=hang_notify)

    async def return_client(*_args, **_kwargs):
        return fake_client

    with patch(
        "py_nissan_leaf_obd_ble.bleserial.establish_connection",
        side_effect=return_client,
    ):
        with pytest.raises(asyncio.TimeoutError):
            await serial.open()

    # Slot must be released: disconnect was called and reference cleared.
    fake_client.disconnect.assert_awaited_once()
    assert serial._client is None


@pytest.mark.asyncio
async def test_write_force_closes_on_timeout():
    """A hung write_gatt_char must trigger force_close so the slot is freed."""
    serial = _make_serial(io_timeout=0.05)

    fake_client = MagicMock()
    fake_client.disconnect = AsyncMock()

    async def hang_write(*_args, **_kwargs):
        await asyncio.sleep(1.0)

    fake_client.write_gatt_char = AsyncMock(side_effect=hang_write)
    serial._client = fake_client

    with pytest.raises(asyncio.TimeoutError):
        await serial.write(b"ATZ\r")

    fake_client.disconnect.assert_awaited_once()
    assert serial._client is None


@pytest.mark.asyncio
async def test_elm327_create_propagates_out_of_slots():
    """ELM327.create no longer swallows BleakOutOfConnectionSlotsError.

    Regression: previously the broad `except Exception` at the open-port
    step returned `self` with status=NOT_CONNECTED, which the coordinator
    saw as "empty data, car must be off" -- never as the slot exhaustion
    it actually was.
    """
    from py_nissan_leaf_obd_ble.elm327 import ELM327

    device = MagicMock()
    device.name = "fake"

    async def raise_out_of_slots(*_args, **_kwargs):
        raise BleakOutOfConnectionSlotsError("no slots")

    with patch(
        "py_nissan_leaf_obd_ble.bleserial.establish_connection",
        side_effect=raise_out_of_slots,
    ):
        with pytest.raises(BleakOutOfConnectionSlotsError):
            await ELM327.create(device, protocol="6", timeout=0.1)
