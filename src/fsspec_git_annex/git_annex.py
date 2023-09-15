# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess

from .git import GitRepo


class GitAnnexRepo(GitRepo):
    @classmethod
    def clone(cls, git_url, target_directory, private=False):
        repo = super().clone(git_url, target_directory)
        if private:
            repo.set_config("annex.private", "true")
        repo.annex_init()
        return repo

    @classmethod
    def init(cls, path):
        repo = super().init(path)
        repo.annex_init()
        return repo

    def annex_add(self, path):
        cmd = ["git", "-C", str(self.path), "annex", "add", str(path)]
        subprocess.run(cmd, capture_output=True, check=True)

    def annex_init(self):
        cmd = ["git", "-C", str(self.path), "annex", "init"]
        subprocess.run(cmd, capture_output=True, check=True)

    def addurl(self, url, path=None, fast=False, relaxed=False):
        cmd = (
            ["git", "-C", str(self.path), "annex", "addurl"]
            + (["--file", str(path)] if path is not None else [])
            + (["--relaxed"] if relaxed else [])
            + (["--fast"] if fast else [])
            + [str(url)]
        )
        subprocess.run(cmd, capture_output=True, check=True)

    def get(self, path):
        cmd = ["git", "-C", str(self.path), "annex", "get", str(path).lstrip("/")]
        subprocess.run(cmd, capture_output=True, check=True)

    def get_num_bytes(self, path, n):
        cmd = [
            "git",
            "-C",
            str(self.path),
            "annex",
            "get",
            "--json-progress",
            str(path).lstrip("/"),
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            progress = process.stdout.readline()
            if progress == b"":
                break
            progress = json.loads(progress)
            is_finished_successfully = progress.get("success", False)
            if is_finished_successfully or int(progress["byte-progress"]) >= n:
                break
        process.terminate()

    def drop(self, path, force=False):
        cmd = (
            ["git", "-C", str(self.path), "annex", "drop"]
            + (["--force"] if force else [])
            + [str(path).lstrip("/")]
        )
        subprocess.run(cmd, capture_output=True, check=True)

    def info(self, path):
        cmd = [
            "git",
            "-C",
            str(self.path),
            "annex",
            "info",
            "--json",
            "--bytes",
            str(path).lstrip("/"),
        ]
        result = subprocess.run(cmd, capture_output=True, check=True)
        info_data = json.loads(result.stdout)
        return info_data
