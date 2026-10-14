#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <canonical-payload-dir> <public-target-commit>" >&2
  exit 64
fi

payload=$(realpath -e -- "$1")
target_commit=$2
repo=hackelia-micrantha/testule-community
version=$(tr -d '\r\n' < VERSION)
tag="v$version"
canonical_commit=879e6f7a0a74ece2c12fcc4a7b16d05387b832ea
release_dir="release/$tag"

[[ "$version" == "0.1.0-alpha.2" ]] || {
  echo "unexpected VERSION: $version" >&2
  exit 65
}
[[ "$target_commit" =~ ^[0-9a-f]{40}$ ]] || {
  echo "public target must be an exact 40-character commit" >&2
  exit 64
}
for cmd in python3 gh sha256sum cmp mktemp; do
  command -v "$cmd" >/dev/null || {
    echo "required command unavailable: $cmd" >&2
    exit 69
  }
done

python3 scripts/verify-canonical-release.py \
  "$payload" \
  "$version" \
  "$canonical_commit"

runtime="testule-$version-linux-amd64.tar.gz"
contracts="testule-$version-public-contracts.tar.gz"
assets=(
  "$payload/$runtime"
  "$payload/$contracts"
  "$payload/SHA256SUMS"
  "$payload/provenance.json"
  "$payload/buildinfo.txt"
)
for asset in "${assets[@]}"; do
  [[ -f "$asset" && ! -L "$asset" ]] || {
    echo "missing/non-regular release asset: $asset" >&2
    exit 66
  }
done

cmp "$payload/SHA256SUMS" "$release_dir/SHA256SUMS"
cmp "$payload/provenance.json" "$release_dir/provenance.json"
cmp "$payload/buildinfo.txt" "$release_dir/buildinfo.txt"

repo_target=$(gh api "repos/$repo/commits/$target_commit" --jq .sha)
[[ "$repo_target" == "$target_commit" ]] || {
  echo "public target commit could not be verified" >&2
  exit 67
}

if gh release view "$tag" --repo "$repo" >/dev/null 2>&1; then
  echo "release $tag already exists; refusing to overwrite publication state" >&2
  exit 68
fi

if ref_json=$(gh api "repos/$repo/git/ref/tags/$tag" 2>/dev/null); then
  ref_type=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["object"]["type"])' <<<"$ref_json")
  ref_sha=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["object"]["sha"])' <<<"$ref_json")
  [[ "$ref_type" == "commit" && "$ref_sha" == "$target_commit" ]] || {
    echo "existing release tag does not directly identify expected public commit" >&2
    exit 70
  }
else
  gh api \
    --method POST \
    "repos/$repo/git/refs" \
    -f "ref=refs/tags/$tag" \
    -f "sha=$target_commit" \
    >/dev/null
fi

ref_type=$(gh api "repos/$repo/git/ref/tags/$tag" --jq .object.type)
ref_sha=$(gh api "repos/$repo/git/ref/tags/$tag" --jq .object.sha)
[[ "$ref_type" == "commit" && "$ref_sha" == "$target_commit" ]] || {
  echo "release tag does not point directly to expected public commit" >&2
  exit 70
}

gh release create "$tag" \
  --repo "$repo" \
  --verify-tag \
  --title "Testule $version" \
  --notes-file "$release_dir/README.md" \
  --draft \
  --prerelease \
  "${assets[@]}"

work=$(mktemp -d)
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT
release_json="$work/release.json"
gh release view "$tag" \
  --repo "$repo" \
  --json tagName,isDraft,isPrerelease,assets \
  > "$release_json"

python3 - "$release_json" "$tag" <<'PY'
import json
import pathlib
import sys

release = json.loads(pathlib.Path(sys.argv[1]).read_text())
tag = sys.argv[2]
expected = {
    "testule-0.1.0-alpha.2-linux-amd64.tar.gz":
        "sha256:a5cabc19d233e84fbd880cdcdbcdc682f51141c31e39f0677ac1a144cdf02cec",
    "testule-0.1.0-alpha.2-public-contracts.tar.gz":
        "sha256:beeff1932d9b7725c16ee7e6dcf3d1d9c7b4dad1b9300009b9b2ed3f0603c626",
    "SHA256SUMS":
        "sha256:40657a4d8a8e2c292f26ac10fc97eb7dca19e572235af146625bacdb28f14c26",
    "provenance.json":
        "sha256:c3745d6f17b92eecf31fbb75f9eaad22b17ddcd289832dd0b988eb5395cea5f5",
    "buildinfo.txt":
        "sha256:b0b807e0af78e5f2916d654d122739c1969538f768e77623726e4e138128fa67",
}
if release.get("tagName") != tag:
    raise SystemExit("draft release tag mismatch")
if release.get("isDraft") is not True or release.get("isPrerelease") is not True:
    raise SystemExit("release must remain draft prerelease during asset verification")
actual = {
    asset.get("name"): asset.get("digest")
    for asset in release.get("assets", [])
}
if actual != expected:
    raise SystemExit(f"draft release asset digest set mismatch: {actual!r}")
PY

gh release edit "$tag" \
  --repo "$repo" \
  --draft=false \
  --prerelease

published=$(gh release view "$tag" --repo "$repo" --json isDraft --jq .isDraft)
[[ "$published" == "false" ]] || {
  echo "release did not leave draft state" >&2
  exit 71
}

echo "published verified $repo $tag at $target_commit"
