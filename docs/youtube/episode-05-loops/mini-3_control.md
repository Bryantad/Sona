# Mini-Episode 5.3: Break & Continue

> Controlling loop flow

## Script

### Intro (0:00 - 0:15)
"Sometimes you need to exit a loop early or skip an iteration. That's where break and continue help!"

### Break: Exit Immediately (0:15 - 1:45)
```sona
// Find first even number
for n in [1, 3, 5, 4, 7, 8] {
    if n % 2 == 0 {
        print("Found even: " + str(n))
        break  // Stop the loop!
    }
}
// Output: Found even: 4
```

"Once we find what we want, `break` exits the loop."

### Continue: Skip This Iteration (1:45 - 3:00)
```sona
// Print only odd numbers
for i in range(10) {
    if i % 2 == 0 {
        continue  // Skip to next iteration
    }
    print(i)
}
// Output: 1, 3, 5, 7, 9
```

"Continue skips to the next loop iteration."

### Practical Example: Search (3:00 - 4:00)
```sona
let users = ["alice", "bob", "charlie", "diana"]
let searchFor = "charlie"
let found = false

for user in users {
    if user == searchFor {
        print("Found " + user + "!")
        found = true
        break
    }
}

if !found {
    print("User not found")
}
```

### Skip Invalid Data (4:00 - 4:45)
```sona
let scores = [85, -1, 92, 0, 78, -5, 88]

for score in scores {
    if score <= 0 {
        continue  // Skip invalid scores
    }
    print("Valid score: " + str(score))
}
```

### Outro (4:45 - 5:00)
"Break = exit loop. Continue = skip to next. Use them to control exactly how your loops run!"

---

## Visual Notes
- Break: show arrow exiting loop
- Continue: show arrow jumping to next iteration
- Flowchart with both paths
