class Slskr < Formula
  desc "Rust Soulseek daemon with bundled Web UI"
  homepage "https://github.com/snapetech-org/slskr"
  license "AGPL-3.0-only"
  version "0.2.83"

  on_macos do
    on_arm do
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-aarch64-apple-darwin.tar.gz"
      sha256 "208216bc33e770fe0211b4f9c0681c36035d8b5a1fdf375b1c8aa87877e226a4"
    end
    on_intel do
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-x86_64-apple-darwin.tar.gz"
      sha256 "c76c44cafbffc958250d32da80a62c1dd4df5cdf1253c2a65ecefe8b12d026df"
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-aarch64-unknown-linux-musl.tar.gz"
      sha256 "a814e893d5686a84cab8bc2e8d0422db6bc7b3a2d4de74147ae2233b46807cbe"
    else
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-x86_64-unknown-linux-musl.tar.gz"
      sha256 "b623e6f007a360c5bc04fac547bd09f614aeb86e7689bfbdb40b4664223c473d"
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
