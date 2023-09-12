# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import tempfile

import fsspec
import fsspec.fuse


def run(args):
    fs = fsspec.filesystem("git-annex", git_url=args.git_url, rev=args.rev)
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = fsspec.filesystem("blockcache", fs=fs, cache_storage=str(tmpdir))
        fsspec.fuse.run(fs, "/", args.mountpoint)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rev",
        default="HEAD",
        help=(
            "The git rev to mount; e.g. a branch name, tag or commit hash. Defaults to"
            " HEAD, i.e. the remote default branch."
        ),
    )
    parser.add_argument(
        "git_url",
        help="The git url to clone from. Anything that `git clone` accepts is allowed.",
    )
    parser.add_argument("mountpoint", help="The path to mount the repository at.")
    args = parser.parse_args()
    run(args)
