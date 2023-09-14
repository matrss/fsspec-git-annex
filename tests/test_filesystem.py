# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import fsspec
import pytest

from .utils import bytes_data


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
        "/git-annex-large-file",
        "/git-file",
    ]


@pytest.mark.parametrize(
    "path,mode,expected_content",
    [
        ("/git-file", "r", "some text"),
        ("/git-annex-file", "r", "annex'ed text"),
        ("/127.0.0.1_shared_hello-world.txt", "r", "Hello World\n"),
        ("/git-file", "rb", b"some text"),
        ("/git-annex-file", "rb", b"annex'ed text"),
        ("/127.0.0.1_shared_hello-world.txt", "rb", b"Hello World\n"),
        ("/git-annex-large-file", "rb", lambda: bytes_data(0)),
    ],
)
def test_read(fs, path, mode, expected_content):
    if callable(expected_content):
        expected_content = expected_content()
    with fs.open(path, mode) as f:
        assert f.read() == expected_content


def test_read_partial(fs):
    expected_content = bytes_data(0)
    assert (
        len(expected_content) > 12345 + 4321 + 15243
    ), "The data produced by bytes_data is too short for this test"
    with fs.open("/git-annex-large-file", "rb") as f:
        assert f.read(12345) == expected_content[:12345]
        assert f.read(4321) == expected_content[12345 : 12345 + 4321]
        assert f.read(15243) == expected_content[12345 + 4321 : 12345 + 4321 + 15243]
        assert f.read() == expected_content[12345 + 4321 + 15243 :]
