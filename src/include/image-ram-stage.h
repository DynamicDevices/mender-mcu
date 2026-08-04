/**
 * @file      image-ram-stage.h
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

#ifndef __MENDER_IMAGE_RAM_STAGE_PRIV_H__
#define __MENDER_IMAGE_RAM_STAGE_PRIV_H__

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <mender/utils.h>

typedef struct mender_image_ram_stage {
    uint8_t *buf;
    size_t   capacity;
    size_t   length;
} mender_image_ram_stage_t;

/**
 * @brief Try to allocate a staging buffer for @p size bytes
 * @param stage     Staging state (must not be NULL)
 * @param size      Artifact payload size
 * @param enabled   When false, leave stage inactive (direct-to-flash)
 * @param max_size  When > 0 and size > max_size, leave stage inactive
 * @return MENDER_OK always (inactive stage is a valid outcome); MENDER_FAIL on bad args
 *
 * Allocation uses mender_malloc. Failure to allocate leaves the stage inactive.
 */
mender_err_t mender_image_ram_stage_begin(mender_image_ram_stage_t *stage, size_t size, bool enabled, size_t max_size);

bool mender_image_ram_stage_active(const mender_image_ram_stage_t *stage);

/**
 * @brief Copy a download chunk into the staging buffer
 * @return MENDER_OK, or MENDER_FAIL on overflow / inactive stage / bad args
 */
mender_err_t mender_image_ram_stage_write(mender_image_ram_stage_t *stage, const void *data, size_t index, size_t length);

/** Free staging buffer and clear state. */
void mender_image_ram_stage_reset(mender_image_ram_stage_t *stage);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __MENDER_IMAGE_RAM_STAGE_PRIV_H__ */
