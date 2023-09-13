# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import tempfile
from pathlib import Path

from fsspec import AbstractFileSystem
from fsspec.spec import AbstractBufferedFile

from .git_annex import GitAnnexRepo


class GitAnnexFile(AbstractBufferedFile):
    def _fetch_range(self, start, end):
        if end >= self.size:
            self.fs._repository.get(self.path)
            path = Path(self.path)
            full_path = self.fs._repository.path / path.relative_to("/")
            with open(full_path, "rb") as f:
                f.seek(start)
                buf = f.read(end - start)
            self.fs._repository.drop(self.path, force=True)
            return buf
        else:
            self.fs._repository.get_num_bytes(self.path, end)
            path = Path(self.path)
            full_path = (self.fs._repository.path / path.relative_to("/")).resolve()
            filename = full_path.name
            tmp_path = self.fs._repository.path / ".git" / "annex" / "tmp" / filename
            if tmp_path.exists():
                data_path = tmp_path
            else:  # file was fetched completely
                data_path = full_path
            with open(data_path, "rb") as f:
                f.seek(start)
                buf = f.read(end - start)
            self.fs._repository.drop(self.path, force=True)
            return buf


class GitAnnexFileSystem(AbstractFileSystem):
    protocol = "git-annex"
    root_marker = "/"

    def __init__(self, git_url, *args, rev="HEAD", target_directory=None, **kwargs):
        super().__init__(*args, **kwargs)
        if target_directory is None:
            # Assign object to attribute to bind to lifetime of this filesystem object.
            # TemporaryDirectory removes the created directory when the object is gc'ed.
            self._temp_dir_obj = tempfile.TemporaryDirectory()
            target_directory = self._temp_dir_obj.name
        self._repository = GitAnnexRepo.private_clone(git_url, target_directory)
        self._repository.switch(rev, detach=True)

    def ls(self, path, detail=True, **kwargs):
        path = self._strip_protocol(path)
        if path not in self.dircache:
            entries = self._repository.ls_tree(path)
            detailed_entries = []
            for e in entries:
                full_path = self._repository.path / e
                entry_type = "directory" if full_path.is_dir() else "file"
                stat = full_path.lstat()
                try:
                    annex_info = self._repository.info(e)
                    size = int(annex_info["size"])
                except (subprocess.CalledProcessError, KeyError):
                    size = stat.st_size
                detailed_entries.append(
                    {
                        "created": stat.st_ctime,
                        "gid": stat.st_gid,
                        "ino": stat.st_ino,
                        "mode": 0o755 if entry_type == "directory" else 0o644,
                        "mtime": stat.st_mtime,
                        "name": "/" + e,
                        "nlink": stat.st_nlink,
                        "size": size,
                        "type": entry_type,
                        "uid": stat.st_uid,
                    }
                )
            self.dircache[path] = detailed_entries
        entries = self.dircache[path]
        if not detail:
            return [entry["name"] for entry in entries]
        return entries

    def info(self, path, **kwargs):
        path = self._strip_protocol(path)
        if path == "/":
            stat = self._repository.path.stat()
            return {
                "created": stat.st_ctime,
                "gid": stat.st_gid,
                "ino": stat.st_ino,
                "mode": 0o755,
                "mtime": stat.st_mtime,
                "name": "/",
                "nlink": stat.st_nlink,
                "size": stat.st_size,
                "type": "directory",
                "uid": stat.st_uid,
            }
        return super().info(path)

    def _open(
        self,
        path,
        mode="rb",
        block_size=None,
        autocommit=True,
        cache_options=None,
        **kwargs,
    ):
        return GitAnnexFile(
            self,
            path,
            mode,
            block_size,
            autocommit,
            cache_options=cache_options,
            **kwargs,
        )
