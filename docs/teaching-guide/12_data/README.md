# Module 12: Working with Data

## Overview
Real programs work with real data. This module teaches practical data processing: APIs, databases, validation, and transformation.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-11  
**Duration:** 60-75 minutes

---

## Learning Objectives
- Fetch and process data from APIs
- Store and retrieve data persistently
- Validate and transform data
- Handle large datasets efficiently

---

## Mini-Lessons

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_apis.md) | APIs | Fetching and sending data |
| [mini-2](mini-2_storage.md) | Storage | Files, databases, caching |
| [mini-3](mini-3_transform.md) | Transformation | Filter, map, reduce patterns |

---

## Quick Reference

```sona
import http
import json
import io

// Fetch from API
let response = http.get_json("https://api.example.com/users")
for user in response.users {
    print(user.name)
}

// Store locally
io.write("cache.json", json.stringify(data))

// Transform data
let active = users.filter(func(u) { return u.active })
let names = users.map(func(u) { return u.name })
let total = prices.reduce(0, func(sum, p) { return sum + p })
```

---

## Next Steps
→ Continue to [Module 13: Building Projects](../13_projects/README.md)
