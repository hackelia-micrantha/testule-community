#!/usr/bin/env python3
"""Verify a canonical Testule release payload before public promotion.

This verifier deliberately does not fetch private canonical source. It accepts
only the already-built canonical release payload and proves that its checksums,
provenance, runtime archive, public-contract archive, and projected manifest
agree with one explicit version and canonical commit.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile

PROJECT = "testule"
CANONICAL_REPOSITORY = "hackelia-micrantha/testule"
PUBLIC_REPOSITORY = "hackelia-micrantha/testule-community"
PLATFORM = "linux-amd64"

PUBLIC_CONTRACT_FILES = {
    "LICENSE",
    "docs/rfcs/0001-core-model.md",
    "docs/rfcs/0002-evidence-gap-analysis.md",
    "docs/rfcs/0003-capability-host-contract.md",
    "docs/cli-unix-composability.md",
    "docs/evidence.md",
    "docs/evidence-streaming.md",
    "docs/adapters/go.md",
    "man/man1/testule.1",
}

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-.][0-9A-Za-z.-]+)?$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class VerificationError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def read_checksum_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        require(len(parts) == 2, f"SHA256SUMS:{line_no}: expected '<digest> <file>'")
        digest, name = parts
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                f"SHA256SUMS:{line_no}: invalid sha256")
        require("/" not in name and "\\" not in name,
                f"SHA256SUMS:{line_no}: path components are not allowed")
        require(name not in result, f"SHA256SUMS:{line_no}: duplicate entry {name}")
        result[name] = digest
    return result


def safe_regular_members(archive: Path) -> tuple[tarfile.TarFile, dict[str, tarfile.TarInfo]]:
    tf = tarfile.open(archive, mode="r:gz")
    regular: dict[str, tarfile.TarInfo] = {}
    for member in tf.getmembers():
        name = member.name
        require(not name.startswith("/"), f"{archive.name}: absolute path rejected: {name}")
        parts = Path(name).parts
        require(".." not in parts, f"{archive.name}: traversal path rejected: {name}")
        require(not member.issym() and not member.islnk(),
                f"{archive.name}: links are not permitted: {name}")
        require(member.isdir() or member.isfile(),
                f"{archive.name}: unsupported archive entry type: {name}")
        if member.isfile():
            require(name not in regular, f"{archive.name}: duplicate file entry: {name}")
            regular[name] = member
    return tf, regular


def member_bytes(tf: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    extracted = tf.extractfile(member)
    require(extracted is not None, f"unable to read archive member {member.name}")
    return extracted.read()


def verify_runtime_archive(path: Path, version: str) -> bytes:
    root = f"testule-{version}-{PLATFORM}"
    expected = {
        f"{root}/bin/testule",
        f"{root}/share/man/man1/testule.1",
        f"{root}/share/licenses/testule/LICENSE",
    }
    tf, regular = safe_regular_members(path)
    try:
        require(set(regular) == expected,
                f"{path.name}: unexpected runtime file set: {sorted(set(regular) ^ expected)}")
        man = member_bytes(tf, regular[f"{root}/share/man/man1/testule.1"])
        require(f"testule {version}".encode() in man,
                f"{path.name}: man page does not identify release version {version}")
        license_bytes = member_bytes(tf, regular[f"{root}/share/licenses/testule/LICENSE"])
        require(bool(license_bytes.strip()), f"{path.name}: empty license")
        binary = member_bytes(tf, regular[f"{root}/bin/testule"])
        require(binary.startswith(b"\x7fELF"), f"{path.name}: runtime executable is not ELF")
        return man
    finally:
        tf.close()


def verify_projection_manifest(data: bytes, files: dict[str, bytes]) -> None:
    seen: dict[str, str] = {}
    for line_no, raw in enumerate(data.decode("utf-8").splitlines(), 1):
        parts = raw.split()
        require(len(parts) == 2, f"PROJECTION.sha256:{line_no}: malformed entry")
        digest, name = parts
        require(name in PUBLIC_CONTRACT_FILES,
                f"PROJECTION.sha256:{line_no}: unexpected path {name}")
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                f"PROJECTION.sha256:{line_no}: invalid digest")
        require(name not in seen, f"PROJECTION.sha256:{line_no}: duplicate {name}")
        seen[name] = digest
    require(set(seen) == PUBLIC_CONTRACT_FILES,
            "PROJECTION.sha256 does not cover the exact public contract allowlist")
    for name, digest in seen.items():
        require(sha256_bytes(files[name]) == digest,
                f"PROJECTION.sha256 digest mismatch for {name}")


def verify_contract_archive(path: Path, version: str, runtime_man: bytes) -> str:
    root = "release-public-contracts"
    expected = {f"{root}/{name}" for name in PUBLIC_CONTRACT_FILES}
    manifest_name = f"{root}/PROJECTION.sha256"
    expected.add(manifest_name)

    tf, regular = safe_regular_members(path)
    try:
        require(set(regular) == expected,
                f"{path.name}: unexpected public-contract file set: {sorted(set(regular) ^ expected)}")
        files = {
            name.removeprefix(f"{root}/"): member_bytes(tf, member)
            for name, member in regular.items()
            if name != manifest_name
        }
        manifest = member_bytes(tf, regular[manifest_name])
        verify_projection_manifest(manifest, files)
        require(files["man/man1/testule.1"] == runtime_man,
                "public-contract man page differs from runtime release man page")
        require(f"testule {version}".encode() in runtime_man,
                f"public-contract man page does not identify release version {version}")
        return sha256_bytes(manifest)
    finally:
        tf.close()


def verify(payload: Path, version: str, canonical_commit: str) -> None:
    require(payload.is_dir(), f"payload directory not found: {payload}")
    require(VERSION_RE.fullmatch(version) is not None, f"invalid version: {version}")
    require(COMMIT_RE.fullmatch(canonical_commit) is not None,
            "canonical commit must be a lowercase 40-character git SHA")

    runtime_name = f"testule-{version}-{PLATFORM}.tar.gz"
    contracts_name = f"testule-{version}-public-contracts.tar.gz"
    required = {
        runtime_name,
        contracts_name,
        "SHA256SUMS",
        "provenance.json",
        "buildinfo.txt",
    }
    actual = {entry.name for entry in payload.iterdir() if entry.is_file()}
    require(actual == required,
            f"payload file set differs from release contract: {sorted(actual ^ required)}")

    checksums = read_checksum_manifest(payload / "SHA256SUMS")
    require(set(checksums) == {runtime_name, contracts_name},
            "SHA256SUMS must cover exactly the runtime and public-contract archives")

    runtime_path = payload / runtime_name
    contracts_path = payload / contracts_name
    runtime_digest = sha256_file(runtime_path)
    contracts_digest = sha256_file(contracts_path)
    require(checksums[runtime_name] == runtime_digest,
            f"runtime archive checksum mismatch: {runtime_name}")
    require(checksums[contracts_name] == contracts_digest,
            f"public-contract archive checksum mismatch: {contracts_name}")

    provenance = json.loads((payload / "provenance.json").read_text(encoding="utf-8"))
    expected_fields = {
        "schemaVersion": 1,
        "project": PROJECT,
        "version": version,
        "tag": f"v{version}",
        "canonicalRepository": CANONICAL_REPOSITORY,
        "canonicalCommit": canonical_commit,
        "publicDistributionRepository": PUBLIC_REPOSITORY,
        "platform": PLATFORM,
        "artifact": runtime_name,
        "sha256": runtime_digest,
        "publicContractsArtifact": contracts_name,
        "publicContractsSha256": contracts_digest,
    }
    for key, expected in expected_fields.items():
        require(provenance.get(key) == expected,
                f"provenance mismatch for {key}: expected {expected!r}, got {provenance.get(key)!r}")

    allowed_provenance = set(expected_fields) | {"publicProjectionManifestSha256"}
    require(set(provenance) == allowed_provenance,
            f"unexpected/missing provenance fields: {sorted(set(provenance) ^ allowed_provenance)}")

    runtime_man = verify_runtime_archive(runtime_path, version)
    projection_digest = verify_contract_archive(contracts_path, version, runtime_man)
    require(provenance.get("publicProjectionManifestSha256") == projection_digest,
            "provenance publicProjectionManifestSha256 does not match projected manifest")

    buildinfo = (payload / "buildinfo.txt").read_text(encoding="utf-8")
    require(buildinfo.strip() != "", "buildinfo.txt is empty")
    require("github.com/hackelia-micrantha/testule" in buildinfo,
            "buildinfo.txt does not identify the canonical Testule module")

    print(f"verified Testule {version} canonical payload from {canonical_commit}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path, help="directory containing the canonical release payload")
    parser.add_argument("version", help="expected Testule version, without leading v")
    parser.add_argument("canonical_commit", help="expected canonical implementation commit SHA")
    args = parser.parse_args()
    try:
        verify(args.payload.resolve(), args.version, args.canonical_commit)
    except (OSError, json.JSONDecodeError, tarfile.TarError, UnicodeDecodeError, VerificationError) as exc:
        print(f"release verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
