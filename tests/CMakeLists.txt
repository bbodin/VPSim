enable_testing()

message(STATUS "")
message(STATUS "==== Collecting ELF and XML files ====")

# ELF files
file(GLOB TEST_ELFS "${CMAKE_CURRENT_SOURCE_DIR}/elf/*.elf")
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

message(STATUS "")
message(STATUS "==== Generating tests ====")

# Loop over every XML × ELF combination
foreach(XML_IN ${TEST_XMLS})

    get_filename_component(XML_BASE ${XML_IN} NAME_WE)

    foreach(ELF ${TEST_ELFS})
        get_target_property(VPSIM_LOCATION vpsim BINARY_DIR)
        set(ABS_VPSIM_LOCATION "${VPSIM_OUTPUT}")
        set(ABS_QEMU_LOCATION "${QEMU_OUTPUT}")
        get_filename_component(ELF_BASE ${ELF} NAME_WE)
        set(VPSIMLIBPATH  ${ABS_QEMU_LOCATION})
        message(STATUS "Absolute path to vpsim lib: ${VPSIMLIBPATH}")
        # Values for replacement (for configure_file)
        
        # Generated output
        file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/results")
        set(OUTPUT_FILE "${CMAKE_BINARY_DIR}/results/${XML_BASE}_with_${ELF_BASE}.out")

        # Golden/reference file
        set(GOLDEN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${XML_BASE}_with_${ELF_BASE}.out")


        set(ELF_FILE  ${ELF}) 

        # Create directory for generated XML 
        file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/generated")

        # Output XML file
        set(GENERATED_XML "${CMAKE_BINARY_DIR}/generated/${XML_BASE}_with_${ELF_BASE}.xml")

        message(STATUS "Generating XML:")
        message(STATUS "  Template: ${XML_IN}")
        message(STATUS "  Output:   ${GENERATED_XML}")

        configure_file(
            ${XML_IN}
            ${GENERATED_XML}
            @ONLY
        )

        # Create a unique test name
        set(TESTNAME "vpsim.run_${XML_BASE}_with_${ELF_BASE}")

        message(STATUS "Registering test: ${TESTNAME}")
        message(STATUS "  Command: ${ABS_VPSIM_LOCATION} --run ${GENERATED_XML}")

        add_custom_command(
            OUTPUT ${OUTPUT_FILE}
            COMMAND ${ABS_VPSIM_LOCATION} --run ${GENERATED_XML} || true
            DEPENDS ${GENERATED_XML}
            COMMENT "Generating ${OUTPUT_FILE} using simulator"
        )

        add_test(
         NAME ${TESTNAME}
         COMMAND ${CMAKE_COMMAND} -E compare_files ${OUTPUT_FILE} ${GOLDEN_FILE}
        )



        set_tests_properties(${TESTNAME} PROPERTIES
            ENVIRONMENT "SYSTEMC_DISABLE_COPYRIGHT_MESSAGE=1"
            TIMEOUT 40
             DEPENDS  ${OUTPUT_FILE}
        )

        get_property(TESTS DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY TESTS)
        message(STATUS "Tests in this directory: ${TESTS}")

    endforeach()
endforeach()

message(STATUS "==== Test generation completed ====")
message(STATUS "")
