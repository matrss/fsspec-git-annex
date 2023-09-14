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

    @classmethod
    def init(cls, path):
        cmd = ["git", "init", str(path)]
        subprocess.run(cmd, capture_output=True, check=True)
        return cls(path)

    def add(self, path):
        cmd = ["git", "-C", str(self.path), "add", str(path)]
        subprocess.run(cmd, capture_output=True, check=True)

    def commit(self, message):
        cmd = ["git", "-C", str(self.path), "commit", "-m", str(message)]
        subprocess.run(cmd, capture_output=True, check=True)

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
