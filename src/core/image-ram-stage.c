/**
 * @file      image-ram-stage.c
 * @brief     Whole-image RAM staging helpers (platform-independent)
 *
 * Copyright Northern.tech AS
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <string.h>

#include "alloc.h"
#include "image-ram-stage.h"

mender_err_t
mender_image_ram_stage_begin(mender_image_ram_stage_t *stage, size_t size, bool enabled, size_t max_size) {
    if (NULL == stage) {
        return MENDER_FAIL;
    }

    mender_image_ram_stage_reset(stage);

    if (!enabled || 0 == size) {
        return MENDER_OK;
    }
    if ((max_size > 0) && (size > max_size)) {
        return MENDER_OK;
    }

    stage->buf = mender_malloc(size);
    if (NULL == stage->buf) {
        return MENDER_OK;
    }
    stage->capacity = size;
    stage->length   = 0;
    return MENDER_OK;
}

bool
mender_image_ram_stage_active(const mender_image_ram_stage_t *stage) {
    return (NULL != stage) && (NULL != stage->buf);
}

mender_err_t
mender_image_ram_stage_write(mender_image_ram_stage_t *stage, const void *data, size_t index, size_t length) {
    if ((NULL == stage) || (NULL == stage->buf) || (NULL == data)) {
        return MENDER_FAIL;
    }
    if (index + length > stage->capacity) {
        return MENDER_FAIL;
    }
    memcpy(stage->buf + index, data, length);
    if (index + length > stage->length) {
        stage->length = index + length;
    }
    return MENDER_OK;
}

void
mender_image_ram_stage_reset(mender_image_ram_stage_t *stage) {
    if (NULL == stage) {
        return;
    }
    if (NULL != stage->buf) {
        mender_free(stage->buf);
    }
    stage->buf      = NULL;
    stage->capacity = 0;
    stage->length   = 0;
}
