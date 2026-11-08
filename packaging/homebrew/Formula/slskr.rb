class Slskr < Formula
  desc "Rust Soulseek daemon with bundled Web UI"
  homepage "https://github.com/snapetech-org/slskr"
  license "AGPL-3.0-only"
  version "0.2.86"
  revision 1

  on_macos do
    on_arm do
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-aarch64-apple-darwin.tar.gz"
      sha256 "29d22ba47f3f54281922e1ee1de5dd25432ceeeb10c8f965ecb856f7b4203c32"
    end
    on_intel do
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-x86_64-apple-darwin.tar.gz"
      sha256 "4dfcae90531d1d84d750a4a1402c774d5e01fc7561df3ab18729b9c43806e660"
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-aarch64-unknown-linux-musl.tar.gz"
      sha256 "6979d43bb9c44cbcaf65b9674f3373c2300b5507c74b5bc7641825b4a9506981"
    else
      url "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-x86_64-unknown-linux-musl.tar.gz"
      sha256 "12daf7a1a0ce2faf830c5ab56c86071ecb5fd0a8615561a7ef2ecd7c645218f0"
    end
  end

  def install
    libexec.install Dir["*"]
    bin.write_exec_script libexec/"slskr"
  end

  test do
    assert_path_exists libexec/"slskr"
    assert_path_exists libexec/"web/build/index.html"
    assert_match "slskr", shell_output("#{bin}/slskr version")
  end
end
