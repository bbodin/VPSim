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

#message(STATUS "")
#message(STATUS "==== Generating tests ====")

# Loop over every XML × ELF combination
foreach(XML_IN ${TEST_XMLS})

    get_filename_component(XML_BASE ${XML_IN} NAME_WE)

    foreach(ELF ${TEST_ELFS})
        get_target_property(VPSIM_LOCATION vpsim BINARY_DIR)
        set(ABS_VPSIM_LOCATION "${VPSIM_OUTPUT}")
        set(ABS_QEMU_LOCATION "${QEMU_OUTPUT}")
        get_filename_component(ELF_BASE ${ELF} NAME_WE)
        #message(STATUS "Absolute path to vpsim lib: ${VPSIMLIBPATH}")
        # Values for replacement (for configure_file)
        
        # XML variables to replace
        set(LOG_DIRECTORY "${CMAKE_BINARY_DIR}/results/")
        file(MAKE_DIRECTORY "${LOG_DIRECTORY}")
        
        set(VPSIMLIBPATH  ${ABS_QEMU_LOCATION})
        set(RUN_FILE "${LOG_DIRECTORY}/${XML_BASE}_with_${ELF_BASE}_run.log")
        set(STATS_FILE "${LOG_DIRECTORY}/${XML_BASE}_with_${ELF_BASE}_stats.log")
        set(TRACE_FILE "${LOG_DIRECTORY}/${XML_BASE}_with_${ELF_BASE}_trace.log")
        set(GOLDEN_RUN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${XML_BASE}_with_${ELF_BASE}_run.log")
        set(GOLDEN_STATS_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${XML_BASE}_with_${ELF_BASE}_stats.log")
        set(GOLDEN_TRACE_FILE "${CMAKE_CURRENT_SOURCE_DIR}/golden/${XML_BASE}_with_${ELF_BASE}_trace.log")
        set(ELF_FILE  ${ELF}) 

        

        # Create directory for generated XML 
        file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/generated")

        # Output XML file
        set(GENERATED_XML "${CMAKE_BINARY_DIR}/generated/${XML_BASE}_with_${ELF_BASE}.xml")

        #message(STATUS "Generating XML:")
        #message(STATUS "  Template: ${XML_IN}")
        #message(STATUS "  Output:   ${GENERATED_XML}")

        configure_file(
            ${XML_IN}
            ${GENERATED_XML}
            @ONLY
        )

        # Create a unique test name
        set(TESTNAME "vpsim.run_${XML_BASE}_with_${ELF_BASE}")

        #message(STATUS "Registering test: ${TESTNAME}")
        #message(STATUS "  Command: ${ABS_VPSIM_LOCATION} --run ${GENERATED_XML}")

        add_test(
            NAME ${TESTNAME}_run
            COMMAND  ${ABS_VPSIM_LOCATION} --run ${GENERATED_XML}
        )
        set_tests_properties(${TESTNAME}_run PROPERTIES DEPENDS ${GENERATED_XML})
        set_tests_properties(${TESTNAME}_run PROPERTIES TIMEOUT 15)
        set_tests_properties(${TESTNAME}_run PROPERTIES ENVIRONMENT SYSTEMC_DISABLE_COPYRIGHT_MESSAGE=1)

        get_property(TESTS DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY TESTS)
        #message(STATUS "Tests in this directory: ${TESTS}")

    endforeach()
endforeach()

message(STATUS "==== Test generation completed ====")
message(STATUS "")
