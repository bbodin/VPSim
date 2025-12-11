/*
 * Copyright (C) 2024 Commissariat à l'énergie atomique et aux énergies alternatives (CEA)

 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at

 *    http://www.apache.org/licenses/LICENSE-2.0 

 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "sesam_mmap.h"

void *sesam_mem = NULL;
int fd;

void map_sesam_mem() {
  /* Read configuration file */
  unsigned int base_address;
  FILE *fp;

  fp = fopen("/etc/config_sesam","r");

  if (fp == NULL)
  {
    perror("Error while opening /etc/config_sesam");
    printf("Please type in your terminal 'echo [hex addr sesam_monitor] > /etc/config_sesam'\n");
    exit(1);
  }
  
  fscanf(fp, "%x", &base_address);
  fclose(fp);

  /* Open the memory device */
  fd = open("/dev/mem", O_RDWR | O_SYNC);
  if (fd < 1) {
    perror("sesam_mmap");
    exit(1);
  }

  if (base_address == 0) {
    printf("File /etc/config_sesam is empty or not in the right format\n");
    printf("Please type in your terminal 'echo [hex addr sesam_monitor] > /etc/config_sesam'\n");
    exit(1);
  }
 
  /* Map only 4 bytes */
  sesam_mem = mmap(NULL, 4, PROT_READ | PROT_WRITE, MAP_SHARED, fd, base_address);
  if (sesam_mem == MAP_FAILED)
  {
    printf("mmap failed\n");
    printf("Please check the correct address in /etc/config_sesam\n");
    exit(1);
  }
}

void unmap_sesam() {
  munmap(sesam_mem, fd);
  close(fd);
}
