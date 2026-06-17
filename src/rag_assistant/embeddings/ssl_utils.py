"""TLS setup for outbound HTTPS (Hugging Face, Gemini gRPC, etc.)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_tls_for_hf_downloads() -> None:
    """
    Prepare TLS before Hugging Face downloads or Gemini API calls.

    1. **truststore** — injects the **operating system** certificate store into Python's
       `ssl` module (helps Windows where OpenSSL cannot find issuers).

    2. **certifi** — sets env vars used by urllib/requests **and** gRPC's OpenSSL stack:
       `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, and
       **`GRPC_DEFAULT_SSL_ROOTS_FILE_PATH`** (the last fixes many
       `CERTIFICATE_VERIFY_FAILED` errors from `google.generativeai` / Gemini gRPC).
    """
    try:
        import truststore

        truststore.inject_into_ssl()
        logger.info("TLS: truststore.inject_into_ssl() enabled (OS certificate store).")
    except ImportError:
        logger.info(
            "TLS: package 'truststore' not installed — using certifi/env only. "
            "If Hugging Face SSL still fails on Windows: pip install truststore"
        )
    except Exception as exc:  # noqa: BLE001 — never block app startup on TLS shim
        logger.warning("TLS: truststore.inject_into_ssl() failed (%s); continuing.", exc)

    try:
        import certifi
    except ImportError:
        logger.warning("TLS: certifi not installed; Hugging Face downloads may fail.")
        return

    bundle = certifi.where()
    for key in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        if not os.environ.get(key, "").strip():
            os.environ[key] = bundle
    if not os.environ.get("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", "").strip():
        os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = bundle
    logger.debug("TLS: certifi bundle wired (%s).", bundle)


# Backwards-compatible name
ensure_certifi_ca_bundle = configure_tls_for_hf_downloads
