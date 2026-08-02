# Console input and output

`stdin` owns console input. `io` owns console output and flushing. Filesystem
operations live in `fs`; the old `io.input`, `io.read_file`, and
`io.write_file` exports remain compatibility paths with manifest replacements.

```sona
import stdin;
import io;

let name = stdin.read("Name: ");
io.write_stdout("Hello, ");
io.write_stdout(name);
io.flush();
```

Input, output, and console-capability failures use `SONA-IO-001` through
`SONA-IO-003`.
