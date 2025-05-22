import serial
import time
import threading
import base64
from pydantic import BaseModel
from serial_csv import gen_command_start_csv

ol_command_null = bytes("A", encoding="ascii")[0]

ol_command_get_relays = bytes("B", encoding="ascii")[0]
ol_command_get_csv_active = bytes("C", encoding="ascii")[0]
ol_command_get_csv_prog = bytes("D", encoding="ascii")[0]
ol_command_get_csv_cur_stat = bytes("E", encoding="ascii")[0]

ol_command_alter = bytes("F", encoding="ascii")[0]
ol_command_csv_start = bytes("G", encoding="ascii")[0]
ol_command_csv_stop = bytes("H", encoding="ascii")[0]

ol_command_echo = bytes("I", encoding="ascii")[0]

ol_serial_buf_size = 256
ol_serial_command_size = 1
ol_serial_len_b64_size = 8

ol_num_relay_ports = 5

ol_relay_off = 0
ol_relay_on = 1

ol_relay_deactivate = 0
ol_relay_activate = 1
ol_relay_ignore = 2

ol_csv_time_normal = 0
ol_csv_time_random = 1

ol_csv_relay_off = 0
ol_csv_relay_on = 1
ol_csv_relay_random = 2

ol_csv_run_number = 0
ol_csv_run_perpetual = 1

ol_false = 0
ol_true = 1

class OlTransferCommand(BaseModel):
    data_transferred_amt: int
    val_command: int
    val_data: bytes

class OlfactorySerial:
    def __init__(self, port):
        initial_timeout = 2

        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=initial_timeout,
            rtscts=False,
            dsrdtr=False
        )

        """
        def_read = self.ser.read
        def new_read(clen):
            out = def_read(clen)
            if len(out) > 0:
                print("Read", out)
            return out
        self.ser.read = new_read

        def_write = self.ser.write
        def new_write(arr):
            out = def_write(arr)
            print("Wrote", arr)
            return out
        self.ser.write = new_write
        """

        time.sleep(initial_timeout)

        self._handlers = dict([(x, []) for x in [ol_command_get_relays, 
                                                 ol_command_get_csv_active,
                                                 ol_command_get_csv_prog,
                                                 ol_command_get_csv_cur_stat,
                                                 ol_command_alter,
                                                 ol_command_csv_start,
                                                 ol_command_csv_stop,
                                                 ol_command_echo]])

        self._clear_recv_comm()
        self._send_queue = []

        self._clear_ser_init()
        self._thr_ser_init()

    def _clear_ser_init(self):
        clear_read_len = 512
        
        resp = self.ser.read(clear_read_len)
        while len(resp) > 0:
            resp = self.ser.read(clear_read_len)

        self._reset_ser_timeout()

    def _clear_recv_comm(self):
        self._recv_comm = OlTransferCommand(data_transferred_amt=0, val_command=ol_command_null, val_data=bytes([]))
        self._recv_comm_len_needed = 0

    def _set_ser_timeout_indefinite(self):
        self.ser.timeout = None

    def _reset_ser_timeout(self):
        self.ser.timeout = 0

    def _thr_loop(self):
        next_comm_wait = self._reset_ser_timeout

        while self._is_looping:
            read_amt_loop = 0

            if self._recv_comm.val_command == ol_command_null:
                next_comm_wait()
                read_bytes_val = self.ser.read(ol_serial_command_size)
                self._reset_ser_timeout()

                if len(read_bytes_val) == ol_serial_command_size:
                    self._recv_comm.val_command = read_bytes_val[0]

                if self._recv_comm.val_command != ol_command_null:
                    read_amt_loop = read_amt_loop + 1

                    self._set_ser_timeout_indefinite()
                    len_b64 = self.ser.read(ol_serial_len_b64_size)
                    self._reset_ser_timeout()
                    read_amt_loop += ol_serial_len_b64_size

                    self._recv_comm_len_needed = int.from_bytes(base64.b64decode(len_b64), "little")

            if self._recv_comm.val_command != ol_command_null:
                self._set_ser_timeout_indefinite()
                read_bytes_val = self.ser.read(min(ol_serial_buf_size - read_amt_loop, self._recv_comm_len_needed - self._recv_comm.data_transferred_amt))
                self._reset_ser_timeout()
                self._recv_comm.val_data = self._recv_comm.val_data + read_bytes_val

                self._recv_comm.data_transferred_amt = (
                    self._recv_comm.data_transferred_amt + len(read_bytes_val)
                )
                read_amt_loop = read_amt_loop + len(read_bytes_val)

                if self._recv_comm.data_transferred_amt >= self._recv_comm_len_needed:
                    send_comm_blox = base64.b64decode(self._recv_comm.val_data)

                    self._call_handler(self._recv_comm.val_command, send_comm_blox)

                    self._clear_recv_comm()

            next_comm_wait = self._reset_ser_timeout
            
            if len(self._send_queue) > 0:
                if self._send_queue[0].data_transferred_amt == 0:
                    write_data_len = 0

                    self.ser.write(bytes([self._send_queue[0].val_command]))
                    write_data_len = write_data_len + ol_serial_command_size

                    len_b64_resp = base64.b64encode(len(self._send_queue[0].val_data).to_bytes(4, "little"))
                    self.ser.write(len_b64_resp)
                    write_data_len = write_data_len + ol_serial_len_b64_size

                    if len(self._send_queue[0].val_data) > 0:
                        send_bytes_view = self._send_queue[0].val_data[0:(min(ol_serial_buf_size - write_data_len, len(self._send_queue[0].val_data) - self._send_queue[0].data_transferred_amt))]
                        self._send_queue[0].data_transferred_amt = self._send_queue[0].data_transferred_amt + self.ser.write(send_bytes_view)

                        next_comm_wait = self._set_ser_timeout_indefinite
                else:
                    send_bytes_view = self._send_queue[0].val_data[self._send_queue[0].data_transferred_amt:(self._send_queue[0].data_transferred_amt + min(ol_serial_buf_size, len(self._send_queue[0].val_data) - self._send_queue[0].data_transferred_amt))]
                    self._send_queue[0].data_transferred_amt = self._send_queue[0].data_transferred_amt + self.ser.write(send_bytes_view)

                    next_comm_wait = self._set_ser_timeout_indefinite

                if self._send_queue[0].data_transferred_amt >= len(self._send_queue[0].val_data):
                    self._send_queue.pop(0)
            elif read_amt_loop > 0:
                self.ser.write([ol_command_null])

    def _get_handler_lambda(self, command, blox, handler):
        if command == ol_command_get_relays:
            return lambda: handler([blox[x] == ol_relay_on for x in range(0, ol_num_relay_ports)])

        if command == ol_command_get_csv_active:
            return lambda: handler(blox[0] == ol_true)

        if command == ol_command_get_csv_prog:
            return lambda: handler(blox)

        if command == ol_command_get_csv_cur_stat:
            return lambda: handler(blox)

        if command == ol_command_alter:
            return handler

        if command == ol_command_csv_start:
            return handler

        if command == ol_command_csv_stop:
            return handler

        if command == ol_command_echo:
            return lambda: handler(blox.decode("ascii"))

    def _call_handler(self, command, blox):
        for handler in self._handlers[command]:
            self._get_handler_lambda(command, blox, handler)()

    def post_command_get_relays(self):
        self._post(ol_command_get_relays, bytes([]))

    def post_command_get_csv_active(self):
        self._post(ol_command_get_csv_active, bytes([]))

    def post_command_get_csv_prog(self):
        self._post(ol_command_get_csv_prog, bytes([]))

    def post_command_get_csv_cur_stat(self):
        self._post(ol_command_get_csv_cur_stat, bytes([]))

    def post_command_alter(self, activated, deactivated):
        self._post(ol_command_alter, bytes([ol_relay_activate if x in activated 
                                            else ol_relay_deactivate if x in deactivated
                                             else ol_relay_ignore for x in range(0, ol_num_relay_ports)]))

    def post_command_csv_start(self, file_path, perpetual, num_iterations):
        self._post(ol_command_csv_start, gen_command_start_csv(file_path, perpetual, num_iterations))

    def post_command_csv_stop(self):
        self._post(ol_command_csv_stop, bytes([]))

    def post_command_echo(self, text):
        self._post(ol_command_echo, int.from_bytes(text, "little") if len(text) == 4 else text.encode("ascii"))

    def _post(self, command, blox):
        byte_arr = bytes([])

        if len(blox) > 0:
            byte_arr = base64.b64encode(blox)

        self._send_queue.append(OlTransferCommand(data_transferred_amt=0, val_command=command, val_data=byte_arr))

    def add_handler(self, command, handler):
        self._handlers[command].append(handler)

    def remove_handler(self, command, handler):
        self._handlers[command].remove(handler)

    def _thr_ser_init(self):
        self._is_looping = True
        self._loop = threading.Thread(target=self._thr_loop)
        self._loop.start()

    def close(self):
        self._is_looping = False
        self._loop.join()
        self.ser.close()