#include "bsp_ble.h"
#include "esp_log.h"
#include <string.h>

/* NimBLE Includes */
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"

static const char *TAG = "REPPO_BLE";

/* 16 Bit BLE UUIDs for a simple Custom Service */
/* Device Service: 0x00FF, Write/Read Characteristic: 0xFF01 */
#define GATTS_SERVICE_UUID 0x00FF
#define GATTS_CHAR_UUID    0xFF01

static uint8_t ble_addr_type;
static void ble_app_advertise(void);

/* Write callback: Triggered when the phone writes to our characteristic */
static int device_write_cb(uint16_t conn_handle, uint16_t attr_handle, struct ble_gatt_access_ctxt *ctxt, void *arg)
{
    // The data written by the phone is inside ctxt->om
    char *data = (char *)ctxt->om->om_data;
    uint16_t len = ctxt->om->om_len;
    
    // Print the received data to the serial port
    ESP_LOGI(TAG, "==== Received message from phone: %.*s ====", len, data);
    return 0;
}

/* Service Definition */
static const struct ble_gatt_svc_def gatts_defs[] = {
    {
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = BLE_UUID16_DECLARE(GATTS_SERVICE_UUID),
        .characteristics = (struct ble_gatt_chr_def[]){
            {
                .uuid = BLE_UUID16_DECLARE(GATTS_CHAR_UUID),
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_WRITE_NO_RSP,
                .access_cb = device_write_cb,
            },
            {
                0, /* No more characteristics */
            }
        },
    },
    {
        0, /* No more services */
    },
};

static int bsp_ble_gap_event(struct ble_gap_event *event, void *arg)
{
    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        ESP_LOGI(TAG, "BLE GAP EVENT CONNECT %s", event->connect.status == 0 ? "OK" : "Failed");
        if (event->connect.status != 0) {
            ble_app_advertise(); // Resume advertising if failed
        }
        break;
    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(TAG, "BLE GAP EVENT DISCONNECTED");
        ble_app_advertise(); // Resume advertising when disconnected
        break;
    case BLE_GAP_EVENT_ADV_COMPLETE:
        ESP_LOGI(TAG, "BLE GAP EVENT ADV COMPLETE");
        ble_app_advertise();
        break;
    }
    return 0;
}

static void ble_app_advertise(void)
{
    struct ble_gap_adv_params adv_params;
    struct ble_hs_adv_fields fields;
    int rc;

    memset(&fields, 0, sizeof(fields));
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    fields.name = (uint8_t *)"ESP32_BLE_Device"; // The name the phone sees
    fields.name_len = strlen("ESP32_BLE_Device");
    fields.name_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Advertising set fields failed: %d", rc);
        return;
    }

    memset(&adv_params, 0, sizeof(adv_params));
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;

    rc = ble_gap_adv_start(ble_addr_type, NULL, BLE_HS_FOREVER, &adv_params, bsp_ble_gap_event, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Advertising start failed: %d", rc);
    } else {
        ESP_LOGI(TAG, "Advertising started...");
    }
}

static void ble_app_on_sync(void)
{
    ble_hs_id_infer_auto(0, &ble_addr_type); // Automatically determine address type
    ble_app_advertise();                     // Start advertising
}

static void ble_app_on_reset(int reason)
{
    ESP_LOGI(TAG, "Resetting state; reason=%d", reason);
}

static void ble_host_task(void *param)
{
    ESP_LOGI(TAG, "BLE Host Task Started");
    nimble_port_run();             // This function blocks until nimble_port_stop() is called
    nimble_port_freertos_deinit();
}

void bsp_ble_init(void)
{
    int rc;

    ESP_LOGI(TAG, "Initializing NimBLE...");

    // Initialize the NimBLE host stack
    rc = nimble_port_init();
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to initialize nimble port, rc=%d", rc);
        return;
    }

    // Set callback functions
    ble_hs_cfg.sync_cb = ble_app_on_sync;
    ble_hs_cfg.reset_cb = ble_app_on_reset;

    // Configure and add services
    rc = ble_gatts_count_cfg(gatts_defs);
    if(rc != 0){
        ESP_LOGE(TAG, "ble_gatts_count_cfg failed!");
    }

    rc = ble_gatts_add_svcs(gatts_defs);
    if(rc != 0){
        ESP_LOGE(TAG, "ble_gatts_add_svcs failed!");
    }

    // Set logical device name
    ble_svc_gap_device_name_set("REPPO_BLE_Device");

    // Run the host task on FreeRTOS
    nimble_port_freertos_init(ble_host_task);
}

void bsp_ble_deinit(void)
{
    int rc = nimble_port_stop();
    if (rc == 0) {
        nimble_port_deinit();
        ESP_LOGI(TAG, "NimBLE deinitialized successfully.");
    } else {
        ESP_LOGE(TAG, "NimBLE stop failed, rc=%d", rc);
    }
}