# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import fsspec


def test_git_annex_protocol_is_available():
    assert "git-annex" in fsspec.available_protocols()
