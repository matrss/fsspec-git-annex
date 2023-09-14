# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import functools
import random

import fsspec


@functools.lru_cache(maxsize=4)
def bytes_data(seed):
    # 2*DEFAULT_BLOCK_SIZE + 1 MiB (11 MiB at the time of writing)
    num_bytes = fsspec.spec.AbstractBufferedFile.DEFAULT_BLOCK_SIZE * 2 + 1024 * 1024
    r = random.Random(seed)
    return r.randbytes(num_bytes)
