# reqsnap

> An HTTP request recorder and replay tool for mocking APIs during local development and testing.

---

## Installation

```bash
pip install reqsnap
```

---

## Usage

### Record requests

Wrap your HTTP calls with `reqsnap` to capture and save real API responses to disk.

```python
import reqsnap
import requests

with reqsnap.record(output="fixtures/"):
    response = requests.get("https://api.example.com/users")
```

### Replay recorded requests

Replace live API calls with saved fixtures during tests or offline development.

```python
import reqsnap
import requests

with reqsnap.replay(fixtures="fixtures/"):
    response = requests.get("https://api.example.com/users")
    print(response.json())
```

### CLI

```bash
# Record a single request
reqsnap record --url https://api.example.com/users --output fixtures/

# Start a local replay server
reqsnap serve --fixtures fixtures/ --port 8080
```

---

## How it works

1. **Record** — reqsnap intercepts outgoing HTTP requests and stores responses as JSON fixture files.
2. **Replay** — On playback, matching requests are resolved from local fixtures instead of hitting the network.

---

## License

MIT © reqsnap contributors