"""Unity Cloud Build Webhook Handler
Powered by CherryPy

This scripts boots a server that can accept webhook payloads from Unity Cloud Build
and handle the artifact so that:
* the latest artifacts are always at the specific paths
* the previous artifacts are archived with the timestamp at when the archive occurs.

Creating .env file is required to run this code. Copy the .env.example file to begin.
Bonus: if run directly on macOS, then the events are logged as the notification.
"""

import os.path
from concurrent.futures import ThreadPoolExecutor

import cherrypy as cp
from dotenv import load_dotenv

from app.controllers import UCBWebhookHandler


def main() -> int:
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    # For security reasons, we overwrite the version info and the error template to hide the backend software names.
    # These accesses to protected members are totally intended.
    cp.__version__ = ""
    # noinspection PyProtectedMember
    cp._cperror._HTTPErrorTemplate = cp._cperror._HTTPErrorTemplate.replace(
        'Powered by <a href="https://www.cherrypy.dev">CherryPy %(version)s</a>\n', "%(version)s"
    )

    # cp.config is for global settings
    if not os.environ["APP_DEBUG"].lower() in ("true", "1", "t"):
        print("Booting in production mode. Autoreload is disabled")
        cp.config.update({"environment": "embedded"})
        cp.config.update({"log.screen": True})

    docker_flag = os.environ.get("DOCKER", default="0")
    if (int(docker_flag) if docker_flag.isdigit() else 0) == 1:
        print("Detected Docker environment (DOCKER=1), serving from 0.0.0.0")
        cp.config.update({"server.socket_host": "0.0.0.0"})

    # create thread pool
    max_workers = os.environ["MAX_WORKERS"]
    tpe = ThreadPoolExecutor(max_workers=int(max_workers) if max_workers.isdigit() else 5)

    # Import the rest of the config from the file
    conf_path = os.path.join(os.path.dirname(__file__), "env.conf")
    cp.tree.mount(UCBWebhookHandler(tpe), config=conf_path)

    cp.engine.start()
    cp.engine.block()

    print("Waiting for remaining threads to close.")
    tpe.shutdown()

    return 0


if __name__ == "__main__":
    exit(main())
