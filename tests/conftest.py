# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from fsspec_git_annex.git_annex import GitAnnexRepo

from .utils import bytes_data


@pytest.fixture(scope="session")
def file_server():
    resources_path = Path(__file__).parent / "resources" / "served_files"
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(resources_path, Path(tmpdir) / "shared")
        cmd = [
            "python",
            "-u",
            "-m",
            "http.server",
            "--bind",
            "127.0.0.1",
            "--directory",
            str(tmpdir),
            "0",
        ]
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ) as server_process:
            output = server_process.stdout.readline()
            address, port = re.fullmatch(
                r"^Serving HTTP on ([^ ]+) port ([1-9][0-9]*) .*\n$", output
            ).groups()
            yield f"{address}:{port}", Path(tmpdir)
            server_process.terminate()


@pytest.fixture(scope="session")
def test_submodule(file_server):
    server_address, server_path = file_server
    submodule_path = server_path / "shared" / "submodule"
    repository = GitAnnexRepo.init(submodule_path)

    # Add some content to the repository:
    # A git file
    path = submodule_path / "git-file"
    path.write_text("some text in submodule")
    repository.add(path)
    repository.commit("Add git file")
    # An annex'ed file
    path = submodule_path / "git-annex-file"
    path.write_text("annex'ed text in submodule")
    repository.annex_add(path)
    repository.commit("Add annex'ed file")

    # This is needed to make the repository clone-able via http
    repository.update_server_info()

    return repository


@pytest.fixture(scope="session")
def test_repository(file_server, test_submodule):
    server_address, server_path = file_server
    tmpdir = tempfile.TemporaryDirectory()
    tmpdir_path = Path(tmpdir.name)
    repository = GitAnnexRepo.init(tmpdir_path)
    # Attach tmpdir lifetime to repository's lifetime for cleanup purposes
    repository._temp_dir_obj = tmpdir

    # Add some content to the repository:
    # A git file
    path = tmpdir_path / "git-file"
    path.write_text("some text")
    repository.add(path)
    repository.commit("Add git file")
    # An annex'ed file
    path = tmpdir_path / "git-annex-file"
    path.write_text("annex'ed text")
    repository.annex_add(path)
    repository.commit("Add annex'ed file")
    # From a URL in 3 different ways
    repository.set_config("annex.security.allowed-ip-addresses", "127.0.0.1")
    repository.addurl(
        f"http://{server_address}/shared/hello-world.txt",
        path="hello-world_relaxed.txt",
        relaxed=True,
    )
    repository.commit("Add file from URL (relaxed)")
    repository.addurl(
        f"http://{server_address}/shared/hello-world.txt",
        path="hello-world_fast.txt",
        fast=True,
    )
    repository.commit("Add file from URL (fast)")
    repository.addurl(
        f"http://{server_address}/shared/hello-world.txt", path="hello-world.txt"
    )
    repository.commit("Add file from URL")
    repository.drop("hello-world.txt")
    # A larger annex'ed file
    path = tmpdir_path / "git-annex-large-file"
    path.write_bytes(bytes_data(0))
    repository.annex_add(path)
    repository.commit("Add large annex'ed file")

    repository.submodule_add(
        f"http://{server_address}/{test_submodule.path.relative_to(server_path)}/.git"
    )
    repository.commit("Add submodule")

    return repository
