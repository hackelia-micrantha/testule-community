#!/usr/bin/env bash
set -euo pipefail

version=$(tr -d '\r\n' < VERSION)

scripts/verify-public-release-assets.sh

command -v nix >/dev/null || {
  echo "nix is required for public package qualification" >&2
  exit 69
}

nix --extra-experimental-features 'nix-command flakes' \
  flake check --no-write-lock-file

package=$(
  nix --extra-experimental-features 'nix-command flakes' \
    build --no-link --print-out-paths .#testule
)

[[ -x "$package/bin/testule" ]]
[[ "$("$package/bin/testule" --version)" == "$version" ]]
[[ -r "$package/share/man/man1/testule.1" ]]
[[ -r "$package/share/licenses/testule/LICENSE" ]]
[[ ! -e "$package/go.mod" ]]
[[ ! -e "$package/internal" ]]

run_version=$(
  nix --extra-experimental-features 'nix-command flakes' \
    run . -- --version
)
[[ "$run_version" == "$version" ]]

echo "verified public Testule $version package/app/check surface"
