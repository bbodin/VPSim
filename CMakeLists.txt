cmake_minimum_required(VERSION 3.10)

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

# target to copy artifacts to release directory
add_custom_target(copy_artifacts
    COMMAND ${CMAKE_COMMAND} -E echo "Copying vpsim and qemu artifacts to release directory"
    COMMAND ${CMAKE_COMMAND} -E copy ${QEMU_BINARY_DIR}/aarch64-softmmu/qemu-system-aarch64 ${INSTALL_RELEASE_DIR}/lib/qemu/vpsim-qemu.so
    COMMAND ${CMAKE_COMMAND} -E copy ${VPSIM_BINARY_DIR}/vpsim ${INSTALL_RELEASE_DIR}/bin
    DEPENDS qemu vpsim
)

# Custom target to build everything and copy artifacts
add_custom_target(default ALL
    DEPENDS qemu vpsim copy_artifacts
    COMMENT "Built QEMU, VPSim, and copying artifacts"
)