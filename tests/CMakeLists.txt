cmake_minimum_required(VERSION 3.10)

project(vpsim_tests)

# Set policy to avoid warnings about non-existent targets
cmake_policy(SET CMP0045 NEW)

enable_testing()

# ============================================================
# ARM v8 ELF Compilation Setup
# ============================================================

# ARM v8 Toolchain Configuration
set(CC_PREFIX "aarch64-linux-gnu")
find_program(AS ${CC_PREFIX}-as REQUIRED)
find_program(CC ${CC_PREFIX}-gcc REQUIRED)
find_program(LD ${CC_PREFIX}-ld REQUIRED)

# Compiler flags (matching Makefile)
set(ASFLAGS "-march=armv8-a+sve")
set(INCLUDE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/src_c/include")
set(CFLAGS "-march=armv8-a+sve" "-ffreestanding" "-Wall" "-Wextra" "-Werror" "-c" "-fno-stack-protector" "-I${INCLUDE_PATH}")
set(LDFLAGS "-T" "${CMAKE_CURRENT_SOURCE_DIR}/linker/linker.ld")

# Output directory for object files and ELFs
set(ELF_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/elf_build")
file(MAKE_DIRECTORY ${ELF_BUILD_DIR})

# ============================================================
# Assemble _multicore.S (common for all test cases)
# ============================================================

add_custom_command(
    OUTPUT ${ELF_BUILD_DIR}/_multicore.o
    COMMAND ${AS} ${ASFLAGS} ${CMAKE_CURRENT_SOURCE_DIR}/src_asm/_multicore.S -o ${ELF_BUILD_DIR}/_multicore.o
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src_asm/_multicore.S
    COMMENT "Assembling _multicore.S"
)

# ============================================================
# Compile and Link C Source Files
# ============================================================

# Separate QEMU and SESAM test sources
file(GLOB QEMU_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src_c/testcase_qemu_*.c")
file(GLOB SESAM_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src_c/testcase_sesam_*.c")

# Function to compile and link a list of sources
function(compile_and_link_sources SOURCES EXTRA_INCLUDE_DIRS)
    foreach(C_SOURCE ${SOURCES})
        get_filename_component(C_BASE ${C_SOURCE} NAME_WE)
        set(ELF_NAME "kernel_${C_BASE}.elf")

        # Compile
        if(EXTRA_INCLUDE_DIRS)
            add_custom_command(
                OUTPUT ${ELF_BUILD_DIR}/${C_BASE}.o
                COMMAND ${CC} ${CFLAGS} -I${EXTRA_INCLUDE_DIRS} ${C_SOURCE} -o ${ELF_BUILD_DIR}/${C_BASE}.o
                DEPENDS ${C_SOURCE}
                COMMENT "Compiling ${C_SOURCE}"
            )
        else()
            add_custom_command(
                OUTPUT ${ELF_BUILD_DIR}/${C_BASE}.o
                COMMAND ${CC} ${CFLAGS} ${C_SOURCE} -o ${ELF_BUILD_DIR}/${C_BASE}.o
                DEPENDS ${C_SOURCE}
                COMMENT "Compiling ${C_SOURCE}"
            )
        endif()

        # Link
        add_custom_command(
                OUTPUT ${ELF_BUILD_DIR}/${ELF_NAME}
                COMMAND ${LD} ${LDFLAGS}
                        ${ELF_BUILD_DIR}/_multicore.o
                        ${ELF_BUILD_DIR}/${C_BASE}.o
                        -o ${ELF_BUILD_DIR}/${ELF_NAME}
                DEPENDS ${ELF_BUILD_DIR}/_multicore.o ${ELF_BUILD_DIR}/${C_BASE}.o ${CMAKE_CURRENT_SOURCE_DIR}/linker/linker.ld
                COMMENT "Linking ${ELF_NAME}"
        )


        # Track outputs - use PARENT_SCOPE to propagate to caller
        list(APPEND GENERATED_ELFS ${ELF_BUILD_DIR}/${ELF_NAME})
        list(APPEND ALL_ELF_OUTPUTS ${ELF_BUILD_DIR}/${ELF_NAME} ${ELF_BUILD_DIR}/${C_BASE}.o)
    endforeach()

    # Propagate the lists back to parent scope
    set(GENERATED_ELFS ${GENERATED_ELFS} PARENT_SCOPE)
    set(ALL_ELF_OUTPUTS ${ALL_ELF_OUTPUTS} PARENT_SCOPE)
endfunction()

# Initialize lists
set(GENERATED_ELFS "")
set(ALL_ELF_OUTPUTS "")

# Compile and link QEMU test cases (always available)
compile_and_link_sources("${QEMU_SOURCES}" "")
compile_and_link_sources("${SESAM_SOURCES}" "")


# Also add the multicore object to the outputs
list(APPEND ALL_ELF_OUTPUTS ${ELF_BUILD_DIR}/_multicore.o)

# ============================================================
# Create a target to build all ELFs
# ============================================================

add_custom_target(compile_elfs ALL
    DEPENDS ${ALL_ELF_OUTPUTS}
    COMMENT "Compiling all test ELF files"
)



# ===================================================================
# Direct QEMU System Tests (using local qemu-system-aarch64 directly)
# ===================================================================

find_program(QEMU_SYSTEM_AARCH64 qemu-system-aarch64 REQUIRED)

foreach(ELF ${GENERATED_ELFS})
    get_filename_component(ELF_BASE ${ELF} NAME_WE)

    # Create a test name for direct qemu execution
    set(QEMU_TEST_NAME "qemu_local_${ELF_BASE}")

    add_test(
        NAME ${QEMU_TEST_NAME}
        COMMAND ${QEMU_SYSTEM_AARCH64} -M virt -cpu max -nographic -semihosting -smp 4 -kernel ${ELF}
    )
    set_tests_properties(${QEMU_TEST_NAME} PROPERTIES TIMEOUT 5)
endforeach()






















message(STATUS "")
message(STATUS "==== Collecting ELF and XML files ====")

# ELF files - use generated ELFs instead of pre-built ones
set(TEST_ELFS ${GENERATED_ELFS})
message(STATUS "Found ELF files:")
foreach(e ${TEST_ELFS})
    message(STATUS "  - ${e}")
endforeach()
if(TEST_ELFS STREQUAL "")
    message(WARNING "No ELF found in ${CMAKE_CURRENT_SOURCE_DIR}/elf/*.elf")
endif()

# XML template inputs (*.xml.in)
file(GLOB TEST_XMLS "${CMAKE_CURRENT_SOURCE_DIR}/configs/*.xml.in")
message(STATUS "Found XML template files:")
foreach(x ${TEST_XMLS})
    message(STATUS "  - ${x}")
endforeach()
if(TEST_XMLS STREQUAL "")
    message(WARNING "No XML templates found in ${CMAKE_CURRENT_SOURCE_DIR}/configs/*.xml.in")
endif()

#message(STATUS "")
#message(STATUS "==== Generating tests ====")

# Skip vpsim tests if VPSIM_OUTPUT is not defined
if(DEFINED VPSIM_OUTPUT AND NOT VPSIM_OUTPUT STREQUAL "" )
    # Loop over every XML × ELF combination
    foreach(XML_IN ${TEST_XMLS})

        get_filename_component(XML_BASE ${XML_IN} NAME_WE)

        foreach(ELF ${TEST_ELFS})

            get_filename_component(ELF_BASE ${ELF} NAME_WE)

            foreach(QEMU_VERSION 7 9)
            set(ABS_QEMU_LOCATION "${QEMU${QEMU_VERSION}_OUTPUT}")

            set(UNIT_TEST_NAME "${XML_BASE}_qemu_${QEMU_VERSION}_with_${ELF_BASE}")
            # Only get vpsim target properties if it exists
            if(TARGET vpsim)
                get_target_property(VPSIM_LOCATION vpsim BINARY_DIR)
            endif()
            set(ABS_VPSIM_LOCATION "${VPSIM_OUTPUT}")

            #message(STATUS "Absolute path to vpsim lib: ${VPSIMLIBPATH}")
            # Values for replacement (for configure_file)
            
            # XML variables to replace
            set(LOG_DIRECTORY "${CMAKE_BINARY_DIR}/results/${UNIT_TEST_NAME}/")
            file(MAKE_DIRECTORY "${LOG_DIRECTORY}")
            
            set(VPSIMLIBPATH  ${ABS_QEMU_LOCATION})
            set(RUN_FILE "${LOG_DIRECTORY}/${UNIT_TEST_NAME}_run.log")
            set(STATS_FILE "${LOG_DIRECTORY}/${UNIT_TEST_NAME}_stats.log")
            set(TRACE_FILE "${LOG_DIRECTORY}/${UNIT_TEST_NAME}_trace.log")
            set(GOLDEN_RUN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${UNIT_TEST_NAME}_run.log")
            set(GOLDEN_STATS_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${UNIT_TEST_NAME}_stats.log")
            set(GOLDEN_TRACE_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${UNIT_TEST_NAME}_trace.log")
            set(ELF_FILE  ${ELF}) 

            

            # Create directory for generated XML 
            file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/generated")

            # Output XML file
            set(GENERATED_XML "${CMAKE_BINARY_DIR}/generated/${UNIT_TEST_NAME}.xml")

            #message(STATUS "Generating XML:")
            #message(STATUS "  Template: ${XML_IN}")
            #message(STATUS "  Output:   ${GENERATED_XML}")

            configure_file(
                ${XML_IN}
                ${GENERATED_XML}
                @ONLY
            )

            # Create a unique test name
            set(TESTNAME "vpsim.run_${UNIT_TEST_NAME}")

            #message(STATUS "Registering test: ${TESTNAME}")
            #message(STATUS "  Command: ${ABS_VPSIM_LOCATION} --run ${GENERATED_XML}")

            add_test(
                NAME ${TESTNAME}_run
                COMMAND  ${ABS_VPSIM_LOCATION} --run ${GENERATED_XML}
            )
            set_tests_properties(${TESTNAME}_run PROPERTIES DEPENDS ${GENERATED_XML})
            set_tests_properties(${TESTNAME}_run PROPERTIES TIMEOUT 240)
            set_tests_properties(${TESTNAME}_run PROPERTIES ENVIRONMENT SYSTEMC_DISABLE_COPYRIGHT_MESSAGE=1)

            get_property(TESTS DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY TESTS)
            #message(STATUS "Tests in this directory: ${TESTS}")        
        endforeach()

    endforeach()
endforeach()
else()
    message(STATUS "VPSIM_OUTPUT not defined, skipping vpsim tests")
endif()

message(STATUS "==== Test generation completed ====")
message(STATUS "")
