# /*************************************************************************
# *
# * Copyright 2025 highstreet technologies and others
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *     http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# ***************************************************************************/

from util.logging import get_pynts_logger
import threading
import falcon.asgi
import uvicorn

logger = get_pynts_logger("rest")

class Rest:
    class DefaultRoute:
        rest_instance = None

        def __init__(self, rest_instance):
            self.rest_instance = rest_instance

        async def on_get(self, req, resp):
            resp.media = {
                "status": "ok",
                "routes": self.rest_instance.routes
            }
            resp.status = 200


    _instance = None
    server: uvicorn.Server
    routes: dict

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()

        return cls._instance

    def init(self) -> None:
        self.routes = {}
        self.app = falcon.asgi.App()
        self.app.add_route("/", self.DefaultRoute(self))

        # uvicorn server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=8080, log_level="info")
        self.server = uvicorn.Server(config)

        # start REST server
        logger.info("starting REST server...")
        thread = threading.Thread(target=self.server.run)
        thread.start()

    def stop_server(self) -> None:
        self.server.should_exit = True

    def add_route(self, route: str, object) -> None:
        self.app.add_route(route, object)
        self.routes[route] = type(object).__name__
