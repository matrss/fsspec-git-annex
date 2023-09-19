# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from ..test_filesystem import (
    test_repository_content,
    test_repository_listing,
    test_submodule_listing,
)

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("darwin"),
    reason="I could not get fuse to run in the GitHub Actions macOS runner.",
)


@pytest.fixture(scope="module")
def mounted_filesystem(test_repository):
    with tempfile.TemporaryDirectory() as mountpoint:
        mountpoint = Path(mountpoint)
        cmd = [
            "git-annex-mount",
            str(test_repository.path),
            str(mountpoint),
        ]
        with subprocess.Popen(cmd, text=True) as mount_process:
            # Make sure that the mount is up and running
            while True:
                if mountpoint.is_mount():
                    break
                time.sleep(0.1)
            yield mountpoint
            mount_process.terminate()


def test_ls(mounted_filesystem):
    assert {
        e.relative_to(mounted_filesystem) for e in mounted_filesystem.iterdir()
    } == {Path(e).relative_to("/") for e in test_repository_listing}


def test_ls_submodule(mounted_filesystem):
    assert {
        e.relative_to(mounted_filesystem)
        for e in (mounted_filesystem / "submodule").iterdir()
    } == {Path(e).relative_to("/") for e in test_submodule_listing}


@pytest.mark.parametrize(
    "path,mode,expected_content",
    *test_repository_content,
)
def test_read(mounted_filesystem, path, mode, expected_content):
    if callable(expected_content):
        expected_content = expected_content()
    full_path = mounted_filesystem / Path(path).relative_to("/")
    with open(str(full_path), mode) as f:
        assert f.read() == expected_content
