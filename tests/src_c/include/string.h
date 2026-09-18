#ifndef  _STRING_UTIL_
#define _STRING_UTIL_

int strlen(const char *s) {
    int len = 0;

    while (s[len] != 0) {
        len++;
    }

    return len;
}

double atof(const char *s) {
    double result = 0.0;
    double frac = 0.1;

    int sign = 1;
    int i = 0;

    // sign
    if (s[i] == '-') {
        sign = -1;
        i++;
    }

    // integer part
    while (s[i] >= '0' && s[i] <= '9') {
        result = result * 10.0 + (s[i] - '0');
        i++;
    }

    // fractional part
    if (s[i] == '.') {
        i++;
        while (s[i] >= '0' && s[i] <= '9') {
            result += (s[i] - '0') * frac;
            frac *= 0.1;
            i++;
        }
    }

    return sign * result;
}

char *strstr(const char *haystack, const char *needle) {
    if (!*needle) return (char *)haystack;

    for (int i = 0; haystack[i] != 0; i++) {
        int j = 0;

        while (needle[j] != 0 &&
               haystack[i + j] != 0 &&
               haystack[i + j] == needle[j]) {
            j++;
        }

        if (needle[j] == 0) {
            return (char *)&haystack[i];
        }
    }

    return 0;
}

#endif