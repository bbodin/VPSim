#include "sesam.h"

/* Global variables */
void *sesam_mem = NULL;
int fd = -1;

/* Map SESAM memory from /dev/mem using the address in /etc/config_sesam */
void map_sesam_mem(void) {
    unsigned int base_address;
    FILE *fp;

    /* Read configuration file */
    fp = fopen("/etc/config_sesam", "r");
    if (fp == NULL) {
        perror("Error while opening /etc/config_sesam");
        fprintf(stderr, "Please type in your terminal 'echo [hex addr sesam_monitor] > /etc/config_sesam'\n");
        exit(EXIT_FAILURE);
    }

    if (fscanf(fp, "%x", &base_address) != 1) {
        fprintf(stderr, "File /etc/config_sesam is empty or not in the right format\n");
        fprintf(stderr, "Please type in your terminal 'echo [hex addr sesam_monitor] > /etc/config_sesam'\n");
        fclose(fp);
        exit(EXIT_FAILURE);
    }
    fclose(fp);

    if (base_address == 0) {
        fprintf(stderr, "Base address is 0\n");
        exit(EXIT_FAILURE);
    }

    /* Open /dev/mem */
    fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd < 0) {
        perror("Error opening /dev/mem");
        exit(EXIT_FAILURE);
    }

    /* Map 4 bytes of SESAM memory */
    sesam_mem = mmap(NULL, 4, PROT_READ | PROT_WRITE, MAP_SHARED, fd, base_address);
    if (sesam_mem == MAP_FAILED) {
        perror("mmap failed");
        fprintf(stderr, "Please check the correct address in /etc/config_sesam\n");
        close(fd);
        exit(EXIT_FAILURE);
    }
}

/* Unmap SESAM memory and close file descriptor */
void unmap_sesam(void) {
    if (sesam_mem) {
        munmap(sesam_mem, 4);
        sesam_mem = NULL;
    }
    if (fd >= 0) {
        close(fd);
        fd = -1;
    }
}
