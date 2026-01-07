# Mini-Episode 14.3: JSON & HTTP 🌐

> Data exchange and web requests

---

## Why JSON?

JSON is the universal language for data exchange:
- Config files
- APIs
- Saving game state
- Web communication

---

## JSON Module Basics

```sona
import json

// Dictionary to JSON string
let data = {"name": "Alice", "age": 25}
let json_str = json.dumps(data)
print(json_str)  // '{"name": "Alice", "age": 25}'

// JSON string to dictionary
let text = '{"x": 10, "y": 20}'
let obj = json.loads(text)
print(obj["x"])  // 10
```

---

## File Operations

```sona
import json

// Save to file
let settings = {"theme": "dark", "volume": 80}
json.save("settings.json", settings)

// Load from file
let loaded = json.load("settings.json")
print(loaded["theme"])  // dark
```

---

## The HTTP Module

```sona
import http
```

Make web requests to APIs and websites!

---

## GET Request

```sona
import http

// Fetch data from a URL
let response = http.get("https://api.example.com/data")

if response.status == 200 {
    print("Success!")
    print(response.body)
}
```

---

## POST Request

```sona
import http
import json

// Send data to an API
let data = {"username": "alice", "message": "Hello!"}

let response = http.post(
    "https://api.example.com/messages",
    body=json.dumps(data),
    headers={"Content-Type": "application/json"}
)

print(response.status)  // 201 (Created)
```

---

## Practical: Weather App

```sona
import http
import json

func get_weather(city) {
    let url = f"https://api.weather.com/v1/current?city={city}"
    
    try {
        let response = http.get(url)
        
        if response.status == 200 {
            let data = json.loads(response.body)
            return {
                "temp": data["temperature"],
                "condition": data["condition"],
                "humidity": data["humidity"]
            }
        }
    } catch error {
        print(f"Error: {error}")
    }
    
    return null
}

let weather = get_weather("New York")
if weather {
    print(f"Temperature: {weather['temp']}°F")
    print(f"Condition: {weather['condition']}")
}
```

---

## Practical: REST API Client

```sona
import http
import json

class ApiClient {
    func init(base_url) {
        self.base_url = base_url
    }
    
    func get(endpoint) {
        let url = self.base_url + endpoint
        let response = http.get(url)
        return json.loads(response.body)
    }
    
    func post(endpoint, data) {
        let url = self.base_url + endpoint
        let response = http.post(
            url,
            body=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        return json.loads(response.body)
    }
}

// Use it
let api = ApiClient("https://api.myapp.com")
let users = api.get("/users")
let new_user = api.post("/users", {"name": "Bob"})
```

---

## Handling API Errors

```sona
import http

func safe_request(url) {
    try {
        let response = http.get(url)
        
        match response.status {
            200 => return {"ok": true, "data": response.body},
            404 => return {"ok": false, "error": "Not found"},
            500 => return {"ok": false, "error": "Server error"},
            _ => return {"ok": false, "error": f"Status {response.status}"}
        }
    } catch error {
        return {"ok": false, "error": f"Network error: {error}"}
    }
}
```

---

## Quick Reference

| JSON Function | Description |
|---------------|-------------|
| `json.dumps(obj)` | Object → JSON string |
| `json.loads(str)` | JSON string → Object |
| `json.save(file, obj)` | Save to file |
| `json.load(file)` | Load from file |

| HTTP Function | Description |
|---------------|-------------|
| `http.get(url)` | GET request |
| `http.post(url, ...)` | POST request |
| `response.status` | Status code |
| `response.body` | Response content |
