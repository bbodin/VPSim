#ifndef RTC_H
#define RTC_H

#include <stdint.h>

//
// Base address and registers
//
#ifdef USING_VIRT_RTC
#define RTC_BASE 0x09010000UL
#else
#define RTC_BASE        0x0B000000UL
#endif

static inline volatile uint32_t *rtc_reg(uint32_t offset)
{
    return (volatile uint32_t *)(RTC_BASE + offset);
}

#define RTCDR      (*(volatile uint32_t *)(RTC_BASE + 0x00))  // Data
#define RTCMR      (*(volatile uint32_t *)(RTC_BASE + 0x04))  // Match
#define RTCLR      (*(volatile uint32_t *)(RTC_BASE + 0x08))  // Load
#define RTCCR      (*(volatile uint32_t *)(RTC_BASE + 0x0C))  // Control
#define RTCRIS     (*(volatile uint32_t *)(RTC_BASE + 0x14))  // Raw int
#define RTCICR     (*(volatile uint32_t *)(RTC_BASE + 0x1C))  // Clear int

#define RTC_ENABLE (1u << 0)
#define RTC_INT    (1u << 0)

//
// Public API
//

static inline void rtc_init(void)
{
    RTCLR = 0;          // load initial counter
    RTCCR = RTC_ENABLE; // start ticking
}

static inline uint32_t rtc_get_counter(void)
{
    return RTCDR;
}

static inline void rtc_set_alarm(uint32_t t)
{
    RTCMR = t;
}

static inline int rtc_alarm_fired(void)
{
    return RTCRIS & RTC_INT;    // no interrupt masking involved
}

static inline void rtc_clear_alarm(void)
{
    RTCICR = RTC_INT;
}

#endif // RTC_H
