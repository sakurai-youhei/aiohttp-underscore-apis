# aiohttp-underscore-apis
Inspect and manage aiohttp web application like Elasticsearch

`aiohttp-underscore-apis` provides the following APIs:

- Compact and aligned text (CAT)
    - `GET /_cat`
    - `GET /_cat/middlewares` (Nice to have?)
    - `GET /_cat/routes`
    - `GET /_cat/tasks`
    - `GET /_cat/transports` (Nice to have?)
- Routes
    - `GET /_routes`
    - `GET /_routes/settings` (`flat_settings` is not yet supported)
    - `GET /_routes/stats` (TODO)
    - `PUT /_routes/{route_id}/settings` (Dot notation is not yet supported)
    - `POST /_routes/{route_id}/interrupt`
- Tasks
    - `GET /_tasks` (TODO)
    - `GET /_tasks/{task_id}/cancel` (TODO)
    - `GET /_tasks/{task_id}/print_stack` (TODO)


> [!NOTE]
> Project status: Under construction - I am still experimenting with how to structure code in the project.

## Demo

[This notebook](demos/demo_aiohttp_underscore_apis.ipynb) goes through setup to usage.

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
    http://./${1#"${1%%[^/]*}"} "${@:2}"
}
function POST() {
  GET "$@" -X POST -H "Content-Type: application/json"
}
function PUT() {
  GET "$@" -X PUT -H "Content-Type: application/json"
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

## Use case

Suppose your aiohttp web application suddenly experiences an unexplained surge in traffic.
`aiohttp-underscore-apis` enables troubleshooting through endpoints starting with an underscore.

First, try `GET _cat/routes?v`, which will output a list of all registered routes.
To sort by path, add `&s=path`. If you need more information, add `&h=*`.
If the list is too large, you can use grep, or try output formatting with jq by specifying `&format=json`.

If the investigation reveals that heavy traffic to a specific route is severely impacting
the overall application's performance, it may be advisable to temporarily deactivate that
route and attempt fallback operation. In such cases, configure the route to return a 503
status code as follows.

```shell
$ PUT /_routes/{route_id}/settings -d '
{"transient":
  {"preempt":
    {"status": 503, "reason": "Route is temporarily deactivated"}
  }
}
'
```

If you also need to forcefully drain requests that have been already started processing,
you can achieve it by canceling the superior asyncio tasks using the following endpoint:

```shell
$ POST /_routes/{route_id}/interrupt
```

Once the storm has passed, you can stop the fallback operation by nulling the settings
as follows.

```shell
$ PUT /_routes/{route_id}/settings -d '
{"transient":
  {"preempt":
    {"status": null, "reason": null}
  }
}
'
```
