# Date and time

`date` owns calendar values; `time` owns clocks and durations.

```sona
import date;
import time;

let leap_day = date.parse("2024-02-29");
print(date.format("2024-02-29", "%Y/%m/%d"));

let started = time.monotonic();
time.sleep(0.01);
let finished = time.monotonic();
```

The date foundation is `today`, `from_timestamp`, `parse`, and `format`. The
time foundation is `now`, `timestamp`, `monotonic`, and `sleep`. Invalid
values, formats/timezones, and duration limits use `SONA-TIME-001` through
`SONA-TIME-003`.

`date.sleep` remains classified as a compatibility move to `time.sleep`.
