# Filesystem (`fs`)

Canonical text operations use UTF-8. `write_text` and `append_text` return the
number of Unicode scalar values written. `list_dir` is sorted; recursive
compatibility listings use forward-slash relative paths. Removing a missing
path returns `false`; other failures produce `SONA-FS-*` diagnostics.

```sona
import fs;

fs.write_text("notes.txt", "Hello");
fs.append_text("notes.txt", " Sona");
let contents = fs.read_text("notes.txt");
let entries = fs.list_dir(".");
```

Canonical exports are `read_text`, `write_text`, `append_text`, `exists`,
`is_file`, `is_dir`, `list_dir`, `create_dir`, `remove`, `rename`, and `copy`.
The old `read`, `write`, `append`, and `mkdir` spellings remain aliases.

Python-compatible runs retain normal process access. `sona run --safe`
confines reads to the project, blocks recognized secret files, and denies
writes. Native Core starts with filesystem access denied; see
[runtime capabilities](runtime-capabilities.md).
