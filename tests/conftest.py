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
def simple_repository(file_server):
    server_address, server_dir = file_server
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
    # From a URL
    repository.set_config("annex.security.allowed-ip-addresses", "127.0.0.1")
    repository.addurl(f"http://{server_address}/shared/hello-world.txt")
    repository.commit("Add file from URL")
    repository.drop("/127.0.0.1_shared_hello-world.txt")

    return repository
