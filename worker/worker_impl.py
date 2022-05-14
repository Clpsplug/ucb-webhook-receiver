import os
import shutil
import traceback
from datetime import datetime
from os import path
from typing import Callable
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

import requests

from util.logging import PrintLogger
from util.shell import NotificationSound
from util.shell import TerminalNotifier
from worker.worker_base import IWorker
from worker.worker_base import OSType


class WorkerFactory:
    @staticmethod
    def spawn_worker(os_type: OSType, url: str, project_name: str, target_name: str) -> IWorker:
        """
        Create the worker for os type and url.
        """

        # TODO: Deprecate this method as there are no os_type differences anymore,
        #       as we filled the gap outside the scope of this script.
        if os_type == OSType.macOS:
            # managed to pull notarization off at UCB side, no longer need to notarize here
            return BinaryWorker(url, project_name, target_name, PrintLogger())
        elif os_type == OSType.Windows:
            return BinaryWorker(url, project_name, target_name, PrintLogger())
        raise ValueError("os_type {type} is unknown".format(type=os_type))


class BinaryWorker(IWorker):
    def process_binary(self) -> Callable:
        # Download the binary, and unzip it.
        def process():
            TerminalNotifier.initialize()
            try:
                TerminalNotifier.fire_notification(
                    title="Received a build from Unity Cloud Build!",
                    message="Now processing the binary for {target}".format(target=self.target_name),
                    sound=NotificationSound.Crystal,
                )
                self.logger.info("Received a build from UCB, target: {target}".format(target=self.target_name))
                artifact_dir = self.download()
                self.place_artifacts(artifact_dir)
                TerminalNotifier.fire_notification(
                    title="UCB Binary has been processed!",
                    message="Process has completed and the binary is ready!",
                    sound=NotificationSound.Sonar,
                )
            except Exception as e:
                self.logger.error(
                    "An exception occurred: {type} for target: {target}".format(type=type(e), target=self.target_name)
                )
                self.logger.error("Trace information: {trace}".format(trace=traceback.format_exc()))
            else:
                self.logger.info(
                    "Deployment to container COMPLETED SUCCESSFULLY, target: {target}".format(target=self.target_name)
                )

        return process

    def download(self) -> str:
        self.logger.info("Downloading the binary, target: {target}".format(target=self.target_name))
        # Create a temporary working directory. Duplicates are not allowed.
        tmp_dir_name = path.join(
            ".",
            "tmp",
            self.project_name,
            self.target_name,
            datetime.utcnow().strftime("%Y-%m-%d %H-%M-%S.%f"),
        )
        self.logger.info("Create tmp dir {dir}, target: {target}".format(dir=tmp_dir_name, target=self.target_name))
        os.makedirs(tmp_dir_name, exist_ok=False)

        # from the URL, get the artifact and save it.
        artifact_path = path.join(tmp_dir_name, "artifact.zip")
        self.logger.info("Request the ZIPped binary, target: {target}".format(target=self.target_name))
        # The game is super-big in size and using memory is not ideal
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            with open(artifact_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

        # Then extract the binary.
        extract_dir_name = path.join(tmp_dir_name, "artifact")
        self.logger.info(
            "Extract binary from {zip}, target: {target}".format(zip=artifact_path, target=self.target_name)
        )
        with ZipFile(artifact_path, "r") as z:
            # The extract_dir_name dir will *directly* contain the artifact
            z.extractall(extract_dir_name)

        self.logger.info(
            "Extract OK, dir: {dir}, target: {target}".format(dir=extract_dir_name, target=self.target_name)
        )

        # get this directory name to access artifacts
        return extract_dir_name

    def place_artifacts(self, artifact_dir_path: str):
        self.logger.info("Move artifact to container, target: {target}".format(target=self.target_name))
        artifact_path = path.join(".", "output", self.project_name, self.target_name)
        if path.exists(artifact_path):
            self.logger.info(
                "Artifact path {path} exists, probably from the last run. Archiving now... target: {target}".format(
                    path=artifact_path, target=self.target_name
                )
            )
            # Replace the old binary (if exists) to the archive directory
            # The previous binary should be packed in output/{target_name} directory.
            # We will ZIP the entire directory into a zip file in archive directory,
            # appending timestamp for future references.
            archive_path = path.join(
                ".",
                "output",
                "archives",
                "{project}_{target}_{timestamp}.zip".format(
                    project=self.project_name,
                    target=self.target_name,
                    timestamp=datetime.utcnow().strftime("%Y-%m-%d %H-%M-%S.%f"),
                ),
            )
            self.logger.info(
                "Archiving {source} into {archive_path}".format(source=artifact_path, archive_path=archive_path)
            )
            # Using shutil.make_archive will mess up the thread and thus not recommended
            with ZipFile(archive_path, "w", ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(artifact_path):
                    for file in files:
                        z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), artifact_path))
            self.logger.info(
                "Archive complete, now removing the original ({path},) target: {target}".format(
                    path=artifact_path, target=self.target_name
                )
            )
            shutil.rmtree(artifact_path)

        # Then copy the content of the directory to the output directory
        self.logger.info(
            "Copying the downloaded binary to container at {path}, target: {target}".format(
                path=artifact_path, target=self.target_name
            )
        )
        shutil.copytree(
            artifact_dir_path,
            artifact_path,
            ignore=shutil.ignore_patterns("*BackUpThisFolder_ButDontShipItWithYourGame/**/*"),
        )
        # After that, copy the content of the accompaniment directory, except for .gitignore file
        self.logger.info("Checking for accompaniment resources, target: {target}".format(target=self.target_name))
        accompaniment_dir = path.join(".", "resources", "accompaniment", self.project_name)
        if not path.exists(accompaniment_dir) or not path.isdir(accompaniment_dir):
            self.logger.warning(
                "Accompaniment directory {path} was not found or was not a directory. Skipping.".format(
                    path=accompaniment_dir
                )
            )
            return
        for stuff in os.listdir(accompaniment_dir):
            if stuff == ".gitignore":
                continue
            self.logger.info(
                "Copy file or dir {stuff} into container, target: {target}".format(stuff=stuff, target=self.target_name)
            )
            full_dir = path.join(accompaniment_dir, stuff)
            dest_dir = path.join(artifact_path, stuff)
            # We need to change method by the path type.
            if os.path.isdir(full_dir):
                shutil.copytree(full_dir, dest_dir, dirs_exist_ok=True)
            elif os.path.isfile(full_dir):
                shutil.copyfile(full_dir, dest_dir)
