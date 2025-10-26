# aiohttp-underscore-apis
Inspect and manage aiohttp web application like Elasticsearch

`aiohttp-underscore-apis` provides the following APIs:

- Compact and aligned text (CAT)
    - `GET /_cat`
    - `GET /_cat/middlewares` (TODO)
    - `GET /_cat/routes`
    - `GET /_cat/tasks` (TODO)
- Routes
    - `GET /_routes`
    - `GET /_routes/_settings` (TODO)
    - `GET /_routes/_stats` (TODO)
    - `PUT /_routes/{route_id}/_settings` (TODO)
    - `POST /_routes/{route_id}/_cancel` (TODO)

> [!NOTE]
> Project status: Under construction - I am still experimenting with how to structure code in the project.

## Installation

```shell
pip install git+https://github.com/sakurai-youhei/aiohttp-underscore-apis.git
```

## Setup

### Publish via UNIX domain socket

```python
from functools import partial
from aiohttp import web
from aiohttp_underscore_apis import AiohttpUnderscoreApis

your_app: web.Application

aiohttp_underscore_apis = AiohttpUnderscoreApis()

# Configure it to listen on the UNIX domain socket
aiohttp_underscore_apis.site_factories.append(
    partial(web.UnixSite, path="/tmp/aiohttp-underscore-apis.sock")
)

# Attach it to your app
your_app.cleanup_ctx.append(aiohttp_underscore_apis.listener)
your_app.middlewares.extend(aiohttp_underscore_apis.middlewares)

web.run_app(your_app)  # Run your app as usual
```

With the setup above, you can call the underscore APIs as follows.

```shell
curl -s --unix-socket /tmp/aiohttp-underscore-apis.sock \
  'http://./_cat/routes?v&s=path'
```

Alternatively, you can also do it more Kibana-ishly as follows.

```shell
function GET() {
  curl -s --unix-socket /tmp/aiohttp-underscore-apis.sock \
    http://./${1#"${1%%[^/]*}"}
}

GET '_cat/routes?v&s=path'
```

If you prefer a stricter `600` permission, please use the following site factory.

```python
import os
import socket

path = "/tmp/aiohttp-underscore-apis.sock"
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    os.unlink(path)
except FileNotFoundError:
    pass

sock.bind(path)
os.chmod(path, 0o600)

aiohttp_underscore_apis.site_factories.append(
    partial(web.SockSite, sock=sock)
)
```

### Publish as part of your app (less secure)

While not recommended, you can expose the underscore APIs as part of your app as follows.

```python
from aiohttp import web
from aiohttp_underscore_apis import AiohttpUnderscoreApis

your_app: web.Application

aiohttp_underscore_apis = AiohttpUnderscoreApis()

# Attach it to your app
for name, subapp in aiohttp_underscore_apis.init_subapps(your_app).items():
    your_app.add_subapp(f"/{name}", subapp)
your_app.middlewares.extend(aiohttp_underscore_apis.middlewares)

web.run_app(your_app)  # Run your app as usual
```
