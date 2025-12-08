cmake_minimum_required(VERSION 3.10)

enable_testing()

# Unfortunately some dependencies are not up to date.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

project(vpsim)

##################################
##### Configure & build QEMU #####
##################################

set(QEMU_SOURCE_DIR ${CMAKE_SOURCE_DIR}/vpsim-qemu)
set(QEMU_BINARY_DIR ${CMAKE_BINARY_DIR}/qemu-build)


if(CMAKE_BUILD_TYPE STREQUAL Debug)
    message("Configuring QEMU in DEBUG mode")
    set(QEMU_ENABLE_DEBUG --enable-debug)
endif()

# Ensure the QEMU build directory exists (create it if not)
file(MAKE_DIRECTORY ${QEMU_BINARY_DIR})
include(ExternalProject)

ExternalProject_Add(qemu
        SOURCE_DIR    ${QEMU_SOURCE_DIR}
        BINARY_DIR    ${QEMU_BINARY_DIR}
        CONFIGURE_COMMAND ${QEMU_SOURCE_DIR}/configure --target-list=aarch64-softmmu
    # Core / Emulator Features
        --disable-sparse                     # (old)
        --disable-kvm                        # (old)
        --disable-bsd-user                    # (old)
        --disable-pie                         # (old)
        --disable-coroutine-pool              # (old)
        --disable-attr                        # (old)
        --disable-docs                        # (old)
        --disable-werror                       # (old)
        --disable-guest-agent                  # (old)
        --disable-cap-ng                       # (old)
      # GUI / Display / Input
        --disable-sdl                         # (old)
        --disable-gtk                         # (old)
        --disable-vnc                         # (old)
        --disable-vnc-sasl                     # (old)
        --disable-vnc-jpeg                     # (old)
        --disable-vnc-png                       # (old)
        --disable-curses                        # (old)
        --disable-spice                         # (old)
        --disable-opengl                        # (old)
        --disable-virglrenderer                 # (old)
        --disable-xkbcommon
      # Audio
        --disable-alsa
        --disable-coreaudio
        --disable-dsound
        --disable-jack
        --disable-oss
        --disable-pa
      # USB / Devices / Peripheral Support
        --disable-usb-redir                     # (old)
        --disable-libusb                         # (old)
        --disable-libiscsi                       # (old)
        --disable-virtfs                        # (old)
        --disable-virtiofsd                     # (old)
        --disable-fuse                           # (old)
        --disable-vde
        --disable-xen                             # (old)
        --disable-brlapi                          # (old)
      # Block Device / Disk Formats
        --disable-bochs                          # (old)
        --disable-cloop                           # (old)
        --disable-dmg                             # (old)
        --disable-qcow1                           # (old)
        --disable-qed                             # (old)
        --disable-parallels                        # (old)
        --disable-vhdx                             # (obsolete / always built)
        --disable-vdi
        --disable-vvfat                            # (old)
        --disable-lzfse                            # (old)
        --disable-lzo
        --disable-snappy                           # (old)
        --disable-bzip2                            # (old)
        --disable-zstd                             # (old)
        --disable-glusterfs                         # (old)
        --disable-rbd                               # (old)
        --disable-libpmem                           # (old)
        --disable-libdaxctl                         # (old)
        --disable-libnfs                             # (old)
      # Networking
        --disable-l2tpv3
      #  --disable-slirp # This completely remove networking haha
        --disable-netmap
      # Security / Crypto / System
        --disable-seccomp                          # (old)
        --disable-selinux
        --disable-smartcard
        --disable-tpm
        --disable-u2f
        --disable-linux-aio
        --disable-linux-io-uring
        --disable-mpath
        --disable-replication
        --disable-libssh
        --disable-libudev
        --disable-iconv
        --disable-gettext
        --disable-bpf
      # Accelerators
        --disable-hax
        --disable-hvf
        --disable-nvmm
        --disable-whpx
      # Tracing
        --enable-trace-backends=nop # dtrace / ftrace / log / nop / simple / syslog / ust
        --disable-gprof
      # Tools / Testing / Extras
        --disable-tools
        --disable-fuzzing
        --disable-plugins
     # Firmware
        --disable-blobs                        # (old)
        --disable-install-blobs
    # User-mode
    --disable-linux-user
        ${QEMU_ENABLE_DEBUG}
        BUILD_COMMAND make -j ${CMAKE_BUILD_PARALLEL_LEVEL} qemu-system-aarch64

        INSTALL_COMMAND ""                      # no install step
        BUILD_ALWAYS OFF                        # don’t rebuild every time
        UPDATE_DISCONNECTED 1                   # don’t try to git/pull
        BUILD_BYPRODUCTS ${QEMU_BINARY_DIR}/qemu-system-aarch64
        LOG_CONFIGURE 1
        LOG_BUILD 1
        USES_TERMINAL_CONFIGURE 1
        USES_TERMINAL_BUILD     1
)

##################################
########## Build VPSim ###########
##################################

set(VPSIM_SOURCE_DIR ${CMAKE_SOURCE_DIR}/vpsim-systemc)
set(VPSIM_BINARY_DIR ${CMAKE_BINARY_DIR}/vpsim-build)

add_subdirectory(${VPSIM_SOURCE_DIR} ${VPSIM_BINARY_DIR})







##################################
### Generate release env #########
##################################

# Define paths
set(OUTPUT_FOLDER "${CMAKE_BINARY_DIR}/vpsim-release/")
set(QEMU_OUTPUT  "${OUTPUT_FOLDER}/lib/qemu/vpsim-qemu.so")
set(VPSIM_OUTPUT "${OUTPUT_FOLDER}/bin/vpsim")

MESSAGE(STATUS "VPSIM_OUTPUT IS ${VPSIM_OUTPUT}")
# Custom command to copy QEMU binary
add_custom_command(
    OUTPUT ${QEMU_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E copy
            ${QEMU_BINARY_DIR}/aarch64-softmmu/qemu-system-aarch64
            ${QEMU_OUTPUT}
    DEPENDS qemu
    COMMENT "Copying QEMU binary"
)

# Custom command to copy VPSim binary
add_custom_command(
    OUTPUT ${VPSIM_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E copy
            ${VPSIM_BINARY_DIR}/vpsim
            ${VPSIM_OUTPUT}
    DEPENDS vpsim
    COMMENT "Copying VPSim binary"
)

set(PYTHON_SRC_DIR  "${CMAKE_SOURCE_DIR}/vpsim-release/Python")
set(PYTHON_DST_DIR  "${OUTPUT_FOLDER}/Python")

add_custom_target(link_python ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory "${OUTPUT_FOLDER}"
    COMMAND ${CMAKE_COMMAND} -E create_symlink ${PYTHON_SRC_DIR} ${PYTHON_DST_DIR}
    COMMENT "Linking Python directory into build tree"
)


add_subdirectory(tests)

# Optional: main target that builds everything
add_custom_target(install_vpsim ALL
    DEPENDS ${VPSIM_OUTPUT} link_python
    COMMENT "Built QEMU, VPSim, and copied artifacts"
)
add_custom_target(install_qemu ALL
    DEPENDS ${QEMU_OUTPUT} link_python
    COMMENT "Built QEMU, VPSim, and copied artifacts"
)
add_custom_target(default ALL
    DEPENDS ${QEMU_OUTPUT} ${VPSIM_OUTPUT} link_python
    COMMENT "Built QEMU, VPSim, and copied artifacts"
)
