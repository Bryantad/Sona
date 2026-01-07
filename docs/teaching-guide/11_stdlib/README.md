# Module 11: Standard Library Deep Dive

## Overview
Sona's standard library has 90+ modules ready to use. This module explores the most useful ones with real examples.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-10  
**Duration:** 60-90 minutes

---

## Learning Objectives
By the end of this module, you will:
- Know what's available in the standard library
- Use essential modules effectively
- Combine modules to solve real problems

---

## Mini-Lessons in This Module

| Mini | Topic | Key Modules |
|------|-------|-------------|
| [mini-1](mini-1_data.md) | Data & Processing | json, csv, toml, encoding |
| [mini-2](mini-2_utilities.md) | Utilities | time, random, math, uuid |
| [mini-3](mini-3_system.md) | System & Network | env, path, io, http |

---

## Module Categories

### Data Processing
| Module | Purpose |
|--------|---------|
| `json` | Parse and create JSON |
| `csv` | Read/write CSV files |
| `toml` | Configuration files |
| `encoding` | Base64, hex encoding |

### Math & Numbers
| Module | Purpose |
|--------|---------|
| `math` | Mathematical functions |
| `numbers` | Number utilities |
| `random` | Random generation |

### Text Processing
| Module | Purpose |
|--------|---------|
| `string` | String manipulation |
| `regex` | Pattern matching |
| `validation` | Input validation |

### Time & Dates
| Module | Purpose |
|--------|---------|
| `time` | Current time, formatting |
| `timer` | Measuring duration |

### Collections
| Module | Purpose |
|--------|---------|
| `collection` | List/dict helpers |
| `queue` | Queue data structure |
| `stack` | Stack data structure |

### System
| Module | Purpose |
|--------|---------|
| `io` | File operations |
| `path` | Path manipulation |
| `env` | Environment variables |

### Security
| Module | Purpose |
|--------|---------|
| `hashing` | SHA256, MD5, etc. |
| `uuid` | Unique identifiers |

---

## Quick Examples

```sona
// JSON
import json
let data = json.parse('{"name": "Alex"}')
let text = json.stringify(data)

// Random
import random
let num = random.randint(1, 100)
let item = random.choice(["a", "b", "c"])

// Time
import time
print(time.now())
time.sleep(1)

// Hashing
import hashing
let hash = hashing.sha256("password")

// UUID
import uuid
let id = uuid.generate()
```

---

## Practice Challenges

### Challenge 1: Config System
Use JSON to save and load application settings.

### Challenge 2: Password Generator
Use random and string modules to generate secure passwords.

### Challenge 3: Data Processor
Read a CSV file, process data, and output as JSON.

---

## Next Steps
→ Continue to [Module 12: Working with Data](../12_data/README.md)
