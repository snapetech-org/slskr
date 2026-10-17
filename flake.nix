{
  description = "slskR Rust Soulseek daemon with bundled Web UI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        version = "0.2.71";
        sources = {
          "x86_64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.71/slskr-v0.2.71-x86_64-unknown-linux-gnu.tar.gz";
            sha256 = "efa3ba418d70b1c1c6466cf1d5742b4df18649f4e6c56c1442ab39ffd3621579";
          };
          "aarch64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.71/slskr-v0.2.71-aarch64-unknown-linux-gnu.tar.gz";
            sha256 = "59e58c09fd448591f8645a8336e10183db998527515f1665342e123be1711039";
          };
          "x86_64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.71/slskr-v0.2.71-x86_64-apple-darwin.tar.gz";
            sha256 = "8d3b0f72afce9919e088f5b9c6368d885598f82a5845d050f6ebd71f32c62863";
          };
          "aarch64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.71/slskr-v0.2.71-aarch64-apple-darwin.tar.gz";
            sha256 = "c0a84e8ed42aa1a0f5ddcafb96eb39f51ce2fd6f5def7b53d028240c384e015d";
          };
        };
        mkSlskr = { pname, version, sources }:
          pkgs.stdenv.mkDerivation {
            inherit pname version;
            src = pkgs.fetchurl (sources.${system});
            nativeBuildInputs = [ pkgs.makeWrapper ];
            unpackPhase = "tar xzf $src";
            installPhase = ''
              mkdir -p $out/libexec/${pname} $out/bin
              cp -r . $out/libexec/${pname}/
              chmod +x $out/libexec/${pname}/slskr
              makeWrapper $out/libexec/${pname}/slskr $out/bin/slskr
            '';
          };
      in {
        packages = {
          default = mkSlskr {
            pname = "slskr";
            inherit version sources;
          };
        };
      }
    );
}
