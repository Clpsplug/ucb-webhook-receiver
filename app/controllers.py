import json
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple

import cherrypy as cp

from util.dict import dict_safe_equals
from util.security import verify_signature
from worker.worker_base import OSType
from worker.worker_impl import WorkerFactory


def detect_binary(data: dict) -> Tuple[OSType, str]:
    """
    Decodes the payload and pick up the target OS and the binary archive url.

    :param data: Payload JSON
    :returns: Tuple of OSType and str, former being target OS and latter being the archive url.
    """
    artifacts = data["links"]["artifacts"]
    url = None
    for artifact in artifacts:
        if not artifact["primary"]:
            continue
        else:
            # This is the game binary. It appears to contain only one "files"
            # and href is the url we want to pull.
            url = artifact["files"][0]["href"]
            break
    if url is None:
        raise ValueError("No binary download url found, why...?")

    platform = data["platform"]
    os_type = None
    if platform == "standaloneosxuniversal":
        os_type = OSType.macOS
    elif platform == "standalonewindows64":
        os_type = OSType.Windows
    if os_type is None:
        raise ValueError("Unexpected platform {p}".format(p=platform))

    return os_type, url


class UCBWebhookHandler:
    """
    Controller for the Unity Cloud Build webhook payloads.

    :ivar tpe: ThreadPoolExecutor that the artifact workers are spawned on
    """

    def __init__(self, tpe: ThreadPoolExecutor):
        """
        TODO: Investigate if it's safe to use ProcessPoolExecutor here.
              It *may* be the case since worker currently does not use any environment variables.

        :param tpe: ThreadPoolExecutor created in upper level.
        """
        self.tpe = tpe

    # Intentionally NOT using tools.json_in(), since it makes cp.request.body.read() return nothing.
    @cp.expose
    @cp.tools.json_out()
    def index(self):
        """
        On receiving the correct payload, spawns a worker that places the artifact into the specified directory.
        The workers will be spawned on a given ThreadPoolExecutor.
        This means the webhook response will immediately return.
        """
        if cp.request.method != "POST":
            raise cp.HTTPError(405)

        # We MUST save the content here because read() cannot be called later to get content multiple times;
        # in other words, the body object is like a stream object.
        body = cp.request.body.read()  # type: bytes

        # NOTE: The cherrypy request body is in bytes already, so we don't need to convert them
        if not verify_signature(body, cp.request.headers.get("x-unitycloudbuild-signature", default="")):
            raise cp.HTTPError(403, message="Sorry")

        # Respond only to the "Cloud Build Success" event.
        # If the all guards at this point succeeds though, we return 200 but indicate an error.
        if not dict_safe_equals(cp.request.headers, "x-unity-event", "cloudBuild.success"):
            return {"ok": False}

        data = json.loads(body)  # type: dict
        project_name = data["projectName"]  # type: str
        target_name = data["buildTargetName"]  # type: str
        os_type, url = detect_binary(data)

        # Spawn a thread that processes the binary (while returning the webhook as early as possible)
        self.__process(os_type, url, project_name, target_name)
        return {"ok": True}

    def __process(self, os_type: OSType, url: str, project_name: str, target_name: str):
        worker = WorkerFactory.spawn_worker(os_type, url, project_name, target_name)
        self.tpe.submit(worker.process_binary())
