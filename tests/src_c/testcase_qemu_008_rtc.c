#include <printf.h>
#include <qemu.h>
#define USING_VIRT_RTC
#include <rtc.h>

static inline void delay_cycles(uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        __asm__ volatile("nop" ::: "memory");
    }
}

void rtc_test_read(void)
{
    printf_str("[RTC] Testing counter\n");

    for (int i = 0; i < 5; i++) {
        uint32_t t = rtc_get_counter();

        printf_str("  counter = ");
        printf_hex(t);
        printf_char('\n');

        delay_cycles(120000000);
    }
}

void rtc_test_alarm(void)
{
    printf_str("[RTC] Testing alarm\n");

    uint32_t now = rtc_get_counter();
    uint32_t alarm_tick = now + 3; // PL031 increments at 1Hz

    printf_str("  now  = ");
    printf_hex(now);
    printf_char('\n');

    printf_str("  alarm = ");
    printf_hex(alarm_tick);
    printf_char('\n');

    rtc_set_alarm(alarm_tick);

    // enable alarm interrupt (bit 0)
    //RTCIMSC = RTC_INT;

    while (!rtc_alarm_fired()) {
        // wait for alarm
    }

    printf_str("  Alarm fired!\n");

    rtc_clear_alarm();
}


int main(void)
{
    // not used (c_entry is platform entry)
    return 0;
}

void c_entry()
{
    printf_str("=== Start RTC Test ===\n");

    printf_str("=== RTC Test Init ===\n");
    rtc_init();
    printf_str("=== RTC Test Read ===\n");
    rtc_test_read();
    printf_str("=== RTC Test Alarm ===\n");
    rtc_test_alarm();

    printf_str("=== End RTC Test ===\n");

    qemu_exit(0);
}
