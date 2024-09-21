#include <arpa/inet.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <opencv2/opencv.hpp>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#ifndef PORT
#define PORT 9000
#endif
#ifndef BUFFER_SIZE
#define BUFFER_SIZE 65536
#endif

#define DEVICE_NAME "virDriveCam: virDriveCam"

#define DEBUG

void getCameraIndexFromName(const char *camera_name, char *camera_device) {
  char device[20];
  struct v4l2_capability cap;
  int fd;
  while (true) {
    for (int i = 0; i < 10; ++i) { // Check first 10 video devices
      snprintf(device, sizeof(device), "/dev/video%d", i);

      fd = open(device, O_RDWR);
      if (fd == -1) {
        continue; // Skip if unable to open
      }

      if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == 0) {
        if (strcmp(camera_name, (const char *)cap.card) == 0) {
          strcpy(camera_device, device);
          close(fd);
          return;
        }

        close(fd);
      }
    }
    // Sleep for 2 seconds
    sleep(2);
    printf("Device %s not found\n", camera_name);
  }
}

int main(int argc, char **argv) {
  if (argc != 2) {
    printf("provide camera device name\n");
    return -1;
  }
  char camera_device[16];
  getCameraIndexFromName(argv[1], camera_device);

  // Open the USB camera
  cv::VideoCapture cap(camera_device);
  if (!cap.isOpened()) {
    printf("Error: Could not open camera");
    return -1;
  }

  // Set the resolution of the camera (optional)
  cap.set(cv::CAP_PROP_FRAME_WIDTH, 640);
  cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
  cap.set(cv::CAP_PROP_FPS, 60);

  // Create UDP socket
  int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
  if (sockfd < 0) {
    printf("Error: Could not create socket");
    return -1;
  }

  // Setup UDP address
  struct sockaddr_in server_addr;
  memset(&server_addr, 0, sizeof(server_addr));
  server_addr.sin_family = AF_INET;
  server_addr.sin_addr.s_addr = INADDR_ANY; // Bind to all available interfaces
  server_addr.sin_port = htons(PORT);

  // Bind the socket
  if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
    printf("Error: Could not bind socket");
    close(sockfd);
    return -1;
  }

  struct sockaddr_in client_addr;
  socklen_t client_addr_len = sizeof(client_addr);
  char buffer[BUFFER_SIZE];

  cv::Mat frame;
  std::vector<int> encoding_params;
  encoding_params.push_back(cv::IMWRITE_JPEG_QUALITY);
  encoding_params.push_back(75); // Set JPEG quality to 45

  std::vector<uchar> frame_buffer;
  frame_buffer.reserve(BUFFER_SIZE);

  std::chrono::high_resolution_clock::time_point start, end;
  std::chrono::duration<double, std::milli> elapsed;

  while (true) {
     start = std::chrono::high_resolution_clock::now();
    // cap >> frame;
    cap.read(frame);

    if (frame.empty()) {
      cap.release();
      getCameraIndexFromName(argv[1], camera_device);
      cap.open(camera_device);
      continue;
    }
     end = std::chrono::high_resolution_clock::now();
     elapsed =
         std::chrono::duration_cast<std::chrono::duration<double,
         std::milli>>(
             end - start);
      printf("reading frame: %f ms\n", elapsed.count());

    // start = std::chrono::high_resolution_clock::now();

    cv::imencode(".jpg", frame, frame_buffer, encoding_params);

    // end = std::chrono::high_resolution_clock::now();
    // elapsed =
    //     std::chrono::duration_cast<std::chrono::duration<double,
    //     std::milli>>(
    //         end - start);
    // printf("encoding took: %f ms\t", elapsed.count());

    // start = std::chrono::high_resolution_clock::now();

    int recv_len = recvfrom(sockfd, buffer, sizeof(buffer) - 1, 0,
                            (struct sockaddr *)&client_addr, &client_addr_len);
    if (recv_len < 0) {
      // printf("Error: Failed to receive data");;
      continue;
    }

    buffer[recv_len] = '\0';

    // Check if the command is "data"
    if (strcmp(buffer, "data") == 0) {
      // Send frame size
      int frame_size = frame_buffer.size();
      sendto(sockfd, &frame_size, sizeof(frame_size), 0,
             (struct sockaddr *)&client_addr, client_addr_len);

      // Send frame data
      sendto(sockfd, frame_buffer.data(), frame_size, 0,
             (struct sockaddr *)&client_addr, client_addr_len);
    }
    // end = std::chrono::high_resolution_clock::now();
    // elapsed =
    //     std::chrono::duration_cast<std::chrono::duration<double,
    //     std::milli>>(
    //         end - start);
    // printf("streaming took: %f ms\n", elapsed.count());
  }

  // Clean up
  cap.release();
  cv::destroyAllWindows();
  close(sockfd);

  return 0;
}
