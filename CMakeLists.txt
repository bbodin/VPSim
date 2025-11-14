cmake_minimum_required(VERSION 3.10)
enable_testing()
# Unfortunately some dependencies are not up to date.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

project(vpsim)

set(INSTALL_RELEASE_DIR ${CMAKE_SOURCE_DIR}/vpsim-release)

##### Configure & build QEMU #####
set(QEMU_SOURCE_DIR ${CMAKE_SOURCE_DIR}/vpsim-qemu)
set(QEMU_BINARY_DIR ${CMAKE_BINARY_DIR}/qemu-build)
# set(QEMU_BRANCH "qemu-for-vpsim")

if(CMAKE_BUILD_TYPE STREQUAL Debug)
    set(QEMU_ENABLE_DEBUG --enable-debug)
endif()

# Ensure the QEMU build directory exists (create it if not)
file(MAKE_DIRECTORY ${QEMU_BINARY_DIR})
include(ExternalProject)

ExternalProject_Add(qemu
        SOURCE_DIR    ${QEMU_SOURCE_DIR}
        BINARY_DIR    ${QEMU_BINARY_DIR}
        CONFIGURE_COMMAND ${QEMU_SOURCE_DIR}/configure --target-list=aarch64-softmmu
        --disable-sparse --disable-sdl --disable-gtk --disable-vnc --disable-xen
        --disable-brlapi --disable-vnc-sasl --disable-vnc-jpeg --disable-vnc-png
        --disable-curses --disable-curl --disable-kvm --disable-bsd-user
        --disable-pie --disable-coroutine-pool --disable-attr --disable-blobs --disable-docs
        --disable-spice --disable-usb-redir --disable-guest-agent --disable-cap-ng --disable-libiscsi
        --disable-libusb --disable-werror ${QEMU_ENABLE_DEBUG}
        # BUILD_COMMAND ${CMAKE_MAKE_PROGRAM}
        INSTALL_COMMAND ""                      # no install step
        BUILD_ALWAYS OFF                        # don’t rebuild every time
        UPDATE_DISCONNECTED 1                   # don’t try to git/pull
        BUILD_BYPRODUCTS ${QEMU_BINARY_DIR}/qemu-system-aarch64
        LOG_CONFIGURE 1
        LOG_BUILD 1
        USES_TERMINAL_CONFIGURE 1
        USES_TERMINAL_BUILD     1
)

##### Build VPSim #####

set(VPSIM_SOURCE_DIR ${CMAKE_SOURCE_DIR}/vpsim-systemc)
set(VPSIM_BINARY_DIR ${CMAKE_BINARY_DIR}/vpsim-build)

add_subdirectory(${VPSIM_SOURCE_DIR} ${VPSIM_BINARY_DIR})
# Define paths
set(QEMU_OUTPUT "${INSTALL_RELEASE_DIR}/lib/qemu/vpsim-qemu.so")
set(VPSIM_OUTPUT "${INSTALL_RELEASE_DIR}/bin/vpsim")

# Custom command to copy QEMU binary
add_custom_command(
    OUTPUT ${QEMU_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E echo "Copying QEMU to release directory"
    COMMAND ${CMAKE_COMMAND} -E copy
            ${QEMU_BINARY_DIR}/aarch64-softmmu/qemu-system-aarch64
            ${QEMU_OUTPUT}
    DEPENDS qemu
    COMMENT "Copying QEMU binary"
)

# Custom command to copy VPSim binary
add_custom_command(
    OUTPUT ${VPSIM_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E echo "Copying VPSim to release directory"
    COMMAND ${CMAKE_COMMAND} -E copy
            ${VPSIM_BINARY_DIR}/vpsim
            ${VPSIM_OUTPUT}
    DEPENDS vpsim
    COMMENT "Copying VPSim binary"
)

# Target that depends on these copied files
add_custom_target(copy_artifacts ALL
    DEPENDS ${QEMU_OUTPUT} ${VPSIM_OUTPUT}
    COMMENT "Copied QEMU and VPSim artifacts to release directory"
)


# Optional: main target that builds everything
add_custom_target(default ALL
    DEPENDS qemu vpsim copy_artifacts
    COMMENT "Built QEMU, VPSim, and copied artifacts"
)


add_subdirectory(tests)