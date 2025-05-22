#ifndef __OLFACTORY_PROTOCOL_H__
#define __OLFACTORY_PROTOCOL_H__

#include "driver/uart.h"
#include "driver/gpio.h"
#include "blox.h"
#include "olfactory_common.h"
#include "mbedtls/base64.h"
#include "esp_event.h"
#include "olfactory_loop.h"

#define OL_UART_PORT UART_NUM_0

typedef uint8_t ol_msg_command_t;

#define OL_COMMAND_NULL (ol_msg_command_t)('A')

#define OL_COMMAND_GET_RELAYS (ol_msg_command_t)('B')
#define OL_COMMAND_GET_CSV_ACTIVE (ol_msg_command_t)('C')
#define OL_COMMAND_GET_CSV_PROG (ol_msg_command_t)('D')
#define OL_COMMAND_GET_CSV_CUR_STAT (ol_msg_command_t)('E')

#define OL_COMMAND_ALTER (ol_msg_command_t)('F')
#define OL_COMMAND_CSV_START (ol_msg_command_t)('G')
#define OL_COMMAND_CSV_STOP (ol_msg_command_t)('H')

#define OL_COMMAND_ECHO (ol_msg_command_t)('I')

#define OL_SERIAL_BUF_SIZE (uint32_t)256

#define OL_SERIAL_COMMAND_SIZE (uint32_t)1
#define OL_SERIAL_LEN_B64_SIZE (uint32_t)8

#define OL_SERIAL_COMPENSATED_SIZE(SIZE) (uint32_t)(4 * (((SIZE) + 2) / 3))

struct OlTransferCommand{
    uint32_t data_transferred_amt;
    ol_msg_command_t val_command;
    blox val_data;
};

void olfactory_serial_init();
void olfactory_serial_loop();
void olfactory_serial_post(ol_msg_command_t command, blox data);

#endif