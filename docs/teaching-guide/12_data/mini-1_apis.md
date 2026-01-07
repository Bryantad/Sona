# Mini-Lesson 12.1: Working with APIs

## What is an API?

An **API** (Application Programming Interface) lets programs talk to each other. When you:
- Check the weather on your phone
- Login with Google
- Get movie info

...you're using APIs!

---

## Making GET Requests

GET requests **fetch** data:

```sona
import http
import json

// Simple GET
let response = http.get("https://api.example.com/users")

print(response.status)  // 200 = OK
print(response.body)    // Raw response text

// Parse JSON response
let data = json.parse(response.body)
for user in data.users {
    print(user.name)
}
```

### Shortcut for JSON APIs

```sona
// Automatically parses JSON
let data = http.get_json("https://api.example.com/users")
print(data.users[0].name)
```

---

## Query Parameters

Add parameters to your request:

```sona
// Instead of building URL manually...
let response = http.get("https://api.example.com/search", {
    "params": {
        "query": "sona programming",
        "limit": 10,
        "page": 1
    }
})
// Becomes: https://api.example.com/search?query=sona+programming&limit=10&page=1
```

---

## Making POST Requests

POST requests **send** data:

```sona
let response = http.post("https://api.example.com/users", {
    "body": {
        "name": "Alice",
        "email": "alice@example.com"
    }
})

if response.status == 201 {
    print("User created!")
    let newUser = json.parse(response.body)
    print("ID: " + newUser.id)
}
```

---

## Headers and Authentication

```sona
// API Key authentication
let response = http.get("https://api.example.com/data", {
    "headers": {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }
})

// Basic authentication
let response = http.get("https://api.example.com/data", {
    "auth": {
        "username": "user",
        "password": "pass"
    }
})
```

---

## Error Handling

APIs can fail! Always handle errors:

```sona
func fetchUser(userId) {
    try {
        let response = http.get("https://api.example.com/users/" + userId)
        
        if response.status == 200 {
            return json.parse(response.body)
        } else if response.status == 404 {
            print("User not found")
            return null
        } else {
            print("Error: " + response.status)
            return null
        }
    } catch e {
        print("Network error: " + e.message)
        return null
    }
}

let user = fetchUser("123")
if user != null {
    print("Found: " + user.name)
}
```

---

## Building an API Client

Organize API calls into a class:

```sona
import http
import json

class GithubAPI {
    func init(token = null) {
        self.base = "https://api.github.com"
        self.token = token
    }
    
    func _headers() {
        let h = {"Accept": "application/json"}
        if self.token != null {
            h["Authorization"] = "token " + self.token
        }
        return h
    }
    
    func getUser(username) {
        let response = http.get(
            "{self.base}/users/{username}",
            {"headers": self._headers()}
        )
        if response.status == 200 {
            return json.parse(response.body)
        }
        return null
    }
    
    func getRepos(username) {
        let response = http.get(
            "{self.base}/users/{username}/repos",
            {"headers": self._headers()}
        )
        if response.status == 200 {
            return json.parse(response.body)
        }
        return []
    }
    
    func searchRepos(query) {
        let response = http.get("{self.base}/search/repositories", {
            "params": {"q": query},
            "headers": self._headers()
        })
        if response.status == 200 {
            return json.parse(response.body).items
        }
        return []
    }
}

// Usage
let github = GithubAPI()
let user = github.getUser("octocat")
print("Name: " + user.name)
print("Followers: " + user.followers)

let repos = github.searchRepos("sona language")
for repo in repos {
    print("- {repo.name}: {repo.stars} stars")
}
```

---

## Rate Limiting

APIs often limit requests. Be respectful:

```sona
import time

class RateLimitedClient {
    func init(requests_per_second = 1) {
        self.delay = 1.0 / requests_per_second
        self.last_request = 0
    }
    
    func request(url) {
        // Wait if needed
        let now = time.timestamp()
        let elapsed = now - self.last_request
        if elapsed < self.delay {
            time.sleep(self.delay - elapsed)
        }
        
        self.last_request = time.timestamp()
        return http.get(url)
    }
}

let client = RateLimitedClient(2)  // Max 2 requests/second
```

---

## Practice

### Exercise 1
Fetch a random joke from a jokes API and display it.

### Exercise 2
Create a weather lookup that takes a city name and shows the temperature.

### Exercise 3
Build a simple GitHub profile viewer that shows:
- Username
- Bio
- Number of public repos
- Most recent 5 repos

---

→ Next: [mini-2: Data Storage](mini-2_storage.md)
