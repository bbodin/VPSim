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

#ifndef __SESAM_MMAP_H__
#define __SESAM_MMAP_H__

#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

extern void *sesam_mem;

void map_sesam_mem();

void unmap_sesam();

#endif // __SESAM_MMAP_H__
