#include "ai_demo_task.h"

#include <stdio.h>
#include <time.h>
#include <string.h>
#include <stdlib.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "ai_chat.h"
#include "wifi.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"

typedef struct {
    bool *ntp_initialized;
    const char *api_key;
} ai_demo_args_t;

static void ai_demo_task(void *param)
{
    ai_demo_args_t *args = (ai_demo_args_t *)param;
    bool *ntp_initialized = args ? args->ntp_initialized : NULL;
    const char *api_key = args ? args->api_key : NULL;

    const size_t file_content_size = 1024;
    const size_t prompt_size = 1536;
    char *file_content = NULL;
    char *prompt = NULL;
    char *response = NULL;

    if (!api_key || api_key[0] == '\0') {
        printf("[AI Demo] 未配置 API Key，请检查 ai_chat_secrets.h\r\n");
        free(args);
        vTaskDelete(NULL);
        return;
    }

    ai_chat_init(NULL, api_key, NULL);

    file_content = (char *)heap_caps_malloc(file_content_size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    prompt = (char *)heap_caps_malloc(prompt_size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    response = (char *)heap_caps_malloc(AI_RESPONSE_BUF_SIZE, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!file_content || !prompt || !response) {
        printf("[AI Demo] 内存分配失败: file=%p prompt=%p response=%p\r\n", file_content, prompt, response);
        free(file_content);
        free(prompt);
        free(response);
        free(args);
        vTaskDelete(NULL);
        return;
    }

    printf("\r\n[AI Demo] 等待 WiFi 连接...\r\n");
    while (!is_wifi_connected()) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    vTaskDelay(pdMS_TO_TICKS(5000));
    printf("[AI Demo] WiFi 已连接，等待 NTP 时间同步...\r\n");

    if (ntp_initialized && !(*ntp_initialized)) {
        initialize_sntp();
        *ntp_initialized = true;
        printf("[AI Demo] 已初始化 NTP，正在等待时间同步...\r\n");
    }

    bool time_synced = false;
    while(1){
        time_t now = 0;
        struct tm timeinfo = {0};
        time(&now);
        localtime_r(&now, &timeinfo);
        if (timeinfo.tm_year + 1900 >= 2025) {
            printf("[AI Demo] 时间已同步: %04d-%02d-%02d %02d:%02d:%02d\r\n",
                   timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                   timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
            time_synced = true;
            break;
        } else {
            printf("[AI Demo] 当前时间未同步: %04d-%02d-%02d %02d:%02d:%02d\r\n",
                   timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                   timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    if (!time_synced) {
        printf("[AI Demo] NTP 时间同步失败，无法进行 HTTPS 请求\r\n");
        free(file_content);
        free(prompt);
        free(response);
        free(args);
        vTaskDelete(NULL);
        return;
    }
    printf("[AI Demo] 开始请求 AI...\r\n");

    FILE *file = fopen("/spiffs/todolist.csv", "r");
    if (file == NULL) {
        printf("[AI Demo] 无法打开 /spiffs/todolist.csv\r\n");
        free(file_content);
        free(prompt);
        free(response);
        free(args);
        vTaskDelete(NULL);
        return;
    }

    int total = fread(file_content, 1, file_content_size - 1, file);
    fclose(file);
    file_content[total] = '\0';
    printf("[AI Demo] 读取到 %d 字节的任务数据:\r\n%s\r\n", total, file_content);

    snprintf(prompt, prompt_size,
             "以下是我的10条todolist任务（CSV格式，包含任务名称、专注时间min、完成日期）：\n\n"
             "%s\n\n"
             "请将任务分成3类，并严格只输出下面5行（不要输出任何额外文字、解释、标题、表格、Markdown）：\n"
             "CAT1|<分类名称>|<占比整数%%>\n"
             "CAT2|<分类名称>|<占比整数%%>\n"
             "CAT3|<分类名称>|<占比整数%%>\n"
             "SUMMARY|<一句话总结全部任务，不超过30字>\n"
             "END\n"
             "规则：\n"
             "1) 占比按任务数量计算，三个占比相加必须等于100%%；\n"
             "2) 分类名称不超过8个汉字；\n"
             "3) 只能返回这5行，且顺序固定。",
             file_content);

    free(file_content);
    file_content = NULL;

    printf("[AI Demo] 正在发送请求给 AI，请稍候...\r\n");
    int64_t t_start = esp_timer_get_time();
    esp_err_t ret = ai_chat_send(prompt, response, AI_RESPONSE_BUF_SIZE);
    int64_t t_end = esp_timer_get_time();
    int elapsed_ms = (int)((t_end - t_start) / 1000);

    if (ret == ESP_OK) {
        printf("\r\n===== AI 分类结果 =====\r\n%s\r\n", response);
        printf("========================\r\n");
        printf("[AI Demo] 响应耗时: %d ms\r\n", elapsed_ms);
    } else {
        printf("[AI Demo] 请求失败 (%d ms): %s\r\n", elapsed_ms, response);
    }

    printf("[AI Demo] 任务完成。\r\n");
    free(prompt);
    free(response);
    free(args);
    vTaskDelete(NULL);
}

void start_ai_demo_task(bool *ntp_initialized, const char *api_key)
{
    ai_demo_args_t *args = (ai_demo_args_t *)malloc(sizeof(ai_demo_args_t));
    if (!args) {
        printf("[AI Demo] 启动失败：参数内存分配失败\r\n");
        return;
    }

    args->ntp_initialized = ntp_initialized;
    args->api_key = api_key;
    xTaskCreatePinnedToCore(ai_demo_task, "ai_demo_task", 12288, args, 5, NULL, 1);
}
