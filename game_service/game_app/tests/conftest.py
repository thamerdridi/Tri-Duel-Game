# Ensure tests have a CA bundle path available before any modules import client_config
# This file is imported by pytest during collection, so setting the env var here
# ensures modules that read os.getenv('CA_BUNDLE_PATH') at import time will see it.
import os
import tempfile

_ca_path = os.path.join(tempfile.gettempdir(), "test_ca_bundle.crt")
# Write a minimal fake certificate so code that checks file existence passes
try:
    if not os.path.exists(_ca_path):
        with open(_ca_path, "w") as _f:
            _f.write("-----BEGIN CERTIFICATE-----\nFAKE-CA\n-----END CERTIFICATE-----\n")
except Exception:
    # Best-effort; if writing fails tests may still provide fixtures to mock the path
    pass

# Export environment variable for modules that read CA_BUNDLE_PATH at import time
os.environ.setdefault("CA_BUNDLE_PATH", _ca_path)


# Optional: provide a pytest fixture that returns the CA path for tests that need it
import pytest

@pytest.fixture(scope="session")
def ca_bundle_path():
    return os.environ.get("CA_BUNDLE_PATH")

