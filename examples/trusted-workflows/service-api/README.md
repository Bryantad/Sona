# Verifiable Service/API Workflow Boundary

This example performs a real HTTP request to a loopback-only fixture through
Sona's Python compatibility runtime. Start the fixture in one terminal:

```powershell
python .\fixture_server.py
```

Then run the Sona client from a second terminal:

```powershell
sona run .\client.sona --compatibility sona
```

The `sona` compatibility selection uses the canonical Sona parser and the
Python-hosted standard library; it is not Native Core. The response reports
HTTP `200` and a JSON status document. This workflow does
**not** produce a Native Proof Mode receipt: Native HTTP is intentionally
unavailable in 0.15.4/0.15.6, and Proof Mode does not silently fall back to
Python. Therefore it demonstrates current API usability, not verified network
effects. Native service evidence remains deferred until an instrumented Native
HTTP transport exists.
