from functools import partial

from aiohttp import web

from aiohttp_underscore_apis import AiohttpUnderscoreApis


async def hello(request: web.Request) -> web.Response:
    return web.Response(text="Hello, world\n")


def main():
    app = web.Application()
    app.router.add_get("/", hello, name="ROOT")
    app.router.add_get("/{aaa}/sfd", hello, allow_head=False)

    aiohttp_underscore_apis = AiohttpUnderscoreApis()
    """
    aiohttp_underscore_apis.site_factories.append(
        partial(web.UnixSite, path="/tmp/aiohttp-underscore-apis.sock")
    )
    """

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

    app.cleanup_ctx.append(aiohttp_underscore_apis.listener)
    """
    for name, subapp in aiohttp_underscore_apis.init_subapps(app).items():
        app.add_subapp(f"/{name}", subapp)
    """
    app.middlewares.extend(aiohttp_underscore_apis.middlewares)

    web.run_app(app)


if __name__ == "__main__":
    main()
