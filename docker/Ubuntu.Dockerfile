FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG GITHUB_ROOT=https://github.com/CEA-LIST/

# Install dependencies
RUN apt-get update && \
    apt-get install -y git cmake g++ python2 device-tree-compiler zip ninja-build python2-dev libglib2.0-dev libpixman-1-dev && \
    rm -rf /var/lib/apt/lists/*

# Install debug dependencies 
RUN apt-get update && \
    apt-get install -y emacs && \
    rm -rf /var/lib/apt/lists/*

# Clone VPSim repo
WORKDIR /opt
RUN git clone ${GITHUB_ROOT}/VPSim.git && \
    cd VPSim && git submodule update --init --recursive

# Build VPSim
WORKDIR /opt/VPSim
RUN mkdir build && cd build && cmake .. 
RUN cd build && make -j$(nproc)



WORKDIR /opt/VPSim/vpsim-release
#RUN source setup.sh

CMD ["/bin/bash"]
