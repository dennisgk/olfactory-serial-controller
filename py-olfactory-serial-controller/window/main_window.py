from . import Window
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt
import serial_dev

class MainWindowView(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self._csv_active = serial_dev.ol_csv_active_stopped

        self.window.ui.running_csv_checkbox.stateChanged.connect(lambda: self.window.ui.running_csv_checkbox.setCheckState(self._get_csv_checkbox_state()))

    def set_running_csv(self, val):
        self._csv_active = val
        self.window.ui.start_csv_button.setEnabled(self._csv_active == serial_dev.ol_csv_active_stopped)
        self.window.ui.pause_csv_button.setText("Resume" if self._csv_active == serial_dev.ol_csv_active_paused else "Pause")
        self.window.ui.pause_csv_button.setEnabled(self._csv_active != serial_dev.ol_csv_active_stopped)
        self.window.ui.stop_csv_button.setEnabled(self._csv_active != serial_dev.ol_csv_active_stopped)
        self.window.ui.running_csv_checkbox.setCheckState(self._get_csv_checkbox_state())
        
    def _get_csv_checkbox_state(self):
        return (
            Qt.Checked if self._csv_active == serial_dev.ol_csv_active_started 
            else Qt.PartiallyChecked if self._csv_active == serial_dev.ol_csv_active_paused 
            else Qt.Unchecked
        )

    def add_relay(self, num, val):
        item = QListWidgetItem(f"Relay {num+1}")
        item.setCheckState(Qt.Checked if val else Qt.Unchecked)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setData(Qt.UserRole, num)
        self.window.ui.relays_list.addItem(item)

    def update_relays(self, vals):
        for item in [self.window.ui.relays_list.item(x) for x in range(0, self.window.ui.relays_list.count())]:
            item.setCheckState(Qt.Checked if vals[item.data(Qt.UserRole)] else Qt.Unchecked)

    def get_selected_relay_numbers(self):
        ret = []

        for x in self.window.ui.relays_list.selectedItems():
            ret.append(x.data(Qt.UserRole))

        return ret

class MainWindow(Window):
    def __init__(self, inst_class, parent=None):
        super().__init__(inst_class, parent)
        self.view = MainWindowView(self)