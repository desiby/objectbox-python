# Copyright 2019 ObjectBox Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from objectbox.c import *
from contextlib import contextmanager


@contextmanager
def read(ob: 'ObjectBox'):
    tx = obx_txn_begin_read(ob._c_store)
    try:
        yield
    finally:
        obx_txn_close(tx)


@contextmanager
def write(ob: 'ObjectBox'):
    tx = obx_txn_begin(ob._c_store)
    successful = False
    try:
        yield
        successful = True
    finally:
        # this is better than bare `except:` because it doesn't catch stuff like KeyboardInterrupt
        if successful:
            obx_txn_commit(tx)
        else:
            obx_txn_abort(tx)

        obx_txn_close(tx)