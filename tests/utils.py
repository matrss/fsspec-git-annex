# SPDX-FileCopyrightText: 2023 Matthias Riße <m.risse@fz-juelich.de>
#
# SPDX-License-Identifier: Apache-2.0

import functools
import random


@functools.lru_cache(maxsize=4)
def bytes_data(seed):
    num_bytes = 1 * 1024 * 1024  # 1 MiB
    r = random.Random(seed)
    return r.randbytes(num_bytes)
