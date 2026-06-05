cmake_minimum_required(VERSION 3.10)

enable_testing()

# Unfortunately some dependencies are not up to date.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

project(vpsim)

##################################
##### Configure & build QEMU #####
##################################

set(QEMU7_SOURCE_DIR ${CMAKE_SOURCE_DIR}/vpsim-qemu)
set(QEMU9_SOURCE_DIR ${CMAKE_SOURCE_DIR}/vpsim-qemu9)
set(QEMU7_BINARY_DIR ${CMAKE_BINARY_DIR}/qemu7-build)
set(QEMU9_BINARY_DIR ${CMAKE_BINARY_DIR}/qemu9-build)


if(CMAKE_BUILD_TYPE STREQUAL Debug)
    message("Configuring QEMU in DEBUG mode")
    set(QEMU_ENABLE_DEBUG --enable-debug)
endif()

# Ensure the QEMU build directory exists (create it if not)
file(MAKE_DIRECTORY ${QEMU9_BINARY_DIR})

add_custom_target(qemu9
    # COMMAND ${CMAKE_COMMAND} -E echo "Checking out branch ${QEMU_BRANCH}"
    # COMMAND git checkout ${QEMU_BRANCH}
    COMMAND ${QEMU9_SOURCE_DIR}/configure --target-list=aarch64-softmmu
        --disable-sparse --disable-sdl --disable-gtk --disable-vnc --disable-xen
        --disable-brlapi --disable-vnc-sasl --disable-vnc-jpeg
        --disable-curses --disable-curl --disable-kvm --disable-bsd-user
        --disable-coroutine-pool --disable-attr --disable-docs
        --disable-spice --disable-usb-redir --disable-guest-agent --disable-cap-ng --disable-libiscsi
        --disable-libusb --disable-werror ${QEMU_ENABLE_DEBUG}
    COMMAND make libvpsim-aarch64.so
    COMMAND make contrib-plugins
    WORKING_DIRECTORY ${QEMU9_BINARY_DIR}
    BYPRODUCTS ${QEMU9_BINARY_DIR}/libvpsim-aarch64.so
)
file(MAKE_DIRECTORY ${QEMU7_BINARY_DIR})


add_custom_target(qemu7
        COMMAND ${QEMU7_SOURCE_DIR}/configure --target-list=aarch64-softmmu
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
      COMMAND make -j ${CMAKE_BUILD_PARALLEL_LEVEL} qemu-system-aarch64
      COMMAND cp ${QEMU7_BINARY_DIR}/qemu-system-aarch64 ${QEMU7_BINARY_DIR}/libvpsim-aarch64.so
      WORKING_DIRECTORY ${QEMU7_BINARY_DIR}
      BYPRODUCTS ${QEMU7_BINARY_DIR}/libvpsim-aarch64.so

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
set(QEMU7_OUTPUT  "${OUTPUT_FOLDER}/lib/qemu/vpsim-qemu7.so")
set(QEMU9_OUTPUT  "${OUTPUT_FOLDER}/lib/qemu/vpsim-qemu9.so")
set(VPSIM_OUTPUT "${OUTPUT_FOLDER}/bin/vpsim")

MESSAGE(STATUS "VPSIM_OUTPUT IS ${VPSIM_OUTPUT}")
# Custom command to copy QEMU binary
add_custom_command(
    OUTPUT ${QEMU_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E copy
            ${QEMU7_BINARY_DIR}/libvpsim-aarch64.so
            ${QEMU_OUTPUT}
    DEPENDS ${QEMU7_BINARY_DIR}/libvpsim-aarch64.so
    COMMENT "Copying QEMU binary"
)
add_custom_command(
    OUTPUT ${QEMU9_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E copy
            ${QEMU9_BINARY_DIR}/libvpsim-aarch64.so
            ${QEMU9_OUTPUT}
    DEPENDS ${QEMU9_BINARY_DIR}/libvpsim-aarch64.so
    COMMENT "Copying QEMU binary"
)
add_custom_command(
    OUTPUT ${QEMU7_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E copy
            ${QEMU7_BINARY_DIR}/libvpsim-aarch64.so
            ${QEMU7_OUTPUT}
    DEPENDS ${QEMU7_BINARY_DIR}/libvpsim-aarch64.so
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

set(PYTHON_SRC_DIR  "${CMAKE_SOURCE_DIR}/vpsim-python")
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
    DEPENDS ${QEMU_OUTPUT} ${QEMU7_OUTPUT} ${QEMU9_OUTPUT} ${VPSIM_OUTPUT} link_python
    COMMENT "Built QEMU, VPSim, and copied artifacts"
)


# manage the make install

install(FILES ${VPSIM_OUTPUT} DESTINATION bin)
install(FILES ${QEMU_OUTPUT} DESTINATION lib/vpsim)
install(DIRECTORY ${PYTHON_SRC_DIR}/ DESTINATION share/vpsim/Python)