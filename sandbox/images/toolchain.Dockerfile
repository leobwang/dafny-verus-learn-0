# dvl-toolchain: the sandbox's verification image (DV4-PLAN §5.2, step 2a).
#
# Built only by sandbox/build-images.sh, from a staged context that holds only
# the inputs below (never the checkout): the pinned Dafny and Verus trees as
# scripts/get_toolchain.sh --check verifies them, the Rust toolchain Verus
# needs (with rustup), the in-container entry, controls and grader
# (truthcheck), the pinned uv and age binaries (sha256-checked by the build
# script), and the harness project's pyproject.toml and uv.lock, from which a
# uv cache of exactly the locked wheels (hashes from uv.lock) is seeded at
# /opt/dvl/uv-cache so that Python acceptance tests run offline in the
# verification container (dvl.python copies the seed into the run's scratch:
# uv needs a writable cache). The base is
# ubuntu:24.04 by digest; the packages come from the Ubuntu snapshot of the
# date build-images.sh passes, and their versions are listed in
# /opt/dvl/packages.txt (and hashed into sandbox/images.lock).
ARG BASE
# Stage 1 only fetches the CA bundle apt needs to reach the snapshot service
# over https; nothing else of it reaches the image.
FROM ${BASE} AS certs
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates
FROM ${BASE}
ARG APT_SNAPSHOT
COPY --from=certs /etc/ssl/certs/ca-certificates.crt /tmp/apt-ca.crt
RUN set -eu; \
    chmod 0644 /tmp/apt-ca.crt; \
    ca="-o Acquire::https::CaInfo=/tmp/apt-ca.crt"; \
    apt-get ${ca} update --snapshot "${APT_SNAPSHOT}"; \
    DEBIAN_FRONTEND=noninteractive apt-get ${ca} install -y --no-install-recommends \
        --snapshot "${APT_SNAPSHOT}" python3 libicu74 gcc libc6-dev; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb /tmp/apt-ca.crt; \
    mkdir -p /opt/dvl; \
    dpkg-query -W -f '${Package}=${Version}\n' | LC_ALL=C sort > /opt/dvl/packages.txt
# uid 1000 is the host user's (DV4-PLAN §5.2); the base's own uid-1000 user goes.
RUN set -eu; \
    if getent passwd ubuntu >/dev/null; then userdel ubuntu; fi; \
    if getent group ubuntu >/dev/null; then groupdel ubuntu; fi; \
    groupadd -g 1000 agent; \
    useradd -u 1000 -g 1000 -d /home/agent -M -s /usr/sbin/nologin agent; \
    mkdir -p /home/agent /run/dvl /work; \
    chown 1000:1000 /home/agent; chmod 0700 /home/agent
COPY toolchain/ /opt/dvl/toolchain/
COPY rust/ /opt/rust/
COPY dvl/ /opt/dvl/
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
ENV DVL_TOOLCHAIN_DIR=/opt/dvl/toolchain \
    DVL_UV_SEED_CACHE=/opt/dvl/uv-cache \
    RUSTUP_HOME=/opt/rust/rustup \
    CARGO_HOME=/opt/rust/cargo \
    PATH=/opt/rust/cargo/bin:/usr/local/bin:/usr/bin:/bin \
    HOME=/home/agent \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1
# The tree digests are checked inside the image, by the course's own check.
RUN set -eu; \
    cd /opt/rust/cargo/bin && ln -s rustup cargo && ln -s rustup rustc; \
    bash /opt/dvl/check/get_toolchain.sh dafny --check; \
    bash /opt/dvl/check/get_toolchain.sh verus --check; \
    rustc --version; python3 --version
USER 1000:1000
WORKDIR /work
CMD ["/opt/dvl/bin/entry", "verify"]
