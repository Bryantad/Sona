# Mini-Episode 14.1: Math & Random 🎲

> Essential standard library modules

---

## The Math Module

```sona
import math
```

Your toolkit for mathematical operations!

---

## Common Math Functions

```sona
import math

// Square root
print(math.sqrt(16))    // 4.0
print(math.sqrt(2))     // 1.414...

// Power
print(math.pow(2, 8))   // 256.0

// Absolute value
print(math.abs(-42))    // 42

// Rounding
print(math.floor(3.7))  // 3 (round down)
print(math.ceil(3.2))   // 4 (round up)
print(round(3.5))       // 4 (round nearest)
```

---

## Math Constants

```sona
import math

print(math.pi)   // 3.14159265358979...
print(math.e)    // 2.71828182845904...
```

---

## Trigonometry (For Games!)

```sona
import math

let angle = math.pi / 4  // 45 degrees

print(math.sin(angle))  // 0.707...
print(math.cos(angle))  // 0.707...
print(math.tan(angle))  // 1.0

// Convert degrees to radians
func to_radians(degrees) {
    return degrees * math.pi / 180
}
```

---

## The Random Module

```sona
import random
```

Generate random numbers for games, simulations, etc!

---

## Random Numbers

```sona
import random

// Random float between 0 and 1
print(random.random())  // 0.7234...

// Random integer in range (inclusive)
print(random.randint(1, 6))   // Like rolling a die: 1-6

// Random float in range
print(random.uniform(1.0, 10.0))  // 5.234...
```

---

## Random Choices

```sona
import random

let colors = ["red", "blue", "green", "yellow"]

// Pick one random item
print(random.choice(colors))  // "blue" (or any)

// Pick multiple (can repeat)
print(random.choices(colors, k=3))  // ["red", "red", "green"]

// Pick multiple (no repeats)
print(random.sample(colors, 2))  // ["green", "blue"]
```

---

## Shuffle a List

```sona
import random

let cards = [1, 2, 3, 4, 5]
random.shuffle(cards)
print(cards)  // [3, 1, 5, 2, 4] (randomized)
```

---

## Practical: Dice Game

```sona
import random

func roll_dice(num_dice, sides = 6) {
    let total = 0
    let rolls = []
    
    for i in range(num_dice) {
        let roll = random.randint(1, sides)
        rolls.append(roll)
        total = total + roll
    }
    
    return {"rolls": rolls, "total": total}
}

// Roll 2d6 (two six-sided dice)
let result = roll_dice(2, 6)
print(f"Rolled: {result['rolls']} = {result['total']}")
```

---

## Practical: Random Password

```sona
import random

func generate_password(length = 12) {
    let chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
    let password = ""
    
    for i in range(length) {
        password = password + random.choice(chars)
    }
    
    return password
}

print(generate_password())  // "Kj4#mP9xQw2!"
```

---

## Quick Reference

| Math Function | Description |
|---------------|-------------|
| `sqrt(x)` | Square root |
| `pow(x, y)` | x to the power y |
| `abs(x)` | Absolute value |
| `floor(x)` | Round down |
| `ceil(x)` | Round up |

| Random Function | Description |
|-----------------|-------------|
| `random()` | Float 0-1 |
| `randint(a, b)` | Integer a-b |
| `choice(list)` | Pick one |
| `shuffle(list)` | Randomize order |
