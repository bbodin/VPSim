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

# Verify build artifacts exist
RUN echo "=== Verifying build artifacts ===" && \
    echo "Checking vpsim binary:" && \
    (ls -lh debug/vpsim-release/bin/vpsim && echo "✓ debug vpsim binary found" || echo "✗ debug vpsim binary NOT found") && \
    (ls -lh release/vpsim-release/bin/vpsim && echo "✓ release vpsim binary found" || echo "✗ release vpsim binary NOT found") && \
    echo "Checking QEMU .so files:" && \
    (ls -lh release/vpsim-release/lib/qemu/vpsim-qemu.so && echo "✓ release vpsim-qemu.so found" || echo "✗ release vpsim-qemu.so NOT found") && \
    (ls -lh release/vpsim-release/lib/qemu/vpsim-qemu7.so && echo "✓ release vpsim-qemu7.so found" || echo "✗ release vpsim-qemu7.so NOT found") && \
    (ls -lh release/vpsim-release/lib/qemu/vpsim-qemu9.so && echo "✓ release vpsim-qemu9.so found" || echo "✗ release vpsim-qemu9.so NOT found") && \
    echo "=== Verification complete ==="

# Install all dependencies in one layer
RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

# Download busybox.qcow2 disk image
RUN cd /opt/VPSim && \
    mkdir -p use-cases/GPP/disk_images && \
    wget -q https://github.com/bbodin/vpsim-release/raw/6c5301d74e0797a2c2f7211b63499e8d9c2d3d61/GPP/disk_images/busybox.qcow2.zip -O /tmp/busybox.qcow2.zip && \
    unzip -o /tmp/busybox.qcow2.zip -d use-cases/GPP/disk_images/ && \
    rm /tmp/busybox.qcow2.zip && \
    echo "✓ busybox.qcow2 downloaded and extracted"

# Download Linux kernel
RUN cd /opt/VPSim && \
    mkdir -p use-cases/GPP/linux && \
    wget -q https://github.com/bbodin/vpsim-release/raw/6c5301d74e0797a2c2f7211b63499e8d9c2d3d61/GPP/linux/linux-6.1.44 -O use-cases/GPP/linux/linux-6.1.44 && \
    echo "✓ linux-6.1.44 downloaded"

# Set working directory to where test results are stored
WORKDIR /opt/VPSim/test_results

CMD ["/bin/bash"]


# docker run -it vpsim bash
# > cd /opt/VPSim/ 
# > VPSIM_HOME=/opt/VPSim/release/vpsim-release/ ./use-cases/GPP/gpp_04.py