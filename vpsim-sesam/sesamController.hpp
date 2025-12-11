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

#ifndef __SESAM_CONTROLLER_H__
#define __SESAM_CONTROLLER_H__

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <iostream>
#include <iomanip>

#include "sesam_mmap.h"

/* sesam opcodes */
#define SESAMOP_QUIT            0x42
#define SESAMOP_START_BENCH     0x52
#define SESAMOP_END_BENCH       0x54
#define SESAMOP_LIST            0x20
#define SESAMOP_CLEAN_PARAMS    0x58
#define SESAMOP_START_PARAM     0x62
#define SESAMOP_END_PARAM       0x72
#define SESAMOP_EXECUTE_PARAMS  0x78

void sesam_quit() {
  *((uint8_t *)(sesam_mem)) = SESAMOP_QUIT;
};

void sesam_start_bench(){
  *((uint8_t *)(sesam_mem)) = SESAMOP_START_BENCH;
}

void sesam_list_component(){
  *((uint8_t *)(sesam_mem)) = SESAMOP_LIST;
  uint8_t outReady = 0;
  char res;
  while(!outReady) {
      outReady = *((uint8_t *)(sesam_mem) + 2);
  }
  while (outReady) {
      res = *((uint8_t *)(sesam_mem) + 3);
      while (res != '\0'){
          printf("%c", res);
          res = *((uint8_t *)(sesam_mem) + 3);
      }
      printf("\n");
      
      outReady = *((uint8_t *)(sesam_mem) + 2);
  }
}

void sesam_end_bench(){
  *((uint8_t *)(sesam_mem)) = SESAMOP_END_BENCH;
  char c = *((uint8_t *)(sesam_mem) + 1);
  while (c != '\0') {
    printf("%c",c);
    c = *((uint8_t *)(sesam_mem) + 1);
  } 
}

void sesam_get_name(int n, char name[30]) {
  *((uint8_t *)(sesam_mem)) = SESAMOP_CLEAN_PARAMS;
  *((uint8_t *)(sesam_mem)) = SESAMOP_START_PARAM;
  for (int i = 0; i < n; i++) {
    *((uint8_t *)(sesam_mem + 1)) = name[i];
  }
  *((uint8_t *)(sesam_mem)) = SESAMOP_END_PARAM;
}

void sesam_exec_command(int nb_param, char parameter[10][30]) {
  *((uint8_t *)(sesam_mem)) = SESAMOP_CLEAN_PARAMS;
  for (int i = 0; i < nb_param; ++i) {
    int j = 0;
    *((uint8_t *)(sesam_mem)) = SESAMOP_START_PARAM;

    while (parameter[i][j] != '\0') {
      *((uint8_t *)(sesam_mem + 1)) = parameter[i][j];
      ++j;
    }
    *((uint8_t *)(sesam_mem)) = SESAMOP_END_PARAM;
  }
  *((uint8_t *)(sesam_mem)) = SESAMOP_EXECUTE_PARAMS;
}

#endif // __SESAM_H__
