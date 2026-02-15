#include <stdio.h>
#include <string.h>
#include "esp_spiffs.h"
#include "esp_log.h"

typedef struct {
    char word[32];
    char phonetic[32];
    char definition[64];
} word_item_t;

extern word_item_t current_word;
void init_spiffs(void);
bool get_word_from_csv(int line_num, word_item_t *out_item,char *book_name);