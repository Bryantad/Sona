# Mini-Episode 2.3: User Input

> Making interactive programs

## Script

### Intro (0:00 - 0:15)
"Let's make our programs interactive by getting input from users!"

### The input() Function (0:15 - 1:30)
```sona
let name = input("What is your name? ")
print("Hello, " + name + "!")
```

"How it works:
1. `input()` shows the message
2. Program waits for user to type
3. User presses Enter
4. What they typed is stored in the variable"

### Multiple Inputs (1:30 - 2:30)
```sona
let name = input("Name: ")
let age = input("Age: ")
let city = input("City: ")

print("Hello, " + name + "!")
print("You are " + age + " from " + city)
```

### Numbers from Input (2:30 - 3:30)
"Input is always text! Convert for math:"

```sona
let ageText = input("Your age: ")
let age = int(ageText)  // Convert to number

let nextYear = age + 1
print("Next year you'll be " + str(nextYear))
```

"Shorter version:"
```sona
let age = int(input("Your age: "))
```

### Mini Project: Mad Libs (3:30 - 4:45)
```sona
print("=== MAD LIBS ===")
let animal = input("An animal: ")
let verb = input("A verb: ")
let place = input("A place: ")

print("")
print("The " + animal + " likes to " + verb)
print("at the " + place + "!")
```

### Outro (4:45 - 5:00)
"Now your programs can talk to users! Try making a quiz or a story generator."

---

## Visual Notes
- Show cursor blinking waiting for input
- Highlight what user types
- Show the value flowing into the variable
