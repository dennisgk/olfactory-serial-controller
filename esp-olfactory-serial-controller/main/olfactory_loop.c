#include "olfactory_loop.h"
#include "olfactory_serial.h"
#include "blox.h"

gpio_num_t ol_relay_port_nums[OL_NUM_RELAY_PORTS] = {GPIO_NUM_32, GPIO_NUM_33, GPIO_NUM_25, GPIO_NUM_26, GPIO_NUM_27};
struct OlAppState ol_app_state = {0};

void ol_csv_run_task(void *pv)
{
    ol_app_state.csv_active = OL_CSV_ACTIVE_STARTED;

    uint32_t num_runs_taken = 0;

    ol_bool_t is_running = OL_TRUE;

    ol_command_get_csv_active_handler(blox_nil());

    ol_app_state.csv_table.choices = blox_create(struct OlRelayCsvIterationChoice);

    ol_command_get_csv_prog_handler(blox_nil());

    while (is_running == OL_TRUE)
    {
        blox_stuff(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices);
        blox_back(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices).row_choices = blox_create(struct OlRelayCsvIterationRowChoice);

        for (size_t i = 0; i < ol_app_state.csv_table.rows.length; i++)
        {
            blox_stuff(struct OlRelayCsvIterationRowChoice, blox_back(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices).row_choices);

#define LATEST_ROW blox_back(struct OlRelayCsvIterationRowChoice, blox_back(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices).row_choices)

            LATEST_ROW.active = OL_TRUE;
            LATEST_ROW.actual_time_millis =
                esp_timer_get_time() / (int64_t)1000;

            struct OlRelayCsvRow row = blox_get(struct OlRelayCsvRow, ol_app_state.csv_table.rows, i);

            for (ol_relay_port_t z = 0; z < OL_NUM_RELAY_PORTS; z++)
            {
                if (row.relays[z].val_adj == OL_CSV_RELAY_ON)
                {
                    LATEST_ROW.relay_comms[z] = OL_RELAY_ACTIVATE;
                }
                if (row.relays[z].val_adj == OL_CSV_RELAY_OFF)
                {
                    LATEST_ROW.relay_comms[z] = OL_RELAY_DEACTIVATE;
                }
                if (row.relays[z].val_adj == OL_CSV_RELAY_RANDOM)
                {
                    uint32_t range_random = (100 * 1000) + 1;
                    uint32_t rand_val = (((uint32_t)esp_random()) & range_random);

                    if (rand_val <= row.relays[z].percentage)
                    {
                        LATEST_ROW.relay_comms[z] = OL_RELAY_ACTIVATE;
                    }
                    else
                    {
                        LATEST_ROW.relay_comms[z] = OL_RELAY_DEACTIVATE;
                    }
                }
            }

            ol_command_get_csv_cur_stat_handler(blox_nil());
            ol_command_alter_handler(blox_use_array(uint8_t, LATEST_ROW.relay_comms, sizeof(ol_msg_property_t) * OL_NUM_RELAY_PORTS));

            uint32_t ticks_to_wait = row.time_val_1;

            if (row.time_adj == OL_CSV_TIME_RANDOM)
            {
                uint32_t range = row.time_val_2 - row.time_val_1 + 1;
                ticks_to_wait = (((uint32_t)esp_random()) % range) + row.time_val_1;
            }

#define FINISH_UP_IT              \
    LATEST_ROW.active = OL_FALSE; \
    LATEST_ROW.actual_time_millis = (esp_timer_get_time() / (int64_t)1000) - LATEST_ROW.actual_time_millis;

            ol_task_event_t notified;
            if (xTaskNotifyWait(0, 0, &notified, pdMS_TO_TICKS(ticks_to_wait)) == pdTRUE)
            {
                if (notified == OL_TASK_EVENT_PAUSE)
                {
                    ol_app_state.csv_active = OL_CSV_ACTIVE_PAUSED;
                    ol_command_get_csv_active_handler(blox_nil());

                    xTaskNotifyWait(0, 0, &notified, portMAX_DELAY);
                    if (notified == OL_TASK_EVENT_PAUSE)
                    {
                        ol_app_state.csv_active = OL_CSV_ACTIVE_STARTED;
                        ol_command_get_csv_active_handler(blox_nil());
                        FINISH_UP_IT;
                        continue;
                    }
                }

                if (notified == OL_TASK_EVENT_STOP)
                {
                    is_running = OL_FALSE;
                    FINISH_UP_IT;
                    break;
                }
            }

            FINISH_UP_IT;

#undef FINISH_UP_IT
#undef LATEST_ROW
        }

        num_runs_taken++;

        if (ol_app_state.csv_table.run_adj == OL_CSV_RUN_NUMBER && num_runs_taken >= ol_app_state.csv_table.run_num)
        {
            is_running = OL_FALSE;
            break;
        }
    }

    ol_command_get_csv_cur_stat_handler(blox_nil());

    for (size_t i = 0; i < ol_app_state.csv_table.rows.length; i++)
    {
        blox_free(blox_get(struct OlRelayCsvRow, ol_app_state.csv_table.rows, i).tag);
    }

    for (size_t i = 0; i < ol_app_state.csv_table.choices.length; i++)
    {
        blox_free(blox_get(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices, i).row_choices);
    }

    blox_free(ol_app_state.csv_table.rows);
    blox_free(ol_app_state.csv_table.choices);
    blox_free(ol_app_state.csv_table.csv_clone);

    ol_app_state.csv_task_spawn_handle = NULL;

    ol_app_state.csv_active = OL_CSV_ACTIVE_STOPPED;
    ol_command_get_csv_active_handler(blox_nil());

    vTaskDelete(NULL);
}

void ol_command_get_relays_handler(blox event_blox)
{
    olfactory_serial_post(OL_COMMAND_GET_RELAYS, blox_use_array(uint8_t, ol_app_state.relays, sizeof(ol_msg_property_t) * OL_NUM_RELAY_PORTS));
}

void ol_command_get_csv_active_handler(blox event_blox)
{
    olfactory_serial_post(OL_COMMAND_GET_CSV_ACTIVE, blox_use_array(uint8_t, &ol_app_state.csv_active, sizeof(ol_csv_active_state_t)));
}

void ol_command_get_csv_prog_handler(blox event_blox)
{
    if (ol_app_state.csv_active == OL_CSV_ACTIVE_STOPPED)
    {
        olfactory_serial_post(OL_COMMAND_GET_CSV_PROG, blox_nil());
        return;
    }

    blox resp_data = blox_make(uint8_t, 2 * sizeof(uint32_t));

    *((uint32_t *)resp_data.data) = ol_app_state.csv_table.csv_clone.length;
    blox_append(uint8_t, resp_data, ol_app_state.csv_table.csv_clone);

    for (size_t i = 0; i < ol_app_state.csv_table.choices.length; i++)
    {
        for (size_t j = 0; j < blox_get(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices, i).row_choices.length; j++)
        {
            struct OlRelayCsvIterationRowChoice choice = blox_get(struct OlRelayCsvIterationRowChoice, blox_get(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices, i).row_choices, j);

            if (choice.active == OL_TRUE)
            {
                continue;
            }

            blox_append_array(uint8_t, resp_data, &i, sizeof(uint32_t));
            blox_append_array(uint8_t, resp_data, &j, sizeof(uint32_t));

            blox_append_array(uint8_t, resp_data, &choice.actual_time_millis, sizeof(int64_t));
            blox_append_array(uint8_t, resp_data, choice.relay_comms, sizeof(ol_msg_property_t) * OL_NUM_RELAY_PORTS);
        }
    }

    uint32_t cur_len = resp_data.length - sizeof(uint32_t) - sizeof(uint32_t) - ol_app_state.csv_table.csv_clone.length;
    *((uint32_t *)(blox_index(uint8_t, resp_data, sizeof(uint32_t)))) = cur_len;

    olfactory_serial_post(OL_COMMAND_GET_CSV_PROG, resp_data);

    blox_free(resp_data);
}

void ol_command_get_csv_cur_stat_handler(blox event_blox)
{
    if (ol_app_state.csv_active == OL_CSV_ACTIVE_STOPPED)
    {
        olfactory_serial_post(OL_COMMAND_GET_CSV_CUR_STAT, blox_nil());
        return;
    }

    uint32_t last_it = 0;
    uint32_t last_row = 0;

    uint32_t now_it = ol_app_state.csv_table.choices.length - 1;
    uint32_t now_row = blox_back(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices).row_choices.length - 1;

    if (now_row > 0)
    {
        last_it = now_it;
        last_row = now_row - 1;
    }
    else if (now_row == 0 && now_it == 0)
    {
        last_it = now_it;
        last_row = now_row;
    }
    else
    {
        last_it = now_it - 1;
        last_row = blox_get(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices, ol_app_state.csv_table.choices.length - 2).row_choices.length - 1;
    }

    blox resp_data = blox_create(uint8_t);
    blox_append_array(uint8_t, resp_data, &now_it, sizeof(uint32_t));
    blox_append_array(uint8_t, resp_data, &now_row, sizeof(uint32_t));

    struct OlRelayCsvIterationRowChoice choice = blox_get(struct OlRelayCsvIterationRowChoice, blox_get(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices, now_it).row_choices, now_row);

    ol_bool_t is_last_two_done = choice.active == OL_FALSE;

    if (is_last_two_done == OL_FALSE)
    {
        blox_append_array(uint8_t, resp_data, choice.relay_comms, sizeof(ol_msg_property_t) * OL_NUM_RELAY_PORTS);
    }
    else
    {
        blox_append_array(uint8_t, resp_data, &choice.actual_time_millis, sizeof(int64_t));
    }

    if (is_last_two_done == OL_FALSE && (last_it != now_it || last_row != now_row))
    {
        choice = blox_get(struct OlRelayCsvIterationRowChoice, blox_get(struct OlRelayCsvIterationChoice, ol_app_state.csv_table.choices, last_it).row_choices, last_row);
        blox_append_array(uint8_t, resp_data, &last_it, sizeof(uint32_t));
        blox_append_array(uint8_t, resp_data, &last_row, sizeof(uint32_t));

        blox_append_array(uint8_t, resp_data, &choice.actual_time_millis, sizeof(int64_t));
    }

    olfactory_serial_post(OL_COMMAND_GET_CSV_CUR_STAT, resp_data);

    blox_free(resp_data);
}

void ol_command_alter_handler(blox event_blox)
{
    if (event_blox.length != sizeof(ol_msg_property_t) * OL_NUM_RELAY_PORTS)
    {
        return;
    }

    ol_msg_property_t *relay_comms = (ol_msg_property_t *)event_blox.data;
    for (ol_relay_port_t i = 0; i < OL_NUM_RELAY_PORTS; i++)
    {
        if ((relay_comms[i] == OL_RELAY_IGNORE) || (ol_app_state.relays[i] == OL_RELAY_ON && relay_comms[i] == OL_RELAY_ACTIVATE) || (ol_app_state.relays[i] == OL_RELAY_OFF && relay_comms[i] == OL_RELAY_DEACTIVATE))
            continue;

        if (relay_comms[i] == OL_RELAY_ACTIVATE)
        {
            gpio_set_level(ol_relay_port_nums[i], 1);
            ol_app_state.relays[i] = OL_RELAY_ON;
        }

        if (relay_comms[i] == OL_RELAY_DEACTIVATE)
        {
            gpio_set_level(ol_relay_port_nums[i], 0);
            ol_app_state.relays[i] = OL_RELAY_OFF;
        }
    }

    ol_command_get_relays_handler(blox_nil());
}

void ol_command_csv_start_handler(blox event_blox)
{
    if (ol_app_state.csv_active != OL_CSV_ACTIVE_STOPPED)
    {
        return;
    }

    if (event_blox.length == 0)
    {
        return;
    }

    ol_app_state.csv_table.rows = blox_create(struct OlRelayCsvRow);

    uint32_t cursor = 0;

    ol_app_state.csv_table.run_adj = *((ol_msg_property_t *)(blox_index(uint8_t, event_blox, cursor)));
    cursor += sizeof(ol_msg_property_t);

    if (ol_app_state.csv_table.run_adj == OL_CSV_RUN_NUMBER)
    {
        ol_app_state.csv_table.run_num = *((uint32_t *)(blox_index(uint8_t, event_blox, cursor)));
        cursor += sizeof(uint32_t);
    }

    while (cursor < event_blox.length)
    {
        struct OlRelayCsvRow row = {0};

        uint32_t tag_size = *((uint32_t *)(blox_index(uint8_t, event_blox, cursor)));
        cursor += sizeof(uint32_t);

        row.tag = blox_create(char);
        blox_append_array(char, row.tag, (char *)(blox_index(uint8_t, event_blox, cursor)), tag_size);
        cursor += tag_size;

        row.time_adj = *((ol_msg_property_t *)(blox_index(uint8_t, event_blox, cursor)));
        cursor += sizeof(ol_msg_property_t);

        if (row.time_adj == OL_CSV_TIME_NORMAL)
        {
            row.time_val_1 = *((uint32_t *)(blox_index(uint8_t, event_blox, cursor)));
            cursor += sizeof(uint32_t);
        }
        if (row.time_adj == OL_CSV_TIME_RANDOM)
        {
            row.time_val_1 = *((uint32_t *)(blox_index(uint8_t, event_blox, cursor)));
            cursor += sizeof(uint32_t);
            row.time_val_2 = *((uint32_t *)(blox_index(uint8_t, event_blox, cursor)));
            cursor += sizeof(uint32_t);
        }

        for (ol_relay_port_t i = 0; i < OL_NUM_RELAY_PORTS; i++)
        {
            row.relays[i].val_adj = *((ol_msg_property_t *)(blox_index(uint8_t, event_blox, cursor)));
            cursor += sizeof(ol_msg_property_t);

            if (row.relays[i].val_adj == OL_CSV_RELAY_RANDOM)
            {
                row.relays[i].percentage = *((uint32_t *)(blox_index(uint8_t, event_blox, cursor)));
                cursor += sizeof(uint32_t);
            }
        }

        blox_push(struct OlRelayCsvRow, ol_app_state.csv_table.rows, row);
    }

    ol_app_state.csv_table.csv_clone = blox_clone(uint8_t, event_blox);

    xTaskCreate(ol_csv_run_task, STRINGIFY(ol_csv_run_task), 4096, NULL, tskIDLE_PRIORITY + 5, &ol_app_state.csv_task_spawn_handle);
}

void ol_command_csv_pause_handler(blox event_blox)
{
    if (ol_app_state.csv_active == OL_CSV_ACTIVE_STOPPED)
    {
        return;
    }

    xTaskNotify(ol_app_state.csv_task_spawn_handle, OL_TASK_EVENT_PAUSE, eSetValueWithOverwrite);
}

void ol_command_csv_stop_handler(blox event_blox)
{
    if (ol_app_state.csv_active == OL_CSV_ACTIVE_STOPPED)
    {
        return;
    }

    xTaskNotify(ol_app_state.csv_task_spawn_handle, OL_TASK_EVENT_STOP, eSetValueWithOverwrite);
}

void ol_command_echo_handler(blox event_blox)
{
    olfactory_serial_post(OL_COMMAND_ECHO, event_blox);
}

void olfactory_loop_init()
{
    ol_app_state.csv_task_spawn_handle = NULL;
    ol_app_state.csv_active = OL_CSV_ACTIVE_STOPPED;
    ol_app_state.csv_table.rows = blox_nil();
    ol_app_state.csv_table.run_adj = OL_CSV_RUN_NUMBER;
    ol_app_state.csv_table.run_num = 0;
    ol_app_state.csv_table.choices = blox_nil();
    ol_app_state.csv_table.csv_clone = blox_nil();

    for (ol_relay_port_t i = 0; i < OL_NUM_RELAY_PORTS; i++)
    {
        ol_app_state.relays[i] = OL_RELAY_OFF;
        gpio_set_direction(ol_relay_port_nums[i], GPIO_MODE_OUTPUT);
        gpio_set_level(ol_relay_port_nums[i], 0);
    }
}
