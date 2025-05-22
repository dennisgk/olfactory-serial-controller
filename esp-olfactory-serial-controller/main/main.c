#include "nvs_flash.h"

#include "olfactory_serial.h"
#include "olfactory_loop.h"

void app_main(void)
{
    nvs_flash_init();
    
    olfactory_serial_init();
    olfactory_loop_init();

    olfactory_serial_loop();
}
