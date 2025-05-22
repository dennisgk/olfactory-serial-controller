from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt, QThread
from background_dispatch_worker import ControllerEvent
import threading
import serial_dev
import serial_csv
import serial.tools.list_ports
from window.csv_select_window import CsvSelectIterationsRun, CsvSelectRun

# we will allow private variable access on controller only in this file
# allow private variable access on the windows too

# call controller._quit_if_needed() when ending a thr that may not spawn a window maybe?

def start_program(controller):
    controller._background_loop.set(ControllerEvent(lambda: device_choice_pipeline(controller)))

def device_choice_pipeline(controller):
    ports = serial.tools.list_ports.comports()

    port_vals = []

    for port, desc, hwid in sorted(ports):
        port_vals.append((port, f"{port}: {desc} [{hwid}]"))

    select_window = controller._launch_select("Select your device:")
    for port_val in port_vals:
        item = QListWidgetItem(port_val[1])
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setData(Qt.UserRole, port_val[0])
        select_window.ui.list_widget.addItem(item)

    def on_select():
        if len(select_window.ui.list_widget.selectedItems()) != 1:
            return
        
        port = select_window.ui.list_widget.selectedItems()[0].data(Qt.UserRole)
        serial_dev_load_pipeline(controller, port)
        select_window.close()

    select_window.ui.select_button.clicked.connect(on_select)

def serial_dev_load_pipeline(controller, port):
    loader_window = controller._launch_loader("Connecting to device...")

    def connect():
        try:
            ol = serial_dev.OlfactorySerial(port)
            controller._on_quit = lambda: ol.close()
        except:
            def fail_launch():
                message_window = controller._launch_message("Error - Failed to connect to device.", loader_window)
                message_window.ev_close.connect(lambda: loader_window.close())

            controller._background_loop.set(ControllerEvent(fail_launch))
            return
        
        ol.add_handler(serial_dev.ol_command_echo, lambda text: print(text))

        def on_command_get_relays(relays):
            ol.remove_handler(serial_dev.ol_command_get_relays, on_command_get_relays)

            def on_command_get_csv_active(csv_active):
                ol.remove_handler(serial_dev.ol_command_get_csv_active, on_command_get_csv_active)

                csv_cur_file = serial_csv.CsvProgConv()

                def on_command_get_csv_prog(csv_prog):
                    ol.remove_handler(serial_dev.ol_command_get_csv_prog, on_command_get_csv_prog)

                    csv_cur_file.catch_header(csv_prog)

                    def on_command_get_csv_cur_stat(csv_cur_stat):
                        ol.remove_handler(serial_dev.ol_command_get_csv_cur_stat, on_command_get_csv_cur_stat)

                        csv_cur_file.catch_update(csv_cur_stat)

                        def on_load():
                            serial_dev_main_pipeline(controller, ol, relays, csv_active, csv_cur_file)
                            loader_window.close()
                        
                        controller._background_loop.set(ControllerEvent(on_load))

                    ol.add_handler(serial_dev.ol_command_get_csv_cur_stat, on_command_get_csv_cur_stat)
                    ol.post_command_get_csv_cur_stat()

                ol.add_handler(serial_dev.ol_command_get_csv_prog, on_command_get_csv_prog)
                ol.post_command_get_csv_prog()

            ol.add_handler(serial_dev.ol_command_get_csv_active, on_command_get_csv_active)
            ol.post_command_get_csv_active()

        ol.add_handler(serial_dev.ol_command_get_relays, on_command_get_relays)
        ol.post_command_get_relays()
    
    connect_thr = threading.Thread(target=connect)
    connect_thr.start()

def serial_dev_main_pipeline(controller, ol, relays, csv_active, csv_cur_file):
    main_window = controller._launch_main()

    ol.post_command_echo("Hello World!")

    for i in range(0, serial_dev.ol_num_relay_ports):
        main_window.view.add_relay(i, relays[i])

    main_window.view.set_running_csv(csv_active)

    csv_saved_data = [] if csv_cur_file.is_empty_state() else [csv_cur_file]

    ol.add_handler(serial_dev.ol_command_get_relays, lambda data: controller._background_loop.set(ControllerEvent(lambda: main_window.view.update_relays(data))))
    ol.add_handler(serial_dev.ol_command_get_csv_active, lambda data: controller._background_loop.set(ControllerEvent(lambda: main_window.view.set_running_csv(data))))

    def get_last_or_new_csv_prog_then(after):
        if len(csv_saved_data) == 0 or csv_saved_data[-1].has_caught_csv():
            csv_saved_data.append(serial_csv.CsvProgConv())
        
        after(csv_saved_data[-1])

    ol.add_handler(serial_dev.ol_command_get_csv_prog, lambda data: get_last_or_new_csv_prog_then(lambda csv_prog_conv: csv_prog_conv.catch_header(data)))
    ol.add_handler(serial_dev.ol_command_get_csv_cur_stat, lambda data: csv_saved_data[-1].catch_update(data))

    def enable_relay():
        nums = main_window.view.get_selected_relay_numbers()
        if(len(nums) == 0):
            return
        
        ol.post_command_alter(nums, [])

    def disable_relay():
        nums = main_window.view.get_selected_relay_numbers()
        if(len(nums) == 0):
            return

        ol.post_command_alter([], nums)

    def send_csv(select_args):
        perpetual = False
        num_iterations = 1
        
        if type(select_args) is CsvSelectIterationsRun:
            perpetual = False
            num_iterations = select_args.iterations

        if type(select_args) is CsvSelectRun:
            perpetual = True

        try:
            ol.post_command_csv_start(select_args.file_path, perpetual, num_iterations)
        except:
            import traceback
            traceback.print_exc()

            controller._launch_message("Error - Bad CSV format", main_window)

    def start_csv():
        csv_select_window = controller._launch_csv_select(main_window)
        csv_select_window.view.ev_submit.connect(send_csv)

    def stop_csv():
        ol.post_command_csv_stop()

    def show_csv():
        select_window = controller._launch_select("Select the CSV:")
        for i, csv_prog_conv in enumerate(csv_saved_data):
            item = QListWidgetItem(f"{i+1}: CSV [Last Edited: {csv_prog_conv.get_last_edit().strftime("%Y-%m-%d %H:%M:%S")}]")
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setData(Qt.UserRole, csv_prog_conv)
            select_window.ui.list_widget.addItem(item)

        def on_select():
            if len(select_window.ui.list_widget.selectedItems()) != 1:
                return
            
            csv_prog_conv = select_window.ui.list_widget.selectedItems()[0].data(Qt.UserRole)
            controller._launch_csv_prog(main_window, csv_prog_conv)

            select_window.close()

        select_window.ui.select_button.clicked.connect(on_select)
    
    main_window.ui.enable_button.clicked.connect(enable_relay)
    main_window.ui.disable_button.clicked.connect(disable_relay)

    main_window.ui.start_csv_button.clicked.connect(start_csv)
    main_window.ui.stop_csv_button.clicked.connect(stop_csv)
    main_window.ui.show_csv_button.clicked.connect(show_csv)
    

