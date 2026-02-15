#include "word_storage.h"
static const char *TAG = "DICT_READER";

word_item_t current_word = {
    .definition = "",
    .phonetic = "",
    .word = ""
};

void init_spiffs(void) {
    esp_vfs_spiffs_conf_t conf = {
        .base_path = "/spiffs",
        .partition_label = "storage",
        .max_files = 5,
        .format_if_mount_failed = true
    };

    esp_err_t ret = esp_vfs_spiffs_register(&conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to mount or format filesystem");
    } else {
        ESP_LOGI(TAG, "SPIFFS mounted successfully");
    }
}
// 读取 CSV 文件的第 line_num 行 (从0开始)
bool get_word_from_csv(int line_num, word_item_t *out_item, char *book_name) {
    char book_path[50];
    sniprintf(book_path,sizeof(book_path),"/spiffs/%s.csv",book_name);
    FILE *f = fopen(book_path, "r");
    if (f == NULL) {
        ESP_LOGI(TAG, "Failed to open file");
        return false;
    }

    char line_buffer[256];
    int current_line = 0;
    bool found = false;

    // 逐行读取，直到找到目标行
    while (fgets(line_buffer, sizeof(line_buffer), f) != NULL) {
        if (current_line == line_num) {
            // 找到目标行，开始解析
            // 格式: abandon,[ə'bændən],v.放弃;抛弃;放纵
            
            // 1. 获取单词 (以逗号分隔)
            char *token = strtok(line_buffer, ",");
            if (token) strncpy(out_item->word, token, sizeof(out_item->word) - 1);

            // 2. 获取音标
            token = strtok(NULL, ","); // 继续分割
            if (token) strncpy(out_item->phonetic, token, sizeof(out_item->phonetic) - 1);

            // 3. 获取释义 (读到行尾)
            token = strtok(NULL, "\n"); // 取剩余部分直到换行符
            if (token) strncpy(out_item->definition, token, sizeof(out_item->definition) - 1);

            found = true;
            break;
        }
        current_line++;
    }

    fclose(f);
    return found;
}