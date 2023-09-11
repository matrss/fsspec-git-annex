# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path


class GitRepo:
    def __init__(self, path):
        self.path = Path(path)

    @classmethod
    def clone(cls, git_url, target_directory):
        cmd = ["git", "clone", str(git_url), str(target_directory)]
        subprocess.run(cmd, capture_output=True, check=True)
        return cls(target_directory)

    def set_config(self, key, value):
        cmd = ["git", "-C", str(self.path), "config", str(key), str(value)]
        subprocess.run(cmd, capture_output=True, check=True)

    def ls_tree(self, path=None, trees_only=False):
        if path is None:
            path = "."
        path = "./" + str(path).lstrip("/")
        if (self.path / path).is_dir():
            path += "/"
        cmd = (
            ["git", "-C", str(self.path), "ls-tree", "HEAD", "--name-only", "-z"]
            + (["-d"] if trees_only else [])
            + [path]
        )
        result = subprocess.run(cmd, capture_output=True, check=True)
        files = result.stdout.split(b"\0")[:-1]
        return [f.decode() for f in files]

    def show(self, obj):
        cmd = ["git", "-C", str(self.path), "show", str(obj)]
        result = subprocess.run(cmd, capture_output=True, check=True)
        return result.stdout

    def switch(self, commit, detach=False):
        cmd = (
            [
                "git",
                "-C",
                str(self.path),
                "switch",
            ]
            + (["--detach"] if detach else [])
            + [str(commit)]
        )
        subprocess.run(cmd, capture_output=True, check=True)
