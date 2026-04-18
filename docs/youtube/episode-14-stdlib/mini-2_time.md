# Mini-Episode 14.2: Time & Date ⏰

> Working with time in Sona

---

## The Time Module

```sona
import time
```

Everything you need to work with time and dates!

---

## Current Time

```sona
import time

// Current timestamp (seconds since 1970)
let now = time.time()
print(now)  // 1704067200.0

// More readable
let current = time.now()
print(current)  // 2024-01-01 12:00:00
```

---

## Pausing Your Program

```sona
import time

print("Starting...")
time.sleep(2)        // Wait 2 seconds
print("Done!")

// Useful for:
// - Animations
// - Rate limiting
// - Countdown timers
```

---

## Measuring Time

```sona
import time

let start = time.time()

// Do something...
for i in range(1000000) {
    let x = i * 2
}

let end = time.time()
print(f"Took {end - start} seconds")
```

---

## Formatting Dates

```sona
import time

let now = time.now()

// Different formats
print(time.format(now, "%Y-%m-%d"))      // 2024-01-15
print(time.format(now, "%H:%M:%S"))      // 14:30:45
print(time.format(now, "%B %d, %Y"))     // January 15, 2024
print(time.format(now, "%A"))            // Monday
```

---

## Format Codes

| Code | Meaning | Example |
|------|---------|---------|
| `%Y` | Year (4 digit) | 2024 |
| `%m` | Month (01-12) | 01 |
| `%d` | Day (01-31) | 15 |
| `%H` | Hour (00-23) | 14 |
| `%M` | Minute (00-59) | 30 |
| `%S` | Second (00-59) | 45 |
| `%A` | Weekday name | Monday |
| `%B` | Month name | January |

---

## Practical: Stopwatch

```sona
import time

class Stopwatch {
    func init() {
        self.start_time = null
        self.elapsed = 0
    }
    
    func start() {
        self.start_time = time.time()
    }
    
    func stop() {
        if self.start_time != null {
            self.elapsed = time.time() - self.start_time
            self.start_time = null
        }
        return self.elapsed
    }
    
    func display() {
        let mins = int(self.elapsed / 60)
        let secs = self.elapsed % 60
        return f"{mins}:{secs:.2f}"
    }
}

let timer = Stopwatch()
timer.start()
time.sleep(3)
timer.stop()
print(timer.display())  // 0:3.00
```

---

## Practical: Countdown

```sona
import time

func countdown(seconds) {
    while seconds > 0 {
        print(f"  {seconds}...")
        time.sleep(1)
        seconds = seconds - 1
    }
    print("  GO!")
}

countdown(5)
```

---

## Practical: Log with Timestamp

```sona
import time

func log(message) {
    let timestamp = time.format(time.now(), "%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
    // Also write to file
    let log_line = f"[{timestamp}] {message}\n"
    append_file("app.log", log_line)
}

log("Application started")
log("User logged in")
log("Processing data")
```

Output:
```
[2024-01-15 14:30:45] Application started
[2024-01-15 14:30:46] User logged in
[2024-01-15 14:30:47] Processing data
```

---

## Quick Reference

| Function | Description |
|----------|-------------|
| `time.time()` | Timestamp in seconds |
| `time.now()` | Current datetime |
| `time.sleep(n)` | Pause n seconds |
| `time.format(t, fmt)` | Format datetime |
