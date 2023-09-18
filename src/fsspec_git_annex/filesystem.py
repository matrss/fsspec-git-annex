# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import subprocess
import tempfile
from pathlib import Path

from fsspec import AbstractFileSystem
from fsspec.spec import AbstractBufferedFile

from .git_annex import GitAnnexRepo

logger = logging.getLogger(__name__)


class GitAnnexFile(AbstractBufferedFile):
    def _fetch_range(self, start, end):
        repository = self.fs._get_repository_for_path(self.path)
        relative_path = (
            self.fs._repositories["/"].path / Path(self.path).relative_to("/")
        ).relative_to(repository.path)
        if end >= self.size:
            repository.get(relative_path)
            full_path = repository.path / relative_path
            with open(full_path, "rb") as f:
                f.seek(start)
                buf = f.read(end - start)
            repository.drop(relative_path, force=True)
            return buf
        else:
            repository.get_num_bytes(relative_path, end)
            full_path = (repository.path / relative_path).resolve()
            filename = full_path.name
            tmp_path = repository.path / ".git" / "annex" / "tmp" / filename
            if tmp_path.exists():
                data_path = tmp_path
            else:  # file was fetched completely
                data_path = full_path
            with open(data_path, "rb") as f:
                f.seek(start)
                buf = f.read(end - start)
            repository.drop(relative_path, force=True)
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
        target_directory = Path(target_directory)
        self._repositories = {}
        self._repositories["/"] = GitAnnexRepo.clone(
            git_url, target_directory, private=True
        )
        self._repositories["/"].switch(rev, detach=True)
        self._repositories["/"].submodule_update()
        for submodule_path in self._repositories["/"].submodule_list():
            self._repositories["/" + submodule_path] = GitAnnexRepo(
                target_directory / submodule_path
            )

    def _get_repository_for_path(self, path):
        # If path itself is a repository return that
        if str(path) in self._repositories.keys():
            return self._repositories[str(path)]
        # If any of paths parents are a repository return that
        for parent in Path(path).parents:
            if str(parent) in self._repositories.keys():
                return self._repositories[str(parent)]
        # Otherwise use the root repository
        return self._repositories["/"]

    def ls(self, path, detail=True, **kwargs):
        path = self._strip_protocol(path)

        if path not in self.dircache:
            repository = self._get_repository_for_path(path)
            relative_path = (
                self._repositories["/"].path / Path(path).relative_to("/")
            ).relative_to(repository.path)
            entries = repository.ls_tree(relative_path)
            detailed_entries = []
            for e in entries:
                full_path = repository.path / e
                entry_type = "directory" if full_path.is_dir() else "file"
                stat = full_path.lstat()
                try:
                    annex_info = repository.info(e)
                    size = int(annex_info["size"].split(" ", 1)[0])
                    if size == 0:
                        logger.warning(
                            "'%s' has a reported size of 0 bytes; git-annex probably "
                            "does not know the real size of the file. This will lead to"
                            " issues reading it.",
                            str(e),
                        )
                except (subprocess.CalledProcessError, KeyError):
                    size = stat.st_size
                detailed_entries.append(
                    {
                        "created": stat.st_ctime,
                        "gid": stat.st_gid,
                        "ino": stat.st_ino,
                        "mode": 0o755 if entry_type == "directory" else 0o644,
                        "mtime": stat.st_mtime,
                        "name": str(
                            Path("/")
                            / repository.path.relative_to(self._repositories["/"].path)
                            / e
                        ),
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
        repository = self._get_repository_for_path(path)
        if path == "/":
            stat = repository.path.stat()
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
