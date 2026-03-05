"""Basic smoke tests for py-nissan-leaf-obd-ble."""

import importlib


def test_package_imports():
    pkg = importlib.import_module("py_nissan_leaf_obd_ble")
    assert hasattr(pkg, "NissanLeafObdBleApiClient")
    assert hasattr(pkg, "OBD")
    assert hasattr(pkg, "ELM327")
    assert hasattr(pkg, "OBDStatus")

