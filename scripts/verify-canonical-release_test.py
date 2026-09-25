#!/usr/bin/env python3
"""Synthetic regression coverage for the public release-payload verifier."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

VERSION = "0.1.0-alpha.1"
COMMIT = "b95265e991b7ae9cd972ecf918f5cb1b9771a5c0"
PLATFORM = "linux-amd64"

CONTRACTS = {
    "LICENSE": b"Apache License 2.0 fixture\n",
    "docs/rfcs/0001-core-model.md": b"# Core\n",
    "docs/rfcs/0002-evidence-gap-analysis.md": b"# Evidence\n",
    "docs/rfcs/0003-capability-host-contract.md": b"# Capability\n",
    "docs/cli-unix-composability.md": b"# CLI\n",
    "docs/evidence.md": b"# Evidence\n",
    "docs/evidence-streaming.md": b"# Streaming\n",
    "docs/adapters/go.md": b"# Go\n",
    "man/man1/testule.1": f".TH TESTULE 1 fixture \"testule {VERSION}\"\n".encode(),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_file(tf: tarfile.TarFile, name: str, data: bytes, mode: int = 0o444) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.mtime = 0
    tf.addfile(info, io.BytesIO(data))


def make_runtime(path: Path) -> None:
    root = f"testule-{VERSION}-{PLATFORM}"
    with tarfile.open(path, "w:gz") as tf:
        add_file(tf, f"{root}/bin/testule", b"\x7fELFfixture-" + VERSION.encode(), 0o555)
        add_file(tf, f"{root}/share/man/man1/testule.1", CONTRACTS["man/man1/testule.1"])
        add_file(tf, f"{root}/share/licenses/testule/LICENSE", CONTRACTS["LICENSE"])


def make_contracts(path: Path) -> str:
    manifest = b"".join(
        f"{digest(data)}  {name}\n".encode()
        for name, data in sorted(CONTRACTS.items())
    )
    with tarfile.open(path, "w:gz") as tf:
        for name, data in CONTRACTS.items():
            add_file(tf, f"release-public-contracts/{name}", data)
        add_file(tf, "release-public-contracts/PROJECTION.sha256", manifest)
    return digest(manifest)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(payload: Path) -> None:
    runtime_name = f"testule-{VERSION}-{PLATFORM}.tar.gz"
    contracts_name = f"testule-{VERSION}-public-contracts.tar.gz"
    runtime = payload / runtime_name
    contracts = payload / contracts_name
    make_runtime(runtime)
    projection_digest = make_contracts(contracts)
    runtime_digest = sha256_file(runtime)
    contracts_digest = sha256_file(contracts)

    (payload / "SHA256SUMS").write_text(
        f"{runtime_digest}  {runtime_name}\n"
        f"{contracts_digest}  {contracts_name}\n",
        encoding="utf-8",
    )
    (payload / "provenance.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "project": "testule",
                "version": VERSION,
                "tag": f"v{VERSION}",
                "canonicalRepository": "hackelia-micrantha/testule",
                "canonicalCommit": COMMIT,
                "publicDistributionRepository": "hackelia-micrantha/testule-community",
                "platform": PLATFORM,
                "artifact": runtime_name,
                "sha256": runtime_digest,
                "publicContractsArtifact": contracts_name,
                "publicContractsSha256": contracts_digest,
                "publicProjectionManifestSha256": projection_digest,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (payload / "buildinfo.txt").write_text(
        "path\tgithub.com/hackelia-micrantha/testule\n", encoding="utf-8"
    )


def run_verifier(script: Path, payload: Path, commit: str = COMMIT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), str(payload), VERSION, commit],
        check=False,
        text=True,
        capture_output=True,
    )


def main() -> int:
    script = Path(__file__).with_name("verify-canonical-release.py")
    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp)
        build_fixture(payload)

        good = run_verifier(script, payload)
        if good.returncode != 0:
            print(good.stdout, end="")
            print(good.stderr, end="", file=sys.stderr)
            raise SystemExit("valid synthetic release payload was rejected")

        wrong_commit = run_verifier(script, payload, "0" * 40)
        if wrong_commit.returncode == 0:
            raise SystemExit("verifier accepted the wrong canonical commit")

        provenance = json.loads((payload / "provenance.json").read_text(encoding="utf-8"))
        provenance["artifact"] = "unexpected.tar.gz"
        (payload / "provenance.json").write_text(json.dumps(provenance) + "\n", encoding="utf-8")
        bad_identity = run_verifier(script, payload)
        if bad_identity.returncode == 0:
            raise SystemExit("verifier accepted mismatched provenance identity")

    print("canonical release verifier synthetic cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
