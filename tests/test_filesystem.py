# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import fsspec
import pytest


@pytest.fixture(scope="module")
def fs(simple_repository):
    fs = fsspec.filesystem("git-annex", git_url=simple_repository.path)
    # For web access to local file server:
    fs._repository.set_config("annex.security.allowed-ip-addresses", "127.0.0.1")
    return fs


def test_ls(fs):
    assert sorted(fs.ls("", detail=False)) == [
        "/127.0.0.1_shared_hello-world.txt",
        "/git-annex-file",
        "/git-file",
    ]


@pytest.mark.parametrize(
    "path,expected_content",
    [
        ("/git-file", "some text"),
        ("/git-annex-file", "annex'ed text"),
        ("/127.0.0.1_shared_hello-world.txt", "Hello World\n"),
    ],
)
@pytest.mark.parametrize(
    "mode", ["r", "rb"]
)
def test_read(fs, path, mode, expected_content):
    if mode == "rb":
        expected_content = expected_content.encode()
    with fs.open(path, mode) as f:
        assert f.read() == expected_content
