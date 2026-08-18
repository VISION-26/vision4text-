#!/usr/bin/env python3
"""Offline verifier for EVT-CLIP signed evidence ZIP exports.

Usage:
    python tools/verify_evidence_bundle.py evidence.zip --secret "..."

The secret must match EVIDENCE_SIGNING_SECRET in production. If that variable
was not set, use the deployment JWT_SECRET because the server derives a
separate domain-specific signing key from it.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import zipfile
from pathlib import Path


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def derived_key(secret: str) -> bytes:
    return hashlib.sha256(("evtclip-evidence-signing-v1:" + secret).encode("utf-8")).digest()


def verify(path: Path, secret: str) -> dict:
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        required = {"metadata.json", "manifest.sha256.json", "manifest.signature.json"}
        missing = required - names
        if missing:
            raise ValueError(f"Missing required evidence files: {sorted(missing)}")

        manifest = json.loads(archive.read("manifest.sha256.json"))
        signature_doc = json.loads(archive.read("manifest.signature.json"))
        files = manifest.get("files") or {}
        mismatches = []
        control_files = {"manifest.sha256.json", "manifest.signature.json"}
        unexpected = names - set(files) - control_files
        for name in sorted(unexpected):
            mismatches.append({"file": name, "reason": "unmanifested_extra_file"})
        if manifest.get("schema_version") != "evtclip-evidence-manifest-v2":
            mismatches.append({"file": "manifest.sha256.json", "reason": "unexpected_manifest_schema"})
        if signature_doc.get("algorithm") != "HMAC-SHA256" or signature_doc.get("signed_object") != "manifest.sha256.json":
            mismatches.append({"file": "manifest.signature.json", "reason": "unexpected_signature_metadata"})
        for name, expected in files.items():
            if name not in names:
                mismatches.append({"file": name, "reason": "missing"})
                continue
            actual = hashlib.sha256(archive.read(name)).hexdigest()
            if not hmac.compare_digest(actual, str(expected)):
                mismatches.append({"file": name, "reason": "sha256_mismatch", "expected": expected, "actual": actual})

        key = derived_key(secret)
        expected_signature = hmac.new(key, canonical_json(manifest), hashlib.sha256).hexdigest()
        signature_ok = hmac.compare_digest(expected_signature, str(signature_doc.get("signature") or ""))
        key_id = hashlib.sha256(key).hexdigest()[:16]
        key_id_ok = hmac.compare_digest(key_id, str(signature_doc.get("key_id") or ""))

        return {
            "bundle": str(path),
            "zip_integrity": archive.testzip() is None,
            "file_hashes_ok": not mismatches,
            "signature_ok": signature_ok,
            "key_id_ok": key_id_ok,
            "mismatches": mismatches,
            "verified": archive.testzip() is None and not mismatches and signature_ok and key_id_ok,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--secret", required=True, help="EVIDENCE_SIGNING_SECRET, or JWT_SECRET if no dedicated signing secret was configured")
    args = parser.parse_args()
    result = verify(args.bundle, args.secret)
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    sys.exit(main())
