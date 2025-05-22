#ifndef __OLFACTORY_LOOP_H__
#define __OLFACTORY_LOOP_H__

#include "freertos/FreeRTOS.h"
#include "esp_timer.h"
#include "esp_random.h"
#include "driver/gpio.h"
#include "blox.h"
#include "olfactory_common.h"

typedef uint8_t ol_relay_port_t;

#define OL_NUM_RELAY_PORTS (ol_relay_port_t)5

typedef uint8_t ol_relay_state_t;
typedef uint8_t ol_msg_property_t;

#define OL_RELAY_OFF (ol_relay_state_t)0
#define OL_RELAY_ON (ol_relay_state_t)1

#define OL_RELAY_DEACTIVATE (ol_msg_property_t)0
#define OL_RELAY_ACTIVATE (ol_msg_property_t)1
#define OL_RELAY_IGNORE (ol_msg_property_t)2

#define OL_CSV_TIME_NORMAL (ol_msg_property_t)0
#define OL_CSV_TIME_RANDOM (ol_msg_property_t)1

#define OL_CSV_RELAY_OFF (ol_msg_property_t)0
#define OL_CSV_RELAY_ON (ol_msg_property_t)1
#define OL_CSV_RELAY_RANDOM (ol_msg_property_t)2

#define OL_CSV_RUN_NUMBER (ol_msg_property_t)0
#define OL_CSV_RUN_PERPETUAL (ol_msg_property_t)1

struct OlRelayCsvRowRelay
{
    ol_msg_property_t val_adj;
    uint32_t percentage;
};

struct OlRelayCsvRow
{
    blox tag;
    ol_msg_property_t time_adj;
    uint32_t time_val_1;
    uint32_t time_val_2;

    struct OlRelayCsvRowRelay relays[OL_NUM_RELAY_PORTS];
};

struct OlRelayCsvIterationRowChoice
{
    ol_bool_t active;
    int64_t actual_time_millis;
    ol_msg_property_t relay_comms[OL_NUM_RELAY_PORTS];
};

struct OlRelayCsvIterationChoice
{
    blox row_choices;
};

struct OlRelayCsvTable
{
    blox csv_clone;

    blox rows;
    ol_msg_property_t run_adj;
    uint32_t run_num;

    blox choices;
};

struct OlAppState{
    ol_relay_state_t relays[OL_NUM_RELAY_PORTS];

    TaskHandle_t csv_task_spawn_handle;
    struct OlRelayCsvTable csv_table;
};

void olfactory_loop_init();

void ol_command_get_relays_handler(blox event_blox);
void ol_command_get_csv_active_handler(blox event_blox);
void ol_command_get_csv_prog_handler(blox event_blox);
void ol_command_get_csv_cur_stat_handler(blox event_blox);
void ol_command_alter_handler(blox event_blox);
void ol_command_csv_start_handler(blox event_blox);
void ol_command_csv_stop_handler(blox event_blox);
void ol_command_echo_handler(blox event_blox);

#endif