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
        version = "0.2.83";
        sources = {
          "x86_64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-x86_64-unknown-linux-musl.tar.gz";
            sha256 = "b623e6f007a360c5bc04fac547bd09f614aeb86e7689bfbdb40b4664223c473d";
          };
          "aarch64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-aarch64-unknown-linux-musl.tar.gz";
            sha256 = "a814e893d5686a84cab8bc2e8d0422db6bc7b3a2d4de74147ae2233b46807cbe";
          };
          "x86_64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-x86_64-apple-darwin.tar.gz";
            sha256 = "c76c44cafbffc958250d32da80a62c1dd4df5cdf1253c2a65ecefe8b12d026df";
          };
          "aarch64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-aarch64-apple-darwin.tar.gz";
            sha256 = "208216bc33e770fe0211b4f9c0681c36035d8b5a1fdf375b1c8aa87877e226a4";
          };
        };
        mkSlskr = { pname, version, sources }:
          pkgs.stdenv.mkDerivation {
            inherit pname version;
            src = pkgs.fetchurl (sources.${system});
            nativeBuildInputs = [ pkgs.makeWrapper ];
            dontConfigure = true;
            dontBuild = true;
            dontStrip = true;
            dontPatchELF = true;
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
