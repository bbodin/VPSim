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

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <string.h>
#include <iostream>
#include <libgen.h>  // for basename()
#include <limits.h> // for PATH_MAX

#include "sesamController.hpp"

using namespace std;

void usage(){
  printf("Sesam user controller\n");
  printf("v0.2\n");
  printf("Usage: sesam <command> <parameter>\n");
  printf("\nCommand:\n");
  printf("    help\t\tShow this message\n");
  printf("    show\t\tShow component status\n");
  printf("    benchmark\t\tShow performance statistics of the executed program\n");
  printf("    quit\t\tQuit VPSim\n");
}

bool file_exists(const char *path) {
    return access(path, F_OK) == 0;
}
bool is_system_command(const char *cmd) {
    // Check if the command is a system command in the PATH
    return system((string("command -v ") + cmd + " >/dev/null 2>&1").c_str()) == 0;
}
int main(int argc, char **argv)
{
  char cmd[20];
  char parameter[10][30]; /* Maximum 10 parameters */
  int nb_param;

  int i;

  if (argc < 2) {
    usage();
    exit(1);
  }

  /* Copy input variables to internal */
  strcpy(cmd, argv[1]);

  map_sesam_mem();

  /* Verify command */
  if (strcmp(cmd,"help") == 0) {
    printf("Help: ");
    usage();
    return 0;
  }
  else if (strcmp(cmd,"quit") == 0) {
    /* Call function to quit vpsim */
    printf("Quitting VPSIM environment ...\n");
    sesam_quit();
  }
  else if (strcmp(cmd,"list") == 0) {
    /* Call function to list vpsim components */
    printf("Components in VPSIM: \n");
    sesam_list_component();
  }
  else if (strcmp(cmd,"benchmark") == 0) {
    if (argc < 3) {
      printf("Please put your benchmark application...");
      printf("Usage: sesam benchmark <name_of_application>");
      exit(1);
    }

    ostringstream s;
    string tmp = argv[2];
    bool is_local_executable = false;

    // Check if the provided executable name contains a path
    if (tmp.find('/') == string::npos) { // no path provided
      // Check if it's a system command
      if (!is_system_command(tmp.c_str())) {
        // Not a system command, prepend "./" to check the current directory
        string current_dir_app = "./" + tmp;
        if (file_exists(current_dir_app.c_str())) {
            tmp = current_dir_app;  // Use current directory version
            is_local_executable = true;
        } else {
            printf("Application %s not found in current directory or system PATH\n", tmp.c_str());
            exit(1);
        }
      } // Continue if the app is a system command
    } else { //A path is provided with the app
        is_local_executable = true;
    }
    string base_name;
    if (is_local_executable) {
        // Resolve the absolute path for local executables
        char resolved_path[PATH_MAX];
        if (realpath(tmp.c_str(), resolved_path) == NULL) {
            perror("realpath");
            exit(1);
        }
        // Extract the base name from the resolved path
        base_name = basename(resolved_path);
        tmp = string(resolved_path);
    } else {
      // command is in PATH (system comand), keep its name
      base_name = tmp;
    }

    int n = base_name.length();
    char name[n+1];
    strcpy(name, base_name.c_str());
    // Get the app name in HOST machine
    sesam_get_name(n, name);

    // Build the command string with absolute path and additional arguments
    s << tmp;
    for (int i = 3; i < argc; ++i) {
        s << " " << argv[i];
    }
    sesam_start_bench();
    // Execute the command using system()
    system(s.str().c_str());
    sesam_end_bench();

  } else {
    if (argc < 3) {
      printf("Missing argument: ");
      usage();
      exit(1);
    }

    /* Get argument */
    nb_param = argc - 1;
    for (i = 0; i < nb_param; ++i) {
      strcpy(parameter[i],argv[i+1]);
    }

    sesam_exec_command(nb_param, parameter);

  }

  unmap_sesam();

  return 0;
}
