# Find OpenCV and OpenMP
find_package(OpenCV REQUIRED)

# Add the executable
add_executable(vstreamer-server camera-streamer-server.cpp)
add_executable(vstreamer-client camera-streamer-client.cpp)

# Link OpenCV libraries
target_link_libraries(vstreamer-server PRIVATE ${OpenCV_LIBS})
target_link_libraries(vstreamer-client PRIVATE ${OpenCV_LIBS})

# Link V4L2 library
find_library(V4L2_LIB v4l2 REQUIRED)
target_link_libraries(vstreamer-server PRIVATE ${V4L2_LIB})

# Find and include V4L2 headers
find_path(V4L2_INCLUDE_DIR NAMES linux/videodev2.h)
if(V4L2_INCLUDE_DIR)
    include_directories(${V4L2_INCLUDE_DIR})
endif()

# Set C++ standard
set_target_properties(vstreamer-server PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED YES)
set_target_properties(vstreamer-client PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED YES)

set_target_properties(vstreamer-client PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/bin/Debug
    RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/bin/Release
    ARCHIVE_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/lib/Debug
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/lib/Release
    LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/lib/Debug
    LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/lib/Release    
)

set_target_properties(vstreamer-server PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/bin/Debug
    RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/bin/Release
    ARCHIVE_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/lib/Debug
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/lib/Release
    LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/lib/Debug
    LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/lib/Release    
)