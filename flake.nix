{
  description = "Public binary distribution surface for Testule";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/02e08985a27c65ffd33d434eeb2e660a2e4dc84d";

  outputs =
    { self, nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      version = builtins.replaceStrings [ "\n" "\r" ] [ "" "" ] (builtins.readFile ./VERSION);
      canonicalCommit = "879e6f7a0a74ece2c12fcc4a7b16d05387b832ea";
      artifact = "testule-${version}-linux-amd64.tar.gz";
      artifactHash = "sha256-pcq8GdIz6E+9iAzc283GgvURQcMeOfBnesGhRM3wLOw=";
      releaseUrl =
        "https://github.com/hackelia-micrantha/testule-community/releases/download/v${version}/${artifact}";
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          testule = pkgs.stdenvNoCC.mkDerivation {
            pname = "testule";
            inherit version;
            src = pkgs.fetchurl {
              url = releaseUrl;
              hash = artifactHash;
            };
            sourceRoot = "testule-${version}-linux-amd64";
            dontBuild = true;
            strictDeps = true;

            installPhase = ''
              runHook preInstall
              mkdir -p "$out"
              cp -R bin share "$out/"
              runHook postInstall
            '';

            passthru = {
              inherit canonicalCommit artifact artifactHash releaseUrl;
            };

            meta = {
              description = "Portable testing contracts, normalized evidence, and gap analysis";
              homepage = "https://github.com/hackelia-micrantha/testule-community";
              license = pkgs.lib.licenses.asl20;
              mainProgram = "testule";
              platforms = [ "x86_64-linux" ];
            };
          };
        in
        {
          default = testule;
          inherit testule;
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.testule}/bin/testule";
          meta.description = "Run the Testule CLI";
        };
      });

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          package = self.packages.${system}.testule;
        in
        {
          default = pkgs.runCommand "testule-public-release-${version}" { } ''
            set -eu
            test "$("${package}/bin/testule" --version)" = "${version}"
            "${package}/bin/testule" --help > help.txt
            grep -F "testule --help" help.txt >/dev/null
            grep -F "testule --version" help.txt >/dev/null
            test -r "${package}/share/man/man1/testule.1"
            grep -F "testule ${version}" "${package}/share/man/man1/testule.1" >/dev/null
            test -r "${package}/share/licenses/testule/LICENSE"
            test ! -e "${package}/go.mod"
            test ! -e "${package}/internal"
            mkdir -p "$out"
            cp help.txt "$out/help.txt"
            "${package}/bin/testule" --version > "$out/version.txt"
          '';
        }
      );

      formatter = forAllSystems (system: (import nixpkgs { inherit system; }).nixfmt);
    };
}
