#!/usr/bin/env bash
set -euo pipefail

mirror_dir="${SLSKR_APT_MIRROR_DIR:-/etc/apt}"
source_dir="${SLSKR_APT_SOURCE_DIR:-$mirror_dir}"

if [[ "$#" -gt 0 ]]; then
  source_files=("$@")
else
  source_files=(
    "${source_dir}/sources.list"
    "${source_dir}"/sources.list.d/*.list
    "${source_dir}"/sources.list.d/*.sources
  )
fi

if [[ ! -d "$mirror_dir" ]]; then
  if [[ -w "$(dirname "$mirror_dir")" ]]; then
    mkdir -p "$mirror_dir"
  else
    sudo mkdir -p "$mirror_dir"
  fi
fi

write_mirror_list() {
  local path="$1"
  local content="$2"
  if [[ -w "$mirror_dir" ]]; then
    printf '%s' "$content" > "$path"
  else
    printf '%s' "$content" | sudo tee "$path" >/dev/null
  fi
}

archive_uri="mirror+file:${mirror_dir}/apt-mirrors-archive.txt"
security_uri="mirror+file:${mirror_dir}/apt-mirrors-security.txt"
ports_uri="mirror+file:${mirror_dir}/apt-mirrors-ports.txt"
archive_list="${mirror_dir}/apt-mirrors-archive.txt"
security_list="${mirror_dir}/apt-mirrors-security.txt"
ports_list="${mirror_dir}/apt-mirrors-ports.txt"

# Prefer Ubuntu's canonical endpoints and fail over to a separately hosted
# mirror only when a requested file cannot be fetched from the first endpoint.
write_mirror_list "$archive_list" \
  $'https://archive.ubuntu.com/ubuntu/\tpriority:1\nhttps://mirrors.kernel.org/ubuntu/\tpriority:2\n'
write_mirror_list "$security_list" \
  $'https://security.ubuntu.com/ubuntu/\tpriority:1\nhttps://mirrors.kernel.org/ubuntu/\tpriority:2\n'
write_mirror_list "$ports_list" \
  $'https://ports.ubuntu.com/ubuntu-ports/\tpriority:1\nhttps://mirror.csclub.uwaterloo.ca/ubuntu-ports/\tpriority:2\n'

native_arch="$(dpkg --print-architecture 2>/dev/null || true)"

rewrite_source_file() {
  local source_file="$1"
  local temporary_file
  temporary_file="$(mktemp "${TMPDIR:-/tmp}/slskr-apt-source.XXXXXX")"

  if [[ "$source_file" == *.sources ]]; then
    if ! awk \
      -v archive_uri="$archive_uri" \
      -v security_uri="$security_uri" \
      -v ports_uri="$ports_uri" \
      -v native_arch="$native_arch" \
      '
      BEGIN {
        RS = ""
        FS = "\n"
        ORS = "\n\n"
      }
      {
        suites = ""
        architectures = ""
        uri_values = ""
        current_field = ""
        for (i = 1; i <= NF; i++) {
          if ($i ~ /^[[:space:]]*Suites:[[:space:]]*/) {
            value = $i
            sub(/^[^:]*:[[:space:]]*/, "", value)
            suites = value
            for (j = i + 1; j <= NF && $j ~ /^[[:space:]]+/; j++) {
              suites = suites " " $j
            }
          }
          if ($i ~ /^[[:space:]]*Architectures:[[:space:]]*/) {
            value = $i
            sub(/^[^:]*:[[:space:]]*/, "", value)
            architectures = value
            for (j = i + 1; j <= NF && $j ~ /^[[:space:]]+/; j++) {
              architectures = architectures " " $j
            }
          }
          if ($i ~ /^[[:space:]]*[[:alnum:]-]+:/) {
            current_field = tolower($i)
            sub(/^[[:space:]]*/, "", current_field)
            sub(/:.*/, "", current_field)
          } else if ($i !~ /^[[:space:]]+/) {
            current_field = ""
          }
          if (current_field == "uris") uri_values = uri_values " " $i
        }

        has_security = 0
        has_archive = 0
        suite_count = split(suites, suite_values, /[[:space:],]+/)
        for (i = 1; i <= suite_count; i++) {
          if (suite_values[i] == "") continue
          if (suite_values[i] ~ /-security$/) has_security = 1
          else has_archive = 1
        }

        has_runner_mirror = uri_values ~ /mirror[+]file:[^[:space:],]*apt-mirrors[.]txt/
        has_direct_ubuntu_mirror = uri_values ~ /https?:\/\/(azure[.]archive[.]ubuntu[.]com|([[:alpha:]][[:alpha:]][.])?archive[.]ubuntu[.]com|security[.]ubuntu[.]com|ports[.]ubuntu[.]com)\//
        if (has_runner_mirror && suites == "") {
          print "APT mirror setup cannot route a runner mirror URI without a Suites field" > "/dev/stderr"
          exit 2
        }
        if (has_security && has_archive && (has_runner_mirror || has_direct_ubuntu_mirror)) {
          print "APT mirror setup cannot route a mixed archive/security Deb822 stanza: " suites > "/dev/stderr"
          exit 2
        }

        lower_architectures = tolower(architectures)
        has_x86_architecture = lower_architectures ~ /(^|[[:space:],])(amd64|i386)([[:space:],]|$)/
        has_ports_architecture = lower_architectures ~ /(^|[[:space:],])(arm64|armhf|armel|riscv64|ppc64el|s390x)([[:space:],]|$)/
        if (has_runner_mirror && has_x86_architecture && has_ports_architecture) {
          print "APT mirror setup cannot route mixed x86/ports Architectures in one Deb822 stanza" > "/dev/stderr"
          exit 2
        }
        if (architectures != "") use_ports = has_ports_architecture
        else use_ports = native_arch !~ /^(amd64|i386)$/ && native_arch != ""
        if (use_ports) selected_uri = ports_uri
        else if (has_security) selected_uri = security_uri
        else selected_uri = archive_uri

        current_field = ""
        for (i = 1; i <= NF; i++) {
          if ($i ~ /^[[:space:]]*[[:alnum:]-]+:/) {
            current_field = tolower($i)
            sub(/^[[:space:]]*/, "", current_field)
            sub(/:.*/, "", current_field)
          } else if ($i !~ /^[[:space:]]+/) {
            current_field = ""
          }

          if (current_field == "uris") {
            gsub(/mirror[+]file:[^[:space:],]*apt-mirrors[.]txt/, selected_uri, $i)
            gsub(/https?:\/\/(azure[.]archive[.]ubuntu[.]com|([[:alpha:]][[:alpha:]][.])?archive[.]ubuntu[.]com)\/ubuntu\/?/, archive_uri, $i)
            gsub(/https?:\/\/security[.]ubuntu[.]com\/ubuntu\/?/, security_uri, $i)
            gsub(/https?:\/\/ports[.]ubuntu[.]com\/ubuntu-ports\/?/, ports_uri, $i)
          }
        }

        for (i = 1; i <= NF; i++) {
          printf "%s%s", $i, (i < NF ? "\n" : "")
        }
        printf "\n\n"
      }' "$source_file" >"$temporary_file"; then
      rm -f -- "$temporary_file"
      return 1
    fi
  else
    if ! awk \
      -v archive_uri="$archive_uri" \
      -v security_uri="$security_uri" \
      -v ports_uri="$ports_uri" \
      -v native_arch="$native_arch" \
      '
      {
        line = $0
        if (line !~ /^[[:space:]]*#/) {
          has_security = line ~ /(^|[[:space:]])[^[:space:]]+-security([[:space:]]|$)/
          if (native_arch !~ /^(amd64|i386)$/) selected_uri = ports_uri
          else if (has_security) selected_uri = security_uri
          else selected_uri = archive_uri
          gsub(/mirror[+]file:[^[:space:],]*apt-mirrors[.]txt/, selected_uri, line)
          gsub(/https?:\/\/(azure[.]archive[.]ubuntu[.]com|([[:alpha:]][[:alpha:]][.])?archive[.]ubuntu[.]com)\/ubuntu\/?/, archive_uri, line)
          gsub(/https?:\/\/security[.]ubuntu[.]com\/ubuntu\/?/, security_uri, line)
          gsub(/https?:\/\/ports[.]ubuntu[.]com\/ubuntu-ports\/?/, ports_uri, line)
        }
        print line
      }' "$source_file" >"$temporary_file"; then
      rm -f -- "$temporary_file"
      return 1
    fi
  fi

  if ! cmp -s -- "$source_file" "$temporary_file"; then
    if [[ -w "$source_file" ]]; then
      if ! cat "$temporary_file" >"$source_file"; then
        rm -f -- "$temporary_file"
        return 1
      fi
    else
      if ! cat "$temporary_file" | sudo tee "$source_file" >/dev/null; then
        rm -f -- "$temporary_file"
        return 1
      fi
    fi
  fi
  rm -f -- "$temporary_file"
}

for source_file in "${source_files[@]}"; do
  if [[ ! -f "$source_file" ]]; then
    continue
  fi
  case "$source_file" in
    "$archive_list"|"$security_list"|"$ports_list")
      continue
      ;;
    apt-mirrors*.txt|*/apt-mirrors*.txt)
      # Runner images use apt-mirrors.txt as the backing file for their
      # mirror+file source URI. Rewriting it would create an invalid nested
      # mirror list; rewrite the source stanza to a project-owned list instead.
      continue
      ;;
  esac
  rewrite_source_file "$source_file"
done
