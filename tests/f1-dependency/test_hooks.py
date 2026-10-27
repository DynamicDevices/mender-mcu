#!/usr/bin/env python3
# @file      test_hooks.py
# @brief     Exercise application storage and update-state hooks offline
#
# Copyright joelguittet and mender-mcu-client contributors
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

"""Compile the actual hook functions with synthetic platform fault injection.

No Zephyr SDK, cloud credentials, board or package installation is needed.
This deliberately does not substitute for a complete target/integration build.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def function(path, name):
    source = (ROOT / path).read_text()
    match = re.search(r"(?m)^(?:static )?(?:mender_err_t|int|bool)\s+"
                      + re.escape(name) + r"\([^;]*?\)\s*\{", source)
    if not match:
        raise AssertionError(f"function not found: {name}")
    depth = 1
    end = match.end()
    while depth:
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
        end += 1
    return source[match.start():end] + "\n"


COMMON = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <math.h>
typedef int mender_err_t;
enum { MENDER_OK=0, MENDER_FAIL=-1, MENDER_NOT_FOUND=-2, MENDER_LOOP_DETECTED=-3 };
#define mender_log_error(...) ((void)0)
'''


class Hooks(unittest.TestCase):
    def compile_run(self, source):
        with tempfile.TemporaryDirectory(prefix=".fixture-", dir=Path(__file__).parent) as tmp:
            binary = str(Path(tmp) / "test")
            subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
                            "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                            "-fno-pie", "-no-pie", "-x", "c", "-", "-o", binary],
                           input=COMMON + source, text=True, check=True)
            subprocess.run([binary], check=True)

    def test_storage_slots_sizes_and_failures(self):
        path = "src/platform/storage/zephyr/nvs/storage.c"
        stubs = r'''
static bool f1_nvs_mounted;
static int f1_nvs_owner_lock, lock_depth, init_result, io_result, calls;
static unsigned last_id;
static struct { unsigned sector_size; } mender_storage_nvs_handle;
#define K_FOREVER 0
static void k_mutex_lock(int *lock, int timeout) { (void)lock; (void)timeout; assert(++lock_depth==1); }
static void k_mutex_unlock(int *lock) { (void)lock; assert(--lock_depth==0); }
static int mender_storage_init_impl(bool mount_only) {
    (void)mount_only;
    if (!init_result) f1_nvs_mounted=true;
    return init_result;
}
static int nvs_read(void *fs, unsigned id, void *data, size_t len) {
    (void)fs; (void)data; (void)len; assert(lock_depth==1); calls++; last_id=id; return io_result;
}
static int nvs_write(void *fs, unsigned id, const void *data, size_t len) {
    (void)fs; (void)data; (void)len; assert(lock_depth==1); calls++; last_id=id; return io_result;
}
'''
        code = "".join(function(path, n) for n in ["mender_storage_init", "mender_storage_f1_init",
                                                   "mender_storage_f1_read", "mender_storage_f1_write"])
        self.compile_run(stubs + code + r'''
int main(void) {
    char record[2449]={0};
    assert(mender_storage_f1_read(0, record, 16)==-ENODEV);
    assert(mender_storage_f1_write(0, record, 16)==-ENODEV);
    init_result=-1; assert(mender_storage_f1_init()==-EIO);
    init_result=0; mender_storage_nvs_handle.sector_size=2463;
    assert(mender_storage_f1_init()==-ENOSPC);
    mender_storage_nvs_handle.sector_size=4096;
    assert(mender_storage_f1_init()==0); assert(mender_storage_init()==0);
    for(unsigned slot=0; slot<6; slot++) {
        io_result=16; assert(mender_storage_f1_read(slot,record,16)==16); assert(last_id==0xf100+slot);
        assert(mender_storage_f1_write(slot,record,16)==0); assert(last_id==0xf100+slot);
    }
    int before=calls;
    assert(mender_storage_f1_read(6,record,16)==-EINVAL);
    assert(mender_storage_f1_read(0,NULL,16)==-EINVAL);
    assert(mender_storage_f1_read(0,record,0)==-EINVAL);
    assert(mender_storage_f1_read(0,record,2449)==-EINVAL);
    assert(mender_storage_f1_write(6,record,16)==-EINVAL);
    assert(mender_storage_f1_write(0,NULL,16)==-EINVAL);
    assert(mender_storage_f1_write(0,record,15)==-EINVAL);
    assert(mender_storage_f1_write(0,record,2449)==-EINVAL); assert(calls==before);
    io_result=0; assert(mender_storage_f1_write(5,record,2448)==0);
    io_result=2448; assert(mender_storage_f1_write(5,record,2448)==0);
    io_result=15; assert(mender_storage_f1_write(4,record,16)==-EIO);
    io_result=-EIO; assert(mender_storage_f1_write(4,record,16)==-EIO);
    assert(mender_storage_f1_read(4,record,16)==-EIO); assert(lock_depth==0);
    return 0;
}
''')

    def test_pin_persistence_and_cleanup_guards(self):
        path = "src/core/client.c"
        stubs = r'''
static char mender_expected_deployment[37];
static bool mender_expected_deployment_spent, mender_state_persistence_failed, mender_terminal_cleanup_pending;
typedef int mender_update_state_t;
static void *mender_client_deployment_data;
static int delete_result, set_result, store_result, stores;
static int mender_storage_delete_deployment_data(void) { return delete_result; }
static int mender_deployment_data_set_state(void *data, int state) { (void)data; (void)state; return set_result; }
static int mender_set_deployment_data(void *data) { (void)data; stores++; return store_result; }
'''
        code = "".join(function(path, n) for n in ["mender_client_retry_terminal_cleanup",
                     "mender_client_pin_deployment", "mender_client_deployment_allowed", "set_and_store_state"])
        self.compile_run(stubs + code + r'''
int main(void) {
    const char *id="01234567-89ab-cdef-0123-456789abcdef";
    assert(mender_client_deployment_allowed(NULL));
    assert(mender_client_pin_deployment(NULL)==MENDER_FAIL);
    assert(mender_client_pin_deployment("bad")==MENDER_FAIL);
    assert(mender_client_pin_deployment("01234567_89ab-cdef-0123-456789abcdef")==MENDER_FAIL);
    assert(mender_client_pin_deployment(id)==MENDER_OK);
    assert(mender_client_pin_deployment(id)==MENDER_FAIL);
    assert(mender_client_deployment_allowed(id));
    assert(!mender_client_deployment_allowed(NULL));
    assert(!mender_client_deployment_allowed("11234567-89ab-cdef-0123-456789abcdef"));
    delete_result=MENDER_FAIL; assert(mender_client_retry_terminal_cleanup()==MENDER_FAIL);
    assert(mender_terminal_cleanup_pending); assert(!mender_client_deployment_allowed(id));
    delete_result=MENDER_OK; assert(mender_client_retry_terminal_cleanup()==MENDER_OK);
    assert(!mender_terminal_cleanup_pending); assert(!mender_client_deployment_allowed(id));
    set_result=MENDER_FAIL; assert(set_and_store_state(1)==MENDER_FAIL);
    assert(mender_state_persistence_failed); assert(stores==0);
    mender_state_persistence_failed=false; set_result=MENDER_OK; store_result=MENDER_FAIL;
    assert(set_and_store_state(1)==MENDER_FAIL); assert(mender_state_persistence_failed);
    mender_state_persistence_failed=false; store_result=MENDER_OK;
    assert(set_and_store_state(1)==MENDER_OK); assert(!mender_state_persistence_failed);
    return 0;
}
''')

    def test_loop_detection_enters_persisted_failure_without_weakening_latch(self):
        path = "src/core/client.c"
        source = (ROOT / path).read_text()
        worker = function(path, "mender_client_update_work_function")
        self.assertNotIn("set_and_store_state(", worker)
        macro = source[source.index("#define NEXT_STATE"):source.index("\n\n    if (spontaneous_reboot)")]
        stubs = r'''
typedef int mender_update_state_t;
enum { DOWNLOAD, INSTALL, MENDER_UPDATE_STATE_FAILURE, MENDER_UPDATE_STATE_END };
static const struct { int success, failure; } update_state_transitions[] = {
    {INSTALL, MENDER_UPDATE_STATE_FAILURE},
    {MENDER_UPDATE_STATE_END, MENDER_UPDATE_STATE_FAILURE},
    {MENDER_UPDATE_STATE_END, MENDER_UPDATE_STATE_END}
};
static bool mender_state_persistence_failed;
static void *mender_client_deployment_data;
static int writes[4], write_count, last_state, fail_set;
static int install_calls, failure_calls;
static void *mender_update_module = (void *)1;
#define mender_log_debug(...) ((void)0)
static int mender_deployment_data_set_state(void *data, int state) {
    (void)data; last_state = state; return fail_set ? MENDER_FAIL : MENDER_OK;
}
static int mender_set_deployment_data(void *data) {
    (void)data; assert(write_count < 4); return writes[write_count++];
}
'''
        functions = "".join(function(path, name) for name in
                            ["set_and_store_state", "mender_client_persist_transition"])
        harness = r'''
static int run(int initial_result) {
    int ret = initial_result, update_state = DOWNLOAD;
    while (update_state != MENDER_UPDATE_STATE_END) {
        switch (update_state) {
        case DOWNLOAD:
            NEXT_STATE;
            /* fall through */
        case INSTALL:
            install_calls++; ret = MENDER_OK;
            NEXT_STATE;
            break;
        case MENDER_UPDATE_STATE_FAILURE:
            assert(last_state == MENDER_UPDATE_STATE_FAILURE);
            assert(!mender_state_persistence_failed);
            failure_calls++; ret = MENDER_OK;
            NEXT_STATE;
            break;
        default: abort();
        }
    }
END:
    return ret;
}
static void reset(void) {
    memset(writes, 0, sizeof(writes)); write_count = 0; last_state = -1;
    fail_set = 0; install_calls = 0; failure_calls = 0;
    mender_state_persistence_failed = false;
}
int main(void) {
    reset(); writes[0] = MENDER_LOOP_DETECTED;
    assert(run(MENDER_OK) == MENDER_OK);
    assert(install_calls == 0 && failure_calls == 1 && write_count == 3);
    assert(!mender_state_persistence_failed);
    reset(); writes[0] = MENDER_LOOP_DETECTED;
    assert(run(MENDER_FAIL) == MENDER_OK);
    assert(install_calls == 0 && failure_calls == 1 && write_count == 3);
    reset(); writes[0] = MENDER_FAIL;
    assert(run(MENDER_OK) == MENDER_FAIL);
    assert(install_calls == 0 && failure_calls == 0 && mender_state_persistence_failed);
    reset(); writes[0] = MENDER_LOOP_DETECTED; writes[1] = MENDER_FAIL;
    assert(run(MENDER_OK) == MENDER_FAIL);
    assert(install_calls == 0 && failure_calls == 0 && mender_state_persistence_failed);
    reset(); fail_set = 1;
    assert(run(MENDER_OK) == MENDER_FAIL);
    assert(write_count == 0 && failure_calls == 0 && mender_state_persistence_failed);
    reset(); assert(run(MENDER_OK) == MENDER_OK);
    assert(install_calls == 1 && failure_calls == 0 && !mender_state_persistence_failed);
    return 0;
}
'''
        self.compile_run(stubs + functions + macro + "\n" + harness)

    def test_crc_preserves_caller_allocation(self):
        stubs = r'''
static bool fail_alloc;
static void *mender_malloc(size_t n) { return fail_alloc ? NULL : malloc(n); }
static uint32_t crc32_ieee(const char *data, size_t len) {
    (void)data; (void)len; return 0x12345678;
}
'''
        self.compile_run(stubs + function("src/platform/storage/zephyr/nvs/storage.c", "crc_add") + r'''
int main(void) {
    char *original=malloc(4); assert(original); memcpy(original,"abc",4);
    size_t length=4; char *result=NULL;
    fail_alloc=true; assert(crc_add(original,&length,&result)==MENDER_FAIL);
    assert(length==4 && result==NULL && strcmp(original,"abc")==0);
    fail_alloc=false; assert(crc_add(original,&length,&result)==MENDER_OK);
    assert(length==8 && result!=original && memcmp(result,original,4)==0);
    uint32_t crc; memcpy(&crc,result+4,4); assert(crc==0x12345678);
    free(result); assert(strcmp(original,"abc")==0); free(original); return 0;
}
''')

    def test_persisted_summary_validation(self):
        path = "src/core/deployment-data.c"
        stubs = r'''
typedef struct { double value; bool is_number; } cJSON;
typedef cJSON mender_deployment_data_t;
typedef int mender_update_state_t;
enum { MENDER_UPDATE_STATE_END=10 };
#define MENDER_DEPLOYMENT_DATA_KEY_STATE "state"
static cJSON object={1,true};
static const char *saved_id="01234567-89ab-cdef-0123-456789abcdef";
static int load_result, id_result, state_result, freed;
static int mender_get_deployment_data(mender_deployment_data_t **out) { *out=&object; return load_result; }
static const cJSON *cJSON_GetObjectItemCaseSensitive(cJSON *data, const char *key) { (void)key; return data; }
static double cJSON_GetNumberValue(const cJSON *data) { return data->value; }
static bool cJSON_IsNumber(const cJSON *data) { return data->is_number; }
static void mender_delete_deployment_data(cJSON *data) { (void)data; freed++; }
static int mender_deployment_data_get_id(cJSON *data, const char **out) { (void)data; *out=saved_id; return id_result; }
static int mender_deployment_data_get_state(cJSON *data, int *out) { *out=(int)data->value; return state_result; }
'''
        self.compile_run(stubs + function(path, "mender_client_get_persisted_update_summary") + r'''
int main(void) {
    char id[37]; int state;
    assert(mender_client_get_persisted_update_summary(NULL,&state)==MENDER_FAIL);
    assert(mender_client_get_persisted_update_summary(id,NULL)==MENDER_FAIL);
    load_result=MENDER_NOT_FOUND;
    assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_NOT_FOUND);
    assert(id[0]==0 && state==-1 && freed==0);
    load_result=MENDER_FAIL; assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_FAIL);
    load_result=MENDER_OK;
    assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_OK);
    assert(strcmp(id,saved_id)==0 && state==1 && freed==1);
    double bad[]={NAN,INFINITY,-1,1.5,11,1e100};
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++) {
        object.value=bad[i]; assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_FAIL);
        assert(id[0]==0 && state==-1);
    }
    object.value=1; object.is_number=false;
    assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_FAIL);
    object.is_number=true; saved_id="01234567_89ab-cdef-0123-456789abcdef";
    assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_FAIL);
    saved_id=NULL; assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_FAIL);
    saved_id="01234567-89ab-cdef-0123-456789abcdef"; state_result=MENDER_FAIL;
    assert(mender_client_get_persisted_update_summary(id,&state)==MENDER_FAIL);
    return 0;
}
''')


if __name__ == "__main__":
    unittest.main()
