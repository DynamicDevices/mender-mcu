/**
 * @file      image_ram_stage_test.cpp
 * @brief     Unit Tests for image-ram-stage.c
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

#include <gtest/gtest.h>
#include <string.h>

extern "C" {
#include "image-ram-stage.h"
}

TEST(ImageRamStage, BeginDisabledLeavesInactive) {
    mender_image_ram_stage_t stage = {};
    ASSERT_EQ(MENDER_OK, mender_image_ram_stage_begin(&stage, 64, false, 0));
    EXPECT_FALSE(mender_image_ram_stage_active(&stage));
    mender_image_ram_stage_reset(&stage);
}

TEST(ImageRamStage, BeginOverMaxLeavesInactive) {
    mender_image_ram_stage_t stage = {};
    ASSERT_EQ(MENDER_OK, mender_image_ram_stage_begin(&stage, 128, true, 64));
    EXPECT_FALSE(mender_image_ram_stage_active(&stage));
    mender_image_ram_stage_reset(&stage);
}

TEST(ImageRamStage, WriteAndLength) {
    mender_image_ram_stage_t stage = {};
    uint8_t                  chunk[4] = { 1, 2, 3, 4 };

    ASSERT_EQ(MENDER_OK, mender_image_ram_stage_begin(&stage, 8, true, 0));
    ASSERT_TRUE(mender_image_ram_stage_active(&stage));
    ASSERT_EQ(MENDER_OK, mender_image_ram_stage_write(&stage, chunk, 0, 4));
    EXPECT_EQ(4u, stage.length);
    ASSERT_EQ(MENDER_OK, mender_image_ram_stage_write(&stage, chunk, 4, 4));
    EXPECT_EQ(8u, stage.length);
    EXPECT_EQ(0, memcmp(stage.buf, "\x1\x2\x3\x4\x1\x2\x3\x4", 8));
    mender_image_ram_stage_reset(&stage);
    EXPECT_FALSE(mender_image_ram_stage_active(&stage));
}

TEST(ImageRamStage, OverflowFails) {
    mender_image_ram_stage_t stage = {};
    uint8_t                  chunk[4] = { 9, 9, 9, 9 };

    ASSERT_EQ(MENDER_OK, mender_image_ram_stage_begin(&stage, 4, true, 0));
    EXPECT_EQ(MENDER_FAIL, mender_image_ram_stage_write(&stage, chunk, 2, 4));
    mender_image_ram_stage_reset(&stage);
}

TEST(ImageRamStage, NullArgsFail) {
    EXPECT_EQ(MENDER_FAIL, mender_image_ram_stage_begin(NULL, 4, true, 0));
    EXPECT_FALSE(mender_image_ram_stage_active(NULL));
    EXPECT_EQ(MENDER_FAIL, mender_image_ram_stage_write(NULL, "x", 0, 1));
}
