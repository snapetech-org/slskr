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
        version = "0.2.74";
        sources = {
          "x86_64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-x86_64-unknown-linux-musl.tar.gz";
            sha256 = "c1f63fcad9f98fa5d5d946020fd143dccbdbf77dc86db66c91e4bf183356ca42";
          };
          "aarch64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-aarch64-unknown-linux-musl.tar.gz";
            sha256 = "3ac862d8a9a31ecb54af7ae92970edb69029f1269ed2d7b9bb2e36cfaeda2d82";
          };
          "x86_64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-x86_64-apple-darwin.tar.gz";
            sha256 = "c510f9f5a5b3f813f73022e78b7debc6e662b097e172e76d578bcdb0d08231e2";
          };
          "aarch64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-aarch64-apple-darwin.tar.gz";
            sha256 = "ce808668393baab28778d47a48cdbc1cec7446c6aca156cfc9414195b6258d55";
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
