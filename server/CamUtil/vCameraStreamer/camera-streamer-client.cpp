#include <arpa/inet.h>
#include <chrono>
#include <fcntl.h>
#include <iostream>
#include <opencv2/opencv.hpp>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <vector>

#ifndef PORT
#define PORT 9000
#endif

#ifndef BUFFER_SIZE
#define BUFFER_SIZE 65536
#endif

#ifndef TIMEOUT_USEC
#define TIMEOUT_USEC 33300
#endif

#define DEBUG

int main() {
  // Create UDP socket
  int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
  if (sockfd < 0) {
    std::cerr << "Error: Could not create socket" << std::endl;
    return -1;
  }

  // Set socket timeout
  struct timeval timeout;
  timeout.tv_sec = 0;             // Set to 0 seconds
  timeout.tv_usec = TIMEOUT_USEC; // Set to 33 milliseconds
  if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) <
      0) {
    std::cerr << "Error: Could not set socket timeout" << std::endl;
    close(sockfd);
    return -1;
  }

  // Setup UDP address
  struct sockaddr_in server_addr;
  memset(&server_addr, 0, sizeof(server_addr));
  server_addr.sin_family = AF_INET;
  server_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); // Server IP address
  server_addr.sin_port = htons(PORT);

  // Send request for data
  const char *request = "data";

  struct sockaddr_in from_addr;
  socklen_t from_len = sizeof(from_addr);
  int frame_size;
  std::vector<uchar> frame_buffer(BUFFER_SIZE);

  cv::Mat frame;

  std::chrono::high_resolution_clock::time_point start, end;
  std::chrono::duration<double, std::milli> elapsed;

  size_t ret;

  while (true) {
    start = std::chrono::high_resolution_clock::now();

    ret = sendto(sockfd, request, strlen(request), 0,
                 (struct sockaddr *)&server_addr, sizeof(server_addr));

    // Receive frame size
    ret = recvfrom(sockfd, &frame_size, sizeof(frame_size), 0,
                   (struct sockaddr *)&from_addr, &from_len);
    if (ret < 0) {
      //   if (errno == EAGAIN || errno == EWOULDBLOCK) {
      //     std::cerr << "Timeout: Failed to receive frame size" << std::endl;
      //   } else {
      //     std::cerr << "Error: Failed to receive frame size" << std::endl;
      //   }
      continue;
    }

    if (frame_size <= 0 || frame_size > BUFFER_SIZE) {
      //   std::cerr << "Error: Invalid frame size received: " << frame_size
      //             << std::endl;
      continue;
    }

    // Fill buffer with zeroes before receiving new data
    std::memset(frame_buffer.data(), 0, BUFFER_SIZE);

    // Receive frame data
    ret = recvfrom(sockfd, frame_buffer.data(), frame_size, 0,
                   (struct sockaddr *)&from_addr, &from_len);
    if (ret < 0) {
      //   if (errno == EAGAIN || errno == EWOULDBLOCK) {
      //     std::cerr << "Timeout: Failed to receive frame data" << std::endl;
      //   } else {
      //     std::cerr << "Error: Failed to receive frame data" << std::endl;
      //   }
      continue;
    }

    // Decode JPEG image
    frame = cv::imdecode(frame_buffer, cv::IMREAD_COLOR);
    if (frame.empty()) {
      //   std::cerr << "Error: Failed to decode image" << std::endl;
      continue;
    }

    // Display the frame
    cv::imshow("UDP Client", frame);
    if (cv::waitKey(1) == 'q') {
      break;
    }

    end = std::chrono::high_resolution_clock::now();
    elapsed =
        std::chrono::duration_cast<std::chrono::duration<double, std::milli>>(
            end - start);
    std::cout << "Time elapsed: " << elapsed.count() << " ms" << std::endl;
  }

  // Clean up
  close(sockfd);
  cv::destroyAllWindows();

  return 0;
}
