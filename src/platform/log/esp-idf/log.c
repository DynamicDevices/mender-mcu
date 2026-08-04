/**
 * @file      log.c
 * @brief     Mender logging interface for ESP-IDF
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

#include <stdarg.h>
#include <stdio.h>

#include "esp_log.h"

#include "alloc.h"
#include "log.h"

/* Cap heap-backed messages so a runaway format cannot exhaust memory. */
#define MENDER_ESP_LOG_MAX_MSG 2048

mender_err_t
mender_log_init(void) {
    /* Nothing to do */
    return MENDER_OK;
}

mender_err_t
mender_log_print(uint8_t level, const char *filename, const char *function, int line, char *format, ...) {
    char    stack_msg[256];
    char   *msg      = stack_msg;
    char   *heap_msg = NULL;
    va_list args;
    va_list args_copy;
    int     needed;

    va_start(args, format);
    va_copy(args_copy, args);
    needed = vsnprintf(NULL, 0, format, args_copy);
    va_end(args_copy);

    if (needed < 0) {
        va_end(args);
        return MENDER_FAIL;
    }

    if ((size_t)needed + 1 > sizeof(stack_msg)) {
        size_t alloc_len = (size_t)needed + 1;
        if (alloc_len > MENDER_ESP_LOG_MAX_MSG) {
            alloc_len = MENDER_ESP_LOG_MAX_MSG;
        }
        heap_msg = mender_malloc(alloc_len);
        if (NULL != heap_msg) {
            msg = heap_msg;
            vsnprintf(msg, alloc_len, format, args);
        } else {
            /* Fall back to truncated stack buffer if heap is exhausted. */
            vsnprintf(stack_msg, sizeof(stack_msg), format, args);
            msg = stack_msg;
        }
    } else {
        vsnprintf(stack_msg, sizeof(stack_msg), format, args);
    }
    va_end(args);

    esp_log_level_t esp_level;
    switch (level) {
        case MENDER_LOG_LEVEL_ERR:
            esp_level = ESP_LOG_ERROR;
            break;
        case MENDER_LOG_LEVEL_WRN:
            esp_level = ESP_LOG_WARN;
            break;
        case MENDER_LOG_LEVEL_DBG:
            esp_level = ESP_LOG_DEBUG;
            break;
        case MENDER_LOG_LEVEL_INF:
        default:
            esp_level = ESP_LOG_INFO;
            break;
    }

    /* Include source filename in the tag path so it is not dropped. */
    ESP_LOG_LEVEL(esp_level, "mender", "%s:%s:%d: %s", filename ? filename : "?", function, line, msg);

    mender_free(heap_msg);
    return MENDER_OK;
}

mender_err_t
mender_log_exit(void) {
    /* Nothing to do */
    return MENDER_OK;
}
