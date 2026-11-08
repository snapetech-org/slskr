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
        version = "0.2.86";
        sources = {
          "x86_64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-x86_64-unknown-linux-musl.tar.gz";
            sha256 = "12daf7a1a0ce2faf830c5ab56c86071ecb5fd0a8615561a7ef2ecd7c645218f0";
          };
          "aarch64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-aarch64-unknown-linux-musl.tar.gz";
            sha256 = "6979d43bb9c44cbcaf65b9674f3373c2300b5507c74b5bc7641825b4a9506981";
          };
          "x86_64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-x86_64-apple-darwin.tar.gz";
            sha256 = "4dfcae90531d1d84d750a4a1402c774d5e01fc7561df3ab18729b9c43806e660";
          };
          "aarch64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-aarch64-apple-darwin.tar.gz";
            sha256 = "29d22ba47f3f54281922e1ee1de5dd25432ceeeb10c8f965ecb856f7b4203c32";
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
