# HTTP (`http`)

Python-compatible execution provides bounded `get`, `post`, `put`, `patch`,
and `delete` operations. Options include `timeout`, `headers`, one of `body` or
`json`, `follow_redirects`, and `max_body_bytes`. Defaults are 10 seconds,
redirects enabled, and 10 MiB.

```sona
import http;

let response = http.get(
    "https://example.com/api",
    {timeout: 10, headers: {"Accept": "application/json"}}
);

if response.ok {
    print(response.body);
}
```

A response contains `status`, `ok`, UTF-8 `body`, lower-cased `headers`, and
the final `url`. An HTTP status outside 200-299 is still a response. Invalid
requests, timeouts, transports, body limits, and capability denials use
`SONA-HTTP-001` through `SONA-HTTP-005`. Diagnostic URLs omit credentials and
queries.

Native Core 0.15.5 can import `http`, but every request returns the stable
`SONA-HTTP-005` unavailable diagnostic. `--allow-network` grants policy only;
it does not claim a native transport implementation.
