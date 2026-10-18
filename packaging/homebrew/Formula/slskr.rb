class Slskr < Formula
  desc "Rust Soulseek daemon with bundled Web UI"
  homepage "https://github.com/snapetech-org/slskr"
  license "AGPL-3.0-only"
  version "0.2.74"

  on_macos do
    on_arm do
      url "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-aarch64-apple-darwin.tar.gz"
      sha256 "ce808668393baab28778d47a48cdbc1cec7446c6aca156cfc9414195b6258d55"
    end
    on_intel do
      url "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-x86_64-apple-darwin.tar.gz"
      sha256 "c510f9f5a5b3f813f73022e78b7debc6e662b097e172e76d578bcdb0d08231e2"
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-aarch64-unknown-linux-gnu.tar.gz"
      sha256 "70e55df434fb5333e13f80e9a97cc183a033fed2416ebead458715654265e66d"
    else
      url "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "a9767342626ef961fede6a89296f0578809413178a7889fb8ba752b1bcf26e44"
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
