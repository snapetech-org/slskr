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
        version = "0.2.82";
        sources = {
          "x86_64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-x86_64-unknown-linux-musl.tar.gz";
            sha256 = "00e694748fb53e47b280d84e999d4bc0d6a6a548f093b1526f07a6b30e66e306";
          };
          "aarch64-linux" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-aarch64-unknown-linux-musl.tar.gz";
            sha256 = "1d5f0d3660f297f20cd8e97c1727e153358088ce7327d39decd6526f5e953976";
          };
          "x86_64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-x86_64-apple-darwin.tar.gz";
            sha256 = "0e7acda58e7e9d38b4826c398f012af140de16917eb178b9e4f14b1dffe98cd7";
          };
          "aarch64-darwin" = {
            url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-aarch64-apple-darwin.tar.gz";
            sha256 = "340c9e36fd8e371aa7b07781b99fd3faadd8efefa37ab14661932f232823c7d4";
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
