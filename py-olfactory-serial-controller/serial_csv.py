from pydantic import BaseModel
import serial_dev
from datetime import datetime
import csv
import re

tag_header = "TAG"
time_header = "TIME"
relay_header = "R"

time_random_tag = "RANDOM"
relay_random_tag = "RANDOM"
relay_on_tag = "ON"
relay_off_tag = "OFF"

class CsvConvSchemaRowRelay(BaseModel):
    pass

class CsvConvSchemaRandomRowRelay(CsvConvSchemaRowRelay):
    percentage: float

class CsvConvSchemaSetRowRelay(CsvConvSchemaRowRelay):
    val: bool

class CsvConvSchemaRowTime(BaseModel):
    pass

class CsvConvSchemaRandomRowTime(CsvConvSchemaRowTime):
    time_val_1: int
    time_val_2: int

class CsvConvSchemaSetRowTime(CsvConvSchemaRowTime):
    time_val: int

class CsvConvSchemaRow(BaseModel):
    tag: str
    time: CsvConvSchemaRowTime
    relays: list[CsvConvSchemaRowRelay]

class CsvConvSchema:
    def __init__(self, caught_csv):
        self.csv_rows = []

        x = 0

        if caught_csv[0] == serial_dev.ol_csv_run_perpetual:
            self._perpetual = True
            x = x + 1

        if caught_csv[0] == serial_dev.ol_csv_run_number:
            self._perpetual = False
            self._run_num = int.from_bytes(caught_csv[1:5], "little")
            x = x + 5

        while x < len(caught_csv):
            tag_len = int.from_bytes(caught_csv[x:x+4], "little")
            x = x + 4
            tag = caught_csv[x:x+tag_len].decode("ascii")
            x = x + tag_len

            time = None

            time_byte = caught_csv[x]
            x = x + 1

            if time_byte == serial_dev.ol_csv_time_random:
                time_val_1 = int.from_bytes(caught_csv[x:x+4], "little")
                x = x + 4
                time_val_2 = int.from_bytes(caught_csv[x:x+4], "little")
                x = x + 4

                time = CsvConvSchemaRandomRowTime(time_val_1=time_val_1, time_val_2=time_val_2)
            
            if time_byte == serial_dev.ol_csv_time_normal:
                time_val = int.from_bytes(caught_csv[x:x+4], "little")
                x = x + 4

                time = CsvConvSchemaSetRowTime(time_val=time_val)

            relays = []

            for _relay_num in range(0, serial_dev.ol_num_relay_ports):
                relay_byte = caught_csv[x]
                x = x + 1

                if relay_byte == serial_dev.ol_csv_relay_random:
                    relay_perc_int = int.from_bytes(caught_csv[x:x+4], "little")
                    relay_perc = float(relay_perc_int / 1000)
                    x = x + 4

                    relays.append(CsvConvSchemaRandomRowRelay(percentage=relay_perc))

                if relay_byte == serial_dev.ol_relay_on:
                    relays.append(CsvConvSchemaSetRowRelay(val=True))

                if relay_byte == serial_dev.ol_relay_off:
                    relays.append(CsvConvSchemaSetRowRelay(val=False))
            
            self.csv_rows.append(CsvConvSchemaRow(tag=tag, time=time, relays=relays))

class CsvProgConv():
    def __init__(self):
        self._last_edit = datetime.now()
        self._is_empty_state = True

        self._must_catch_csv = 0
        self._must_catch_fillin = 0
        self._caught_csv = bytes([])
        self._caught_fillin = bytes([])
        self._caught_multi = bytes([])

        self._csv_schema = None
        self._csv_fillin = dict()
        self._csv_fillin_millis = dict()

        self._saved_iteration_row_data = []
        self._ev_iteration_handler = []
        self._ev_row_handler = []

    def _emit_ev_row(self, it, row):
        self._saved_iteration_row_data.append((it, row))

        for h in self._ev_row_handler:
            h(it, row)

    def _emit_iteration(self, num):
        for h in self._ev_iteration_handler:
            h(num)

    def add_handlers(self, ev_iteration_handler, ev_row_handler):
        self._ev_iteration_handler.append(ev_iteration_handler)
        self._ev_row_handler.append(ev_row_handler)

    def remove_handlers(self, ev_iteration_handler, ev_row_handler):
        self._ev_iteration_handler.remove(ev_iteration_handler)
        self._ev_row_handler.remove(ev_row_handler)

    def get_saved_iteration_row_data(self):
        return self._saved_iteration_row_data

    def is_empty_state(self):
        return self._is_empty_state

    def has_caught_csv(self):
        return (not self.is_empty_state()) and (len(self._caught_multi) >= self._must_catch_csv + self._must_catch_fillin)

    def get_row_count(self):
        return len(self._csv_schema.csv_rows)

    def catch_header(self, data):
        self._last_edit = datetime.now()
        if len(data) == 0:
            return
        
        self._must_catch_csv = int.from_bytes(data[0:4], "little")
        self._must_catch_fillin = int.from_bytes(data[4:8], "little")

        self._is_empty_state = False
        self._catch_csv(data[8:])

    def _catch_csv(self, data):
        self._last_edit = datetime.now()

        self._caught_multi = self._caught_multi + data
        self._form_csv_schema_if_needed()

    def _form_csv_schema_if_needed(self):
        if self._csv_schema == None and self.has_caught_csv():

            catch_offset = 0

            if len(self._caught_csv) < self._must_catch_csv:
                max_catch = min(self._must_catch_csv - len(self._caught_csv), len(self._caught_multi))

                self._caught_csv = self._caught_csv + self._caught_multi[catch_offset:(catch_offset + max_catch)]
                catch_offset = catch_offset + max_catch

            if len(self._caught_fillin) < self._must_catch_fillin:
                max_catch = min(self._must_catch_fillin - len(self._caught_fillin), len(self._caught_multi) - catch_offset)

                self._caught_fillin = self._caught_fillin + self._caught_multi[catch_offset:(catch_offset + max_catch)]

            self._csv_schema = CsvConvSchema(self._caught_csv)

            last_it = None
            last_row = None
            last_millis = None

            x = 0
            while x < len(self._caught_fillin):
                i = int.from_bytes(self._caught_fillin[x:x+4], "little")
                x = x + 4
                j = int.from_bytes(self._caught_fillin[x:x+4], "little")
                x = x + 4

                time = int.from_bytes(self._caught_fillin[x:x+8], "little")
                x = x + 8

                relays = [self._caught_fillin[x+y] == serial_dev.ol_relay_activate for y in range(0, serial_dev.ol_num_relay_ports)]
                x = x + serial_dev.ol_num_relay_ports

                self._catch_update_deob(i, j, relays, last_it, last_row, last_millis)

                last_it = i
                last_row = j
                last_millis = time

            self._catch_update_deob(None, None, None, last_it, last_row, last_millis)

    def get_last_edit(self):
        return self._last_edit
    
    def get_headers(self):
        return [tag_header, f"EXPECTED {time_header}", f"ACTUAL {time_header}"] + [f"{relay_header}{x+1}" for x in range(0, serial_dev.ol_num_relay_ports)] + ["R CONFIG"]
    
    def get_row(self, it, row):

        time_text = ""
        if type(self._csv_schema.csv_rows[row].time) is CsvConvSchemaSetRowTime:
            time_text = f"{self._csv_schema.csv_rows[row].time.time_val}MS"
        
        if type(self._csv_schema.csv_rows[row].time) is CsvConvSchemaRandomRowTime:
            time_text = f"{time_random_tag} {self._csv_schema.csv_rows[row].time.time_val_1}MS {self._csv_schema.csv_rows[row].time.time_val_2}MS"

        act_time = ""
        if it in self._csv_fillin_millis and row in self._csv_fillin_millis.get(it).keys():
            act_time = f"{self._csv_fillin_millis.get(it).get(row)}MS"
        
        relay_arr = []
        relay_changes = []

        for x in range(0, serial_dev.ol_num_relay_ports):
            if type(self._csv_schema.csv_rows[row].relays[x]) is CsvConvSchemaRandomRowRelay:
                relay_arr.append(f"{relay_random_tag} {self._csv_schema.csv_rows[row].relays[x].percentage:.3f}%")
                relay_changes.append(f"R{x+1}={relay_on_tag if self._csv_fillin.get(it).get(row)[x] else relay_off_tag}")

            if type(self._csv_schema.csv_rows[row].relays[x]) is CsvConvSchemaSetRowRelay:
                relay_arr.append(relay_on_tag if self._csv_schema.csv_rows[row].relays[x].val else relay_off_tag)

        return [self._csv_schema.csv_rows[row].tag, time_text, act_time] + relay_arr + [",".join(relay_changes)]

    def _catch_update_deob(self, current_it, current_row, current_ports, last_it, last_row, last_millis):

        if current_it != None and current_row != None and current_ports != None:
            if current_it not in self._csv_fillin.keys():
                if current_it not in self._csv_fillin_millis.keys():
                    self._emit_iteration(current_it)
                self._csv_fillin.update(dict([(current_it, dict())]))
            self._csv_fillin.get(current_it).update(dict([(current_row, current_ports)]))
            self._emit_ev_row(current_it, current_row)

        if last_it != None and last_row != None and last_millis != None:
            if last_it not in self._csv_fillin_millis.keys():
                if last_it not in self._csv_fillin.keys():
                    self._emit_iteration(last_it)
                self._csv_fillin_millis.update(dict([(last_it, dict())]))
            self._csv_fillin_millis.get(last_it).update(dict([(last_row, last_millis)]))
            self._emit_ev_row(last_it, last_row)

    def catch_update(self, data):
        self._last_edit = datetime.now()
        if len(data) == 0:
            return
        
        first_out_len = int.from_bytes(data[-8:-4], "little")
        sec_out_len = int.from_bytes(data[-4:], "little")

        catch_args = [
            None if first_out_len == 0 else int.from_bytes(data[0:4], "little"),
            None if first_out_len == 0 else int.from_bytes(data[4:8], "little"),
            None if first_out_len == 0 else [data[8+y] == serial_dev.ol_relay_activate for y in range(0, serial_dev.ol_num_relay_ports)],
            None if sec_out_len == 0 else int.from_bytes(data[first_out_len:4+first_out_len], "little"),
            None if sec_out_len == 0 else int.from_bytes(data[4+first_out_len:8+first_out_len], "little"),
            None if sec_out_len == 0 else int.from_bytes(data[8+first_out_len:16+first_out_len], "little"),
        ]

        self._catch_update_deob(*catch_args)

def parse_csv_time_ms(time_str):
    time_val_re = re.findall(r"(\d*\.?\d*)(MS|S)", time_str)[0]
    time_val = float(time_val_re[0])

    if time_val_re[1] == "MS":
        pass
    elif time_val_re[1] == "S":
        time_val = time_val * 1000
    else:
        raise ValueError("Error - Bad csv time")
    
    return int(round(time_val))

def combine_added_bytes(added):
    return bytes(len(added).to_bytes(4, "little")) + added

def gen_command_start_csv(file_path, perpetual, num_runs):
    all_out_bytes = bytes([])

    if perpetual:
        all_out_bytes = all_out_bytes + bytes([serial_dev.ol_csv_run_perpetual])
    else:
        all_out_bytes = all_out_bytes + bytes([serial_dev.ol_csv_run_number]) + num_runs.to_bytes(4, "little")

    num_rows = 0

    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        if reader.fieldnames != [tag_header, time_header] + [f"{relay_header}{x}" for x in range(1, serial_dev.ol_num_relay_ports + 1)]:
            raise ValueError("Error - Invalid headers")
        
        for row in reader:
            num_rows = num_rows + 1

            tag_ascii = row[tag_header].encode("ascii")
            all_out_bytes = all_out_bytes + combine_added_bytes(tag_ascii)

            time_words = re.split(r"\s+", row["TIME"])
            if time_words[0] == time_random_tag:
                time_val_1 = parse_csv_time_ms(time_words[1])
                time_val_2 = parse_csv_time_ms(time_words[2])

                if time_val_1 > time_val_2:
                    temp = time_val_1
                    time_val_1 = time_val_2
                    time_val_2 = temp

                if time_val_1 == time_val_2:
                    time_val_2 = time_val_2 + 1

                time_bytes = bytes([serial_dev.ol_csv_time_random]) + time_val_1.to_bytes(4, "little") + time_val_2.to_bytes(4, "little");
            else:
                time_val = parse_csv_time_ms(time_words[0])
                time_bytes = bytes([serial_dev.ol_csv_time_normal]) + time_val.to_bytes(4, "little")
            
            all_out_bytes = all_out_bytes + time_bytes

            for x in range(1, serial_dev.ol_num_relay_ports + 1):
                relay_words = re.split(r"\s+", row[f"{relay_header}{x}"])

                if relay_words[0] == relay_random_tag:
                    relay_val = int(round(float(re.findall(r"(\d*\.?\d*)%", relay_words[1])[0]) * 1000))
                    relay_bytes = bytes([serial_dev.ol_csv_relay_random]) + relay_val.to_bytes(4, "little")
                elif relay_words[0] == relay_on_tag:
                    relay_bytes = bytes([serial_dev.ol_csv_relay_on])
                elif relay_words[0] == relay_off_tag:
                    relay_bytes = bytes([serial_dev.ol_csv_relay_off])

                all_out_bytes = all_out_bytes + relay_bytes

    if num_rows == 0:
        raise ValueError("Error - No rows")

    return all_out_bytes