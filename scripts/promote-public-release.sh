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
command -v python3 >/dev/null
command -v gh >/dev/null
command -v sha256sum >/dev/null
command -v cmp >/dev/null

python3 scripts/verify-canonical-release.py   "$payload"   "$version"   "$canonical_commit"

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
  echo "release $tag already exists; refusing to overwrite immutable publication" >&2
  exit 68
fi

gh release create "$tag"   --repo "$repo"   --target "$target_commit"   --title "Testule $version"   --notes-file "$release_dir/README.md"   --prerelease   "${assets[@]}"

echo "published $repo $tag at $target_commit"
