# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import fsspec
import pytest


@pytest.fixture(scope="module")
def fs(simple_repository):
    return fsspec.filesystem("git-annex", git_url=simple_repository.path)


def test_ls(fs):
    assert sorted(fs.ls("", detail=False)) == ["/git-annex-file", "/git-file"]


@pytest.mark.parametrize(
    "path,expected_content",
    [("/git-file", "some text"), ("/git-annex-file", "annex'ed text")],
)
def test_read(fs, path, expected_content):
    with fs.open(path, "r") as f:
        assert f.read() == expected_content
