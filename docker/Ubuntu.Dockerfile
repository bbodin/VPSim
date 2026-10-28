FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG VPSIM_REPO=https://github.com/bbodin/VPSim.git
ARG VPSIM_BRANCH=qemu9

# Install all dependencies in one layer
RUN apt-get update && \
    apt-get install -y git cmake g++ python2 python3 python3-venv python3-pip python3-tomli \
    device-tree-compiler zip ninja-build python2-dev libglib2.0-dev libpixman-1-dev \
    qemu-system-aarch64 binutils-aarch64-linux-gnu gcc-aarch64-linux-gnu emacs && \
    rm -rf /var/lib/apt/lists/*

# Clone VPSim repo
WORKDIR /opt
RUN git clone ${VPSIM_REPO} && \
    cd VPSim && \
    git checkout ${VPSIM_BRANCH} && \
    git submodule update --init --recursive

# Build VPSim
WORKDIR /opt/VPSim
RUN make release && make debug

# Run tests but don't fail the Docker build - keep results in /opt/VPSim/test_results
RUN mkdir -p /opt/VPSim/test_results && \
    make test || true

# Copy test results to a persistent location
RUN cp -r debug/Testing /opt/VPSim/test_results/ 2>/dev/null || true
RUN cp -r release/Testing /opt/VPSim/test_results/ 2>/dev/null || true

# Set working directory to where test results are stored
WORKDIR /opt/VPSim/test_results

CMD ["/bin/bash"]
