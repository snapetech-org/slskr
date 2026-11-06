class Slskr < Formula
  desc "Rust Soulseek daemon with bundled Web UI"
  homepage "https://github.com/snapetech-org/slskr"
  license "AGPL-3.0-only"
  version "0.2.82"

  on_macos do
    on_arm do
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-aarch64-apple-darwin.tar.gz"
      sha256 "340c9e36fd8e371aa7b07781b99fd3faadd8efefa37ab14661932f232823c7d4"
    end
    on_intel do
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-x86_64-apple-darwin.tar.gz"
      sha256 "0e7acda58e7e9d38b4826c398f012af140de16917eb178b9e4f14b1dffe98cd7"
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-aarch64-unknown-linux-musl.tar.gz"
      sha256 "1d5f0d3660f297f20cd8e97c1727e153358088ce7327d39decd6526f5e953976"
    else
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-x86_64-unknown-linux-musl.tar.gz"
      sha256 "00e694748fb53e47b280d84e999d4bc0d6a6a548f093b1526f07a6b30e66e306"
    end
  end

  def install
    libexec.install Dir["*"]
    bin.install libexec/"slskr"
  end

  test do
    assert_match "slskr", shell_output("#{bin}/slskr version")
  end
end
