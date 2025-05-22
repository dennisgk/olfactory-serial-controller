#include "olfactory_serial.h"

blox send_queue = {0};

struct OlTransferCommand recv_comm = {0};

void olfactory_serial_init(){
    send_queue = blox_create(struct OlTransferCommand);
    recv_comm.val_command = OL_COMMAND_NULL;
    recv_comm.val_data = blox_nil();
    recv_comm.data_transferred_amt = 0;

    const uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    };

    uart_param_config(OL_UART_PORT, &uart_config);
    uart_set_pin(OL_UART_PORT, GPIO_NUM_1, GPIO_NUM_3, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(OL_UART_PORT, OL_SERIAL_BUF_SIZE * 2, OL_SERIAL_BUF_SIZE * 2, 0, NULL, 0);
}

blox olfactory_base64(blox data, int (*operation)(uint8_t*, size_t, size_t*, const uint8_t*, size_t)){
    size_t olen = 0;
    operation(NULL, 0, &olen, data.data, data.length);

    blox out = blox_make(uint8_t, olen);

    size_t olen_wr = 0;
    operation(out.data, olen, &olen_wr, data.data, data.length);

    blox_resize(uint8_t, out, olen_wr);

    return out;
}

void olfactory_serial_post(ol_msg_command_t command, blox data){
    struct OlTransferCommand trans = {0};
    trans.data_transferred_amt = 0;
    trans.val_command = command;

    if(data.length > 0){
        trans.val_data = olfactory_base64(data, mbedtls_base64_encode);
    }
    else{
        trans.val_data = blox_nil();
    }

    blox_push(struct OlTransferCommand, send_queue, trans);
}

void olfactory_serial_loop(){
    TickType_t next_comm_wait = 0;

    while (OL_TRUE){
        uint32_t read_amt_loop = 0;

        if(recv_comm.val_command == OL_COMMAND_NULL){
            uart_read_bytes(OL_UART_PORT, &recv_comm.val_command, OL_SERIAL_COMMAND_SIZE, next_comm_wait);
            
            if(recv_comm.val_command != OL_COMMAND_NULL){
                read_amt_loop++;

                uint8_t len_b64[OL_SERIAL_LEN_B64_SIZE] = {0};
                read_amt_loop += uart_read_bytes(OL_UART_PORT, len_b64, OL_SERIAL_LEN_B64_SIZE, portMAX_DELAY);

                blox len_needed_blox = olfactory_base64(blox_use_array(uint8_t, len_b64, OL_SERIAL_LEN_B64_SIZE), mbedtls_base64_decode);
                uint32_t len_needed = *((uint32_t*)len_needed_blox.data);
                blox_free(len_needed_blox);

                recv_comm.val_data = blox_make(uint8_t, len_needed);
            }
        }

        if(recv_comm.val_command != OL_COMMAND_NULL){
            uint32_t read_data_len = uart_read_bytes(OL_UART_PORT, blox_index(uint8_t, recv_comm.val_data, recv_comm.data_transferred_amt), 
                MIN(OL_SERIAL_BUF_SIZE - read_amt_loop, recv_comm.val_data.length - recv_comm.data_transferred_amt), portMAX_DELAY);

            recv_comm.data_transferred_amt += read_data_len;
            read_amt_loop += read_data_len;

            if(recv_comm.data_transferred_amt >= recv_comm.val_data.length){
                blox send_comm_blox = olfactory_base64(recv_comm.val_data, mbedtls_base64_decode);

                switch(recv_comm.val_command){
                    case OL_COMMAND_GET_RELAYS: ol_command_get_relays_handler(send_comm_blox); break;
                    case OL_COMMAND_GET_CSV_ACTIVE: ol_command_get_csv_active_handler(send_comm_blox); break;
                    case OL_COMMAND_GET_CSV_PROG: ol_command_get_csv_prog_handler(send_comm_blox); break;
                    case OL_COMMAND_GET_CSV_CUR_STAT: ol_command_get_csv_cur_stat_handler(send_comm_blox); break;
                    case OL_COMMAND_ALTER: ol_command_alter_handler(send_comm_blox); break;
                    case OL_COMMAND_CSV_START: ol_command_csv_start_handler(send_comm_blox); break;
                    case OL_COMMAND_CSV_STOP: ol_command_csv_stop_handler(send_comm_blox); break;
                    case OL_COMMAND_ECHO: ol_command_echo_handler(send_comm_blox); break;
                    default: break;
                }

                blox_free(send_comm_blox);

                blox_free(recv_comm.val_data);
                recv_comm.val_command = OL_COMMAND_NULL;
                recv_comm.data_transferred_amt = 0;
            }
        }

        next_comm_wait = 0;

        if (send_queue.length > 0){
            #define COMMAND_FIRST (blox_get(struct OlTransferCommand, send_queue, 0))

            if(COMMAND_FIRST.data_transferred_amt == 0){
                uint32_t write_data_len = 0;

                write_data_len += uart_write_bytes(OL_UART_PORT, &COMMAND_FIRST.val_command, OL_SERIAL_COMMAND_SIZE);

                uint32_t send_len = COMMAND_FIRST.val_data.length;
                blox len_b64_resp = olfactory_base64(blox_use_array(uint8_t, &send_len, sizeof(uint32_t)), mbedtls_base64_encode);
                write_data_len += uart_write_bytes(OL_UART_PORT, len_b64_resp.data, len_b64_resp.length);
                blox_free(len_b64_resp);

                if(COMMAND_FIRST.val_data.length > 0){
                    COMMAND_FIRST.data_transferred_amt += uart_write_bytes(OL_UART_PORT, COMMAND_FIRST.val_data.data, 
                        MIN(OL_SERIAL_BUF_SIZE - write_data_len, COMMAND_FIRST.val_data.length - COMMAND_FIRST.data_transferred_amt));
                }

                next_comm_wait = portMAX_DELAY;
            }
            else{
                COMMAND_FIRST.data_transferred_amt += uart_write_bytes(OL_UART_PORT, blox_index(uint8_t, COMMAND_FIRST.val_data, COMMAND_FIRST.data_transferred_amt),
                    MIN(OL_SERIAL_BUF_SIZE, COMMAND_FIRST.val_data.length - COMMAND_FIRST.data_transferred_amt));

                next_comm_wait = portMAX_DELAY;
            }

            if(COMMAND_FIRST.data_transferred_amt >= COMMAND_FIRST.val_data.length){
                blox_free(COMMAND_FIRST.val_data);
                blox_shift(struct OlTransferCommand, send_queue);
            }

            #undef COMMAND_FIRST
        }
        else if (read_amt_loop > 0) {
            ol_msg_command_t to_write = OL_COMMAND_NULL;
            uart_write_bytes(OL_UART_PORT, &to_write, OL_SERIAL_COMMAND_SIZE);
        }
    }
}