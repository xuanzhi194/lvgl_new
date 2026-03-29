#include "wifi.h"

static const char *TAG = "NTP_TIME";

// Definitions of the global variables for scan results
wifi_scan_info_t g_scan_results[MAX_SCAN_RECORDS];
uint16_t g_scan_ap_num = 0;

/**
 * @brief Default event handler for WiFi and IP events
 */
void my_esp_event(void* event_handler_arg, esp_event_base_t event_base, int32_t event_id, void* event_data)
{
    // 1. Handling WiFi Events
    if (event_base == WIFI_EVENT) {
        if (event_id == WIFI_EVENT_STA_DISCONNECTED) {
            wifi_event_sta_disconnected_t *disc = (wifi_event_sta_disconnected_t *)event_data;
            int reason = disc ? disc->reason : -1;
            printf("WiFi Connection Disconnected.\n");
            ESP_LOGW(TAG, "STA disconnected, reason=%d", reason);
        }
    }
    // 2. Handling IP Events
    else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        printf("IP Address obtained successfully!\n");
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;         
        char ip_str[16];
        sprintf(ip_str, IPSTR, IP2STR(&event->ip_info.ip));     
        printf("Station IP Address: %s\n", ip_str);
    }
}

/**
 * @brief Initialize WiFi in Station mode and start the driver
 */
void init_wifi()
{
    esp_netif_init();               // Initialize the underlying TCP/IP stack
    esp_event_loop_create_default(); // Create the default system event loop
    
    // Create the default WiFi Station interface
    esp_netif_create_default_wifi_sta(); 
    printf("WiFi stack initialization complete!\n");

    // Step 2: Register Event Handlers
    esp_event_handler_instance_t wifi_event_handler;
    esp_event_handler_instance_register(WIFI_EVENT, 
                                        ESP_EVENT_ANY_ID, 
                                        &my_esp_event, 
                                        NULL, 
                                        &wifi_event_handler);

    esp_event_handler_instance_t ip_event_handler;
    esp_event_handler_instance_register(IP_EVENT, 
                                        IP_EVENT_STA_GOT_IP, 
                                        &my_esp_event, 
                                        NULL, 
                                        &ip_event_handler);
    printf("WiFi and IP event handlers registered!\n");

    // Step 3: WiFi Configuration
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT(); 
    esp_wifi_init(&cfg);
    esp_wifi_set_mode(WIFI_MODE_STA);
    
    esp_wifi_start(); // Start the WiFi driver (Turns on RF hardware)
    // Disable modem sleep to avoid beacon timeout on weak/interference-prone links.
    esp_wifi_set_ps(WIFI_PS_NONE);
    printf("WiFi driver started!\n");
}

void wifi_connect_to_new_network(const char *ssid, const char *password) {
    wifi_config_t wifi_config = { 0 };

    // 1. Copy the new credentials into the config structure
    strncpy((char *)wifi_config.sta.ssid, ssid, sizeof(wifi_config.sta.ssid));
    strncpy((char *)wifi_config.sta.password, password, sizeof(wifi_config.sta.password));
    
    // Set security threshold (match your init_wifi setting)
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    // 2. Stop any existing connection attempt
    esp_wifi_disconnect();

    // 3. Apply the new configuration to the Station interface
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);

    // 4. Trigger the connection process
    esp_wifi_connect();
    
    printf("Connecting to WiFi: %s...\n", ssid);
}

/**
 * @brief Initialize Simple Network Time Protocol (SNTP) for time synchronization
 */
void initialize_sntp() {
    ESP_LOGI(TAG, "Initializing SNTP");
    // Set operating mode to polling
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    
    // Configure NTP servers
    esp_sntp_setservername(0, "pool.ntp.org");      // Global pool
    esp_sntp_setservername(1, "cn.pool.ntp.org");   // China pool
    esp_sntp_setservername(2, "ntp1.aliyun.com");   // AliCloud NTP
    
    esp_sntp_init();

    // Set timezone to Beijing Time (UTC+8)
    setenv("TZ", "CST-8", 1);
    tzset();
}

/**
 * @brief Check if the WiFi station has a valid IP address
 */
bool is_wifi_connected(void)
{
    // Retrieve the handle for the default Station interface
    esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    if (netif == NULL) return false; 

    esp_netif_ip_info_t ip_info;
    if (esp_netif_get_ip_info(netif, &ip_info) != ESP_OK) return false;

    // A non-zero IP address indicates a successful connection
    return (ip_info.ip.addr != 0);
}

/**
 * @brief Scans for available APs, performs deduplication, and stores top 5 results
 */
void wifi_scan_top_5(void) {
    wifi_scan_config_t scan_config = {
        .show_hidden = false,
        .scan_type = WIFI_SCAN_TYPE_ACTIVE,
    };

    // Step 1: Start blocking scan (Wait until scan is complete)
    printf("Starting WiFi scan...\n");
    esp_err_t ret = esp_wifi_scan_start(&scan_config, true);
    if (ret != ESP_OK) return;

    // Step 2: Get the total number of APs found
    uint16_t ap_count = 0;
    esp_wifi_scan_get_ap_num(&ap_count);
    
    // Allocate temporary memory to store raw scan results
    wifi_ap_record_t *ap_records = malloc(sizeof(wifi_ap_record_t) * ap_count);
    if (ap_records == NULL) return;

    // Step 3: Fetch AP records into memory
    esp_wifi_scan_get_ap_records(&ap_count, ap_records);

    // Step 4: Deduplication logic (Filter multiple BSSIDs with the same SSID)
    g_scan_ap_num = 0;
    memset(g_scan_results, 0, sizeof(g_scan_results));

    for (int i = 0; i < ap_count; i++) {
        bool already_exists = false;
        char *current_ssid = (char *)ap_records[i].ssid;

        // Check if the SSID is already in our global results array
        for (int j = 0; j < g_scan_ap_num; j++) {
            if (strcmp(g_scan_results[j].ssid, current_ssid) == 0) {
                already_exists = true;
                // If the same SSID is found, keep the record with the stronger RSSI
                if (ap_records[i].rssi > g_scan_results[j].rssi) {
                    g_scan_results[j].rssi = ap_records[i].rssi;
                }
                break;
            }
        }

        // If SSID is unique, add it to the top 5 list
        if (!already_exists && g_scan_ap_num < MAX_SCAN_RECORDS) {
            strncpy(g_scan_results[g_scan_ap_num].ssid, current_ssid, 32);
            g_scan_results[g_scan_ap_num].rssi = ap_records[i].rssi;
            g_scan_ap_num++;
        }
    }

    // Print final filtered scan list
    for(int k=0; k < g_scan_ap_num; k++) {
        printf("Final List [%d]: %s (%d dBm)\n", k, g_scan_results[k].ssid, g_scan_results[k].rssi);
    }

    free(ap_records);
    esp_wifi_scan_stop(); // Clear scan list from memory
}