# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import fsspec
import pytest

from .utils import bytes_data


@pytest.fixture(scope="module")
def fs(test_repository):
    fs = fsspec.filesystem("git-annex", git_url=test_repository.path)
    # For web access to local file server:
    fs._repositories["/"].set_config("annex.security.allowed-ip-addresses", "127.0.0.1")
    fs._repositories["/submodule"].set_config(
        "annex.security.allowed-ip-addresses", "127.0.0.1"
    )
    return fs


def test_ls(fs):
    assert set(fs.ls("", detail=False)) == {
        "/.gitmodules",
        "/git-annex-file",
        "/git-annex-large-file",
        "/git-file",
        "/hello-world.txt",
        "/hello-world_fast.txt",
        "/hello-world_relaxed.txt",
        "/submodule",
    }


def test_ls_submodule(fs):
    assert set(fs.ls("/submodule", detail=False)) == {
        "/submodule/git-annex-file",
        "/submodule/git-file",
    }


@pytest.mark.parametrize(
    "path,mode,expected_content",
    [
        ("/git-file", "r", "some text"),
        ("/git-file", "rb", b"some text"),
        ("/git-annex-file", "r", "annex'ed text"),
        ("/git-annex-file", "rb", b"annex'ed text"),
        ("/hello-world.txt", "r", "Hello World\n"),
        ("/hello-world.txt", "rb", b"Hello World\n"),
        ("/hello-world_fast.txt", "r", "Hello World\n"),
        ("/hello-world_fast.txt", "rb", b"Hello World\n"),
        *(
            pytest.param(
                *x,
                marks=pytest.mark.xfail(
                    reason="Missing size on files from `git annex addurl --relaxed`."
                ),
            )
            for x in [
                ("/hello-world_relaxed.txt", "r", "Hello World\n"),
                ("/hello-world_relaxed.txt", "rb", b"Hello World\n"),
            ]
        ),
        ("/submodule/git-file", "r", "some text in submodule"),
        ("/submodule/git-file", "rb", b"some text in submodule"),
        ("/submodule/git-annex-file", "r", "annex'ed text in submodule"),
        ("/submodule/git-annex-file", "rb", b"annex'ed text in submodule"),
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
    DEFAULT_BLOCK_SIZE = fsspec.spec.AbstractBufferedFile.DEFAULT_BLOCK_SIZE
    assert (
        len(expected_content) > 12345 + 4321 + DEFAULT_BLOCK_SIZE
    ), "The data produced by bytes_data is too short for this test"
    with fs.open("/git-annex-large-file", "rb") as f:
        assert f.read(12345) == expected_content[:12345]
        assert f.read(4321) == expected_content[12345 : 12345 + 4321]
        assert (
            f.read(DEFAULT_BLOCK_SIZE)
            == expected_content[12345 + 4321 : 12345 + 4321 + DEFAULT_BLOCK_SIZE]
        )
        assert f.read() == expected_content[12345 + 4321 + DEFAULT_BLOCK_SIZE :]
