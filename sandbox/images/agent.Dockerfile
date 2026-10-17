# dvl-agent: the agent image (DV4-PLAN §5.2, step 2a): dvl-toolchain by digest
# plus the pinned opencode binary, whose sha256 sandbox/build-images.sh checks
# before staging it. The provider package opencode needs, if any, and the
# pinned Claude Code version file (after step 4c) come with later steps and a
# new digest.
ARG TOOLCHAIN
FROM ${TOOLCHAIN}
USER 0:0
COPY agent/opencode /opt/dvl/agent/opencode
RUN chmod 0555 /opt/dvl/agent/opencode && HOME=/tmp /opt/dvl/agent/opencode --version && rm -rf /tmp/.[!.]* /tmp/*
USER 1000:1000
WORKDIR /work
CMD ["/opt/dvl/bin/entry", "agent"]
