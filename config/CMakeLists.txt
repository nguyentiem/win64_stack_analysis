# -----------------------------------------------------------------------------
# @file: CMakeLists.txt
# @copyright:
# Copyright (C) 2025 Sagemcom. All rights reserved.
#
# @licence:
# The source code contained herein includes proprietary
# information belonging to Sagemcom.
# The source code and program may be used and/or copied
# only with the written permission of Sagemcom,
# or in accordance with the terms and conditions
# stipulated in the agreement/contract under which the programs
# have been supplied.
#
# @author:
# Dev : NGUYEN PHUONG Nam
#
# @brief:
# CMake build configuration for the shared library, including Cellular submodule
# sources and stubbing sources
#
# @date:
# 2025-11-12
# -----------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.23)

# C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# C++ standard
set(CMAKE_CXX_STANDARD 98)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

project(CMCELL)

option(CMCELL_ENABLE_TESTS "Build unit tests" OFF)
option(CMCELL_ENABLE_STACK_ANALYSIS
    "Emit GCC callgraph and stack-usage artifacts (.ci/.su)" OFF)

# Base directory
set(CELLULAR_BASE_DIR "${CMAKE_SOURCE_DIR}/..")
set(PLATFORM_DIR "${CMAKE_SOURCE_DIR}/platform")
set(PLATFORM_WINDOWS_DIR "${CMAKE_SOURCE_DIR}/platform/windows")
set(PLATFORM_STDOUT_SYNC_DIR "${CMAKE_SOURCE_DIR}/platform/stdout_sync")
set(MAIN_DIR "${CMAKE_SOURCE_DIR}/main")
set(CORE_DIR "${CMAKE_SOURCE_DIR}/core")
set(LOG_DIR "${CMAKE_SOURCE_DIR}/log")
set(CMD_DIR "${CMAKE_SOURCE_DIR}/cmd")
set(CMD_REPR_DIR "${CMAKE_SOURCE_DIR}/cmd/cmd_repr")
set(SERIALIZER_DIR "${CMAKE_SOURCE_DIR}/serializer")
set(TRANSPORT_DIR "${CMAKE_SOURCE_DIR}/transport")

# cJSON directory
set(CJSON_DIR "${CMAKE_SOURCE_DIR}/third_party/cjson")

# LibSerialPort directory
set(LIBSERIALPORT_DIR "${CMAKE_SOURCE_DIR}/third_party/libserialport")

# Base64 directory
set(BASE64_DIR "${CMAKE_SOURCE_DIR}/third_party/base64")

# Core layer source and include path
set(CORE_SRC ${CORE_DIR}/src)
set(CORE_INC ${CORE_DIR}/inc)

# Log layer source and include path
set(LOG_SRC ${LOG_DIR}/src)
set(LOG_INC ${LOG_DIR}/inc)

# Command (cmd) layer source and include path
set(CMD_SRC ${CMD_DIR}/src)
set(CMD_INC ${CMD_DIR}/inc)

# Command (cmd) Representation source and include path
set(CMD_REPR_SRC ${CMD_REPR_DIR}/src)
set(CMD_REPR_INC ${CMD_REPR_DIR}/inc)

# Serializer layer source and include path
set(SERIALIZER_SRC ${SERIALIZER_DIR}/src)
set(SERIALIZER_INC ${SERIALIZER_DIR}/inc)

# Transport layer source and include path
set(TRANSPORT_SRC ${TRANSPORT_DIR}/src)
set(TRANSPORT_INC ${TRANSPORT_DIR}/inc)

# CMCELL source and include path
set(CMCELL_COM_SRC ${CELLULAR_BASE_DIR}/com/src)
set(CMCELL_COM_INC ${CELLULAR_BASE_DIR}/com/inc)
set(CMCELL_CELLULAR_SRC ${CELLULAR_BASE_DIR}/cellular/src)
set(CMCELL_CELLULAR_INC ${CELLULAR_BASE_DIR}/cellular/inc)
set(CMCELL_MODEM_SRC ${CELLULAR_BASE_DIR}/modem/src)
set(CMCELL_MODEM_INC ${CELLULAR_BASE_DIR}/modem/inc)

# Platform Windows module source and include path
set(PLATFORM_WINDOWS_SRC ${PLATFORM_WINDOWS_DIR}/src)
set(PLATFORM_WINDOWS_INC ${PLATFORM_WINDOWS_DIR}/inc)

# Platform STDOUT Synchronization module source and include path
set(PLATFORM_STDOUT_SYNC_SRC ${PLATFORM_STDOUT_SYNC_DIR}/src)
set(PLATFORM_STDOUT_SYNC_INC ${PLATFORM_STDOUT_SYNC_DIR}/inc)

# Declare the configuration for Transport Type
set(TRANSPORT
    ""
    CACHE STRING "Emulator Transport type"
)

# Provide the valid values for the TRANSPORT
set_property(CACHE TRANSPORT PROPERTY STRINGS
    "stdio"
    "named_pipe"
    "socket"
)

# Declare the configuration for Serializer type
set(SERIALIZER
    ""
    CACHE STRING "Emulator Serializer type"
)

# Provide the valid values for the SERIALIZER
set_property(CACHE SERIALIZER PROPERTY STRINGS
    "cli"
    "json"
)

# Project include directories
include_directories(
    "${CORE_INC}"
    "${LOG_INC}"
    "${CMD_INC}"
    "${CMD_REPR_INC}"
    "${SERIALIZER_INC}"
    "${TRANSPORT_INC}"
    "${CMCELL_COM_INC}"
    "${CMCELL_CELLULAR_INC}"
    "${CMCELL_MODEM_INC}"
    "${CJSON_DIR}"
    "${LIBSERIALPORT_DIR}"
    "${BASE64_DIR}"
    "${PLATFORM_WINDOWS_INC}"
    "${PLATFORM_STDOUT_SYNC_INC}"
)

if (CMCELL_ENABLE_TESTS)
    enable_testing()
    add_subdirectory(unit_tests)
else()
    add_executable(cmcell)

    # Project source files
    target_sources(cmcell PRIVATE
        # Entry point
        "${MAIN_DIR}/main.c"

        # Core layer source files
        "${CORE_SRC}/core.c"

        # Log layer source files
        "${LOG_SRC}/log.c"

        # Command (cmd) layer source files
        "${CMD_SRC}/cmd.c"
        "${CMD_SRC}/cmd_cmcell.c"
        "${CMD_SRC}/cmd_modem_sp.c"

        # Command (cmd) Representation source files
        "${CMD_REPR_SRC}/cmd_repr.c"
        "${CMD_REPR_SRC}/cmd_repr_cell_init.c"
        "${CMD_REPR_SRC}/cmd_repr_cell_connect.c"
        "${CMD_REPR_SRC}/cmd_repr_cell_monitoring.c"
        "${CMD_REPR_SRC}/cmd_repr_cell_socket.c"
        "${CMD_REPR_SRC}/cmd_repr_cell_log.c"
        "${CMD_REPR_SRC}/cmd_repr_cell_event.c"
        "${CMD_REPR_SRC}/cmd_repr_modem_sp.c"
        "${CMD_REPR_SRC}/cmd_repr_utils.c"

        # CMCELL cellular source files
        "${CMCELL_CELLULAR_SRC}/cell_api.c"
        "${CMCELL_CELLULAR_SRC}/cell_task.c"
        "${CMCELL_CELLULAR_SRC}/cell_log.c"
        "${CMCELL_CELLULAR_SRC}/cell_connect.c"
        "${CMCELL_CELLULAR_SRC}/cell_monitoring.c"
        "${CMCELL_CELLULAR_SRC}/cell_socket.c"
        "${CMCELL_CELLULAR_SRC}/cell_dfota.c"
        "${CMCELL_CELLULAR_SRC}/cell_test.c"

        # CMCELL com source files
        "${CMCELL_COM_SRC}/cell_com.c"

        # CMCELL modem source files
        "${CMCELL_MODEM_SRC}/cell_at.c"
        "${CMCELL_MODEM_SRC}/cell_modem_common.c"
        "${CMCELL_MODEM_SRC}/cell_urc.c"
        "${CMCELL_MODEM_SRC}/cell_modem_bg95.c"
        "${CMCELL_MODEM_SRC}/cell_modem_eg915u.c"
        "${CMCELL_MODEM_SRC}/cell_modem_quectel.c"
        "${CMCELL_MODEM_SRC}/cell_modem_helper.c"
        "${CMCELL_MODEM_SRC}/cell_modem_semtech.c"
        "${CMCELL_MODEM_SRC}/cell_modem_semtech_hl7900.c"

        # Platform source files
        "${PLATFORM_DIR}/cell_os.c"
        "${PLATFORM_DIR}/cell_driver_interface.c"

        # Serializer internal source files
        "${SERIALIZER_SRC}/serializer_common.c"

        # Platform Windows specific source files
        "${PLATFORM_WINDOWS_SRC}/windows_uart.c"

        # Platform STDOUT Synchronization source files
        "${PLATFORM_STDOUT_SYNC_SRC}/stdout_sync.c"

        # Base64 source file
        "${BASE64_DIR}/base64.c"

        # cJSON source file
        "${CJSON_DIR}/cJSON.c"

        # LibSerialPort source files
        "${LIBSERIALPORT_DIR}/serialport.c"
        "${LIBSERIALPORT_DIR}/timing.c"
        "${LIBSERIALPORT_DIR}/windows.c"
    )

    # Add the TRANSPORT-specific sources
    if(TRANSPORT STREQUAL "stdio")
        target_sources(cmcell PRIVATE
            "${TRANSPORT_SRC}/transport_stdio.c"
        )

    elseif(TRANSPORT STREQUAL "named_pipe")
        ### Doesn't support in this version
        message(FATAL_ERROR
            "TRANSPORT='${TRANSPORT}' Doesn't support in this version")
        # target_sources(cmcell PRIVATE
        #     "${TRANSPORT_SRC}/transport_named_pipe.c"
        # )

    elseif(TRANSPORT STREQUAL "socket")
        ### Doesn't support in this version
        message(FATAL_ERROR
            "TRANSPORT='${TRANSPORT}' Doesn't support in this version")
        # target_sources(cmcell PRIVATE
        #     "${TRANSPORT_SRC}/transport_socket.c"
        # )

    else()
        message(FATAL_ERROR
            "Unexpected TRANSPORT='${TRANSPORT}'. "
            "Configure \"-DTRANSPORT=\" with valid values: \"stdio\", \"named_pipe\" or \"socket\"")

    endif()

    message(STATUS
        "Using TRANSPORT type = \"${TRANSPORT}\""
    )

    # Add the SERIALIZER-specific sources and
    if(SERIALIZER STREQUAL "json")
        # Remove the below message when the JSON serializer is supported.
        message(FATAL_ERROR
            "SERIALIZER='${SERIALIZER}' Doesn't support in this version")

        target_sources(cmcell PRIVATE
            "${SERIALIZER_SRC}/serializer_json.c"
        )

        target_compile_definitions(cmcell PRIVATE
            "CMD_FORMAT_JSON_ENABLE=1"
        )

    elseif(SERIALIZER STREQUAL "cli")
        target_sources(cmcell PRIVATE
            "${SERIALIZER_SRC}/serializer_cli.c"
        )

        target_compile_definitions(cmcell PRIVATE
            "CMD_FORMAT_CLI_ENABLE=1"
        )

    else()
        message(FATAL_ERROR
            "Unexpected SERIALIZER='${SERIALIZER}'. "
            "Configure \"-DSERIALIZER=\" with valid values: \"json\", \"cli\"")

    endif()

    message(STATUS
        "Using SERIALIZER type = \"${SERIALIZER}\""
    )

    # Compile flags
    target_compile_options(cmcell PRIVATE
        -O0
        -Wall
        -Wextra
        -Wno-unused-parameter
        -Wno-unused-function
        -Wno-unused-variable
    )

    if(CMCELL_ENABLE_STACK_ANALYSIS)
        if(NOT CMAKE_C_COMPILER_ID STREQUAL "GNU")
            message(FATAL_ERROR
                "CMCELL_ENABLE_STACK_ANALYSIS requires a GCC compiler; "
                "current compiler is ${CMAKE_C_COMPILER_ID}")
        endif()

        # The VCG graph contains the per-function usage from the `su` marker.
        # Keep -fstack-usage too, so the familiar standalone .su files remain
        # available for other analysis tooling.
        target_compile_options(cmcell PRIVATE -fcallgraph-info=su -fstack-usage)
    endif()

    target_compile_definitions(cmcell PRIVATE
        "SP_PRIV="  # Prevent compilation errors during the libserialport build
    )


    target_link_libraries(cmcell PRIVATE
        setupapi    # Required library for libserialport
    )

endif()
