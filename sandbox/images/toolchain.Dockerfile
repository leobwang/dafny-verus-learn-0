# The sandbox images (DV4-PLAN §5.2; DELTAS Δ504): two targets of one file,
# built only by sandbox/build-images.sh, natively for one architecture
# (linux/amd64 on Linux x86-64, linux/arm64 on Apple silicon), from a staged
# context that holds only the inputs below, never the checkout:
#   toolchain  dvl-toolchain, the verification image
#   agent      dvl-agent: dvl-toolchain plus the pinned opencode
# No host binary is copied in: the build stage installs the image's own
# pinned Linux toolchain (install/install-toolchain.sh: the vendor x64
# releases through get_toolchain.sh on amd64, pinned source builds on arm64)
# and checks every solver's rlimit fingerprint, and the pinned uv, age and
# opencode Linux releases for the architecture (install/install-tools.sh).
# The base is ubuntu:24.04 by the architecture's manifest digest; the packages
# come from the Ubuntu snapshot of the date build-images.sh passes, and their
# versions are listed in /opt/dvl/packages.txt (hashed into images.lock).
ARG BASE
# apt's --snapshot maps archive.ubuntu.com and security.ubuntu.com to the Ubuntu
# snapshot service, but not ports.ubuntu.com, the arm64 base's source; the
# public snapshot of ubuntu/ carries the arm64 indexes and pool too (its
# ubuntu-ports/ path is not public), so ports.ubuntu.com is mapped there.
# Inert on amd64, whose base names no ports.ubuntu.com source.
ARG SNAP_PORTS="Acquire::Snapshots::URI::Host::ports.ubuntu.com=https://snapshot.ubuntu.com/ubuntu/@SNAPSHOTID@/"
# Only fetches the CA bundle apt needs to reach the snapshot service over https.
FROM ${BASE} AS certs
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates

FROM ${BASE} AS build
ARG SNAP_PORTS
ARG APT_SNAPSHOT
ARG DVL_ARCH
COPY --from=certs /etc/ssl/certs/ca-certificates.crt /tmp/apt-ca.crt
RUN set -eu; \
    ca="-o Acquire::https::CaInfo=/tmp/apt-ca.crt -o ${SNAP_PORTS}"; \
    apt-get ${ca} update --snapshot "${APT_SNAPSHOT}"; \
    pk="ca-certificates curl unzip python3 git libicu74"; \
    if [ "${DVL_ARCH}" = arm64 ]; then pk="$pk build-essential cmake pkg-config libssl-dev dotnet-runtime-8.0"; fi; \
    DEBIAN_FRONTEND=noninteractive apt-get ${ca} install -y --no-install-recommends \
        --snapshot "${APT_SNAPSHOT}" $pk
COPY install/ /opt/dvl/install/
COPY check/ /opt/dvl/check/
RUN bash /opt/dvl/install/install-toolchain.sh "${DVL_ARCH}"
RUN bash /opt/dvl/install/install-tools.sh

FROM ${BASE} AS toolchain
ARG SNAP_PORTS
ARG APT_SNAPSHOT
ARG DVL_ARCH
ARG DVL_TOOLCHAIN_DIR_ENV
COPY --from=certs /etc/ssl/certs/ca-certificates.crt /tmp/apt-ca.crt
RUN set -eu; \
    chmod 0644 /tmp/apt-ca.crt; \
    ca="-o Acquire::https::CaInfo=/tmp/apt-ca.crt -o ${SNAP_PORTS}"; \
    apt-get ${ca} update --snapshot "${APT_SNAPSHOT}"; \
    pk="python3 libicu74 gcc libc6-dev"; \
    if [ "${DVL_ARCH}" = arm64 ]; then pk="$pk dotnet-runtime-8.0"; fi; \
    DEBIAN_FRONTEND=noninteractive apt-get ${ca} install -y --no-install-recommends \
        --snapshot "${APT_SNAPSHOT}" $pk; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb /tmp/apt-ca.crt; \
    mkdir -p /opt/dvl; \
    dpkg-query -W -f '${Package}=${Version}\n' | LC_ALL=C sort > /opt/dvl/packages.txt
# uid 1000 is the run's user (DV4-PLAN §5.2); the base's own uid-1000 user goes.
RUN set -eu; \
    if getent passwd ubuntu >/dev/null; then userdel ubuntu; fi; \
    if getent group ubuntu >/dev/null; then groupdel ubuntu; fi; \
    groupadd -g 1000 agent; \
    useradd -u 1000 -g 1000 -d /home/agent -M -s /usr/sbin/nologin agent; \
    mkdir -p /home/agent /run/dvl /work; \
    chown 1000:1000 /home/agent; chmod 0700 /home/agent
COPY --from=build /opt/dvl/toolchain/ /opt/dvl/toolchain/
COPY --from=build /opt/rust/ /opt/rust/
COPY --from=build /opt/dvl/path/ /opt/dvl/path/
COPY --from=build /opt/dvl/tools/uv /opt/dvl/tools/age /opt/dvl/bin/
COPY bin/ /opt/dvl/bin/
COPY py/ /opt/dvl/py/
COPY check/ /opt/dvl/check/
# uv's seeded cache: the locked wheels only, each checked against uv.lock's hash
RUN set -eu; \
    ln -s /opt/dvl/bin/uv /usr/local/bin/uv; \
    cd /opt/dvl/py; \
    UV_CACHE_DIR=/opt/dvl/uv-cache UV_PROJECT_ENVIRONMENT=/tmp/dvl-py-env UV_NO_PROGRESS=1 \
      HOME=/tmp uv sync --frozen; \
    rm -rf /tmp/dvl-py-env /tmp/.cache; \
    cp -a /opt/dvl/uv-cache /tmp/uv-check; \
    UV_CACHE_DIR=/tmp/uv-check UV_PROJECT_ENVIRONMENT=/tmp/dvl-py-env UV_NO_PROGRESS=1 \
      HOME=/tmp uv run --offline --frozen pytest --version; \
    rm -rf /tmp/uv-check /tmp/dvl-py-env /tmp/.cache; \
    chmod -R a+rX,go-w /opt/dvl/uv-cache; \
    /opt/dvl/bin/age --version
# amd64: the in-container tools use the pinned install (get_toolchain.sh --check);
# arm64: dafny and verus on PATH (/opt/dvl/path), checked by version (D78, D79).
ENV DVL_TOOLCHAIN_DIR=${DVL_TOOLCHAIN_DIR_ENV} \
    DVL_UV_SEED_CACHE=/opt/dvl/uv-cache \
    RUSTUP_HOME=/opt/rust/rustup \
    CARGO_HOME=/opt/rust/cargo \
    PATH=/opt/rust/cargo/bin:/usr/local/bin:/usr/bin:/bin:/opt/dvl/path \
    HOME=/home/agent \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1
RUN set -eu; \
    if [ -n "${DVL_TOOLCHAIN_DIR}" ]; then \
      bash /opt/dvl/check/get_toolchain.sh dafny --check; \
      bash /opt/dvl/check/get_toolchain.sh verus --check; \
    fi; \
    dafny --version; verus --version >/dev/null; rustc --version; python3 --version
USER 1000:1000
WORKDIR /work
CMD ["/opt/dvl/bin/entry", "verify"]

FROM toolchain AS agent
USER 0:0
COPY --from=build /opt/dvl/tools/opencode /opt/dvl/agent/opencode
RUN chmod 0555 /opt/dvl/agent/opencode && HOME=/tmp /opt/dvl/agent/opencode --version && rm -rf /tmp/.[!.]* /tmp/*
USER 1000:1000
WORKDIR /work
CMD ["/opt/dvl/bin/entry", "agent"]
