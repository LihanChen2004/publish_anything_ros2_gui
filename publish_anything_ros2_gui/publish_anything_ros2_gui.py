# Copyright 2025 Lihan Chen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib
import os
import sys
from typing import Any, Dict

import rclpy
import rclpy.logging
import yaml
from PyQt5.QtCore import QFile, QTextStream, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from rclpy.node import Node


class ROSPublisherGUI(QMainWindow):
    def __init__(self, config_path: str):
        super().__init__()
        self.config = self.load_config(config_path)
        self.ros_node = Node("qt_ros_publisher")
        self.init_ui()
        self.load_style_sheet()

    def load_config(self, path: str) -> Dict[str, Any]:
        with open(path) as f:
            return yaml.safe_load(f)

    def init_ui(self):
        self.setWindowTitle("Publish Anything ROS2 GUI")
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        for topic_name, topic_config in self.config.items():
            tab = QWidget()
            self.tabs.addTab(tab, topic_name)
            layout = QVBoxLayout()
            publisher_widget = PublisherWidget(topic_config, self.ros_node)
            layout.addWidget(publisher_widget)
            tab.setLayout(layout)
        self.setCentralWidget(self.tabs)
        self.resize(1000, 1800)

    def load_style_sheet(self):
        style_file = QFile(
            os.path.join(os.path.dirname(__file__), "../config/qt_style.qss")
        )
        if style_file.open(QFile.ReadOnly | QFile.Text):
            style_sheet = QTextStream(style_file).readAll()
            app = QApplication.instance()
            if app:
                app.setStyleSheet(style_sheet)
            style_file.close()


class PublisherWidget(QWidget):
    def __init__(self, config: Dict[str, Any], ros_node: Node):
        super().__init__()
        self.config = config
        self.ros_node = ros_node
        self.msg_class = self.load_msg_class()
        self.publisher = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.publish_message)
        self.widget_map = {}
        self.init_ui()
        self.freq_spin.valueChanged.connect(self.update_publish_frequency)

    def load_msg_class(self):
        interface_type = self.config["interface_type"]
        pkg_msg = interface_type.split("/")
        pkg_name = pkg_msg[0]
        msg_name = pkg_msg[-1]
        module = importlib.import_module(f"{pkg_name}.msg")
        return getattr(module, msg_name)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Configuration Info Group
        info_group = QGroupBox("Configuration")
        info_layout = QFormLayout()
        info_layout.setContentsMargins(10, 15, 10, 15)
        info_layout.setSpacing(10)
        info_layout.addRow("Topic:", QLabel(self.config["topic_name"]))
        info_layout.addRow("Message Type:", QLabel(self.config["interface_type"]))
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Scroll Area for Message Fields
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.fields_widget = self.create_fields_widget(self.msg_class)
        scroll_area.setWidget(self.fields_widget)
        main_layout.addWidget(scroll_area)

        # Publish Control Group
        control_group = QGroupBox("Publish Control")
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.addWidget(QLabel("Frequency (Hz):"))
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 100)
        self.freq_spin.setValue(self.config.get("publish_frequency", 10))
        control_layout.addWidget(self.freq_spin)
        control_layout.addStretch()

        self.start_btn = QPushButton("Start Publishing")
        self.start_btn.setCheckable(True)
        self.start_btn.clicked.connect(self.toggle_publishing)
        control_layout.addWidget(self.start_btn)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

    def create_fields_widget(self, msg_class, parent_field: str = ""):
        widget = QWidget()
        layout = QFormLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        fields = msg_class.get_fields_and_field_types()

        for field_name, field_type in fields.items():
            field_key = f"{parent_field}.{field_name}" if parent_field else field_name
            if "/" in field_type:
                nested_class = self.resolve_nested_class(field_type)
                nested_widget = self.create_fields_widget(nested_class, field_key)
                group = QGroupBox(field_name)
                group.setLayout(nested_widget.layout())
                layout.addRow(group)
            else:
                input_widget = self.create_input_widget(field_type, field_key)
                layout.addRow(QLabel(field_name + ":"), input_widget)
                self.widget_map[field_key] = input_widget
        widget.setLayout(layout)
        return widget

    def resolve_nested_class(self, field_type: str):
        pkg_msg = field_type.split("/")
        pkg_name = pkg_msg[0]
        msg_name = pkg_msg[-1]
        module = importlib.import_module(f"{pkg_name}.msg")
        return getattr(module, msg_name)

    def create_input_widget(self, field_type: str, field_key: str):
        field_config = self.config.get("field_configs", {}).get(field_key, {})
        initial_value = field_config.get("default", 0)
        range_config = field_config.get("range")
        constants = self.get_constants(field_type) if not range_config else None

        # 优先处理范围设置
        if range_config:
            if field_type in ["float32", "float64", "double"]:
                spin = QDoubleSpinBox()
                spin.setMinimum(float(range_config.get("min", 0)))
                spin.setMaximum(float(range_config.get("max", 100)))
                spin.setValue(float(initial_value))
                spin.setSingleStep(0.1)
                return spin
            elif "int" in field_type:
                spin = QSpinBox()
                spin.setMinimum(int(range_config.get("min", 0)))
                spin.setMaximum(int(range_config.get("max", 100)))
                spin.setValue(int(initial_value))
                return spin

        # 处理常量枚举
        if constants:
            combo = QComboBox()
            for name, value in constants.items():
                combo.addItem(f"{name}  ({value})", value)
                if value == initial_value:
                    combo.setCurrentIndex(combo.count() - 1)
            return combo

        if field_type in ["float32", "float64", "double"]:
            spin = QDoubleSpinBox()
            spin.setValue(float(initial_value))
            return spin
        elif "int" in field_type:
            spin = QSpinBox()
            spin.setValue(int(initial_value))
            return spin
        elif field_type == "boolean":
            checkbox = QCheckBox()
            checkbox.setChecked(bool(initial_value))
            return checkbox
        elif field_type == "string":
            line_edit = QLineEdit(str(initial_value))
            return line_edit
        else:
            return QLabel(f"Unsupported type: {field_type}")

    def get_constants(self, field_type: str):
        constants = {}
        for name in dir(self.msg_class):
            if name.isupper():
                value = getattr(self.msg_class, name)
                if isinstance(value, int) and "int" in field_type:
                    constants[name] = value
                elif isinstance(value, bool) and field_type == "bool":
                    constants[name] = value
        return constants

    def toggle_publishing(self):
        if self.timer.isActive():
            self.timer.stop()
            self.start_btn.setChecked(False)
            if self.publisher:
                self.publisher.destroy()
                self.publisher = None
        else:
            self.publisher = self.ros_node.create_publisher(
                self.msg_class, self.config["topic_name"], 10
            )
            interval = 1000 // self.freq_spin.value()
            self.timer.start(interval)
            self.start_btn.setChecked(True)

    def update_publish_frequency(self):
        if self.timer.isActive():
            interval = 1000 // self.freq_spin.value()
            self.timer.setInterval(interval)

    def publish_message(self):
        msg = self.construct_message(self.msg_class)
        self.publisher.publish(msg)

    def construct_message(self, msg_class, parent_key: str = ""):
        msg = msg_class()
        fields = msg_class.get_fields_and_field_types()

        for field_name, field_type in fields.items():
            field_key = f"{parent_key}.{field_name}" if parent_key else field_name
            if "/" in field_type:  # Nested
                nested_class = self.resolve_nested_class(field_type)
                nested_msg = self.construct_message(nested_class, field_key)
                setattr(msg, field_name, nested_msg)
            else:
                widget = self.widget_map.get(field_key)
                if widget:
                    value = self.get_widget_value(widget)
                    setattr(msg, field_name, value)
        return msg

    def get_widget_value(self, widget):
        if isinstance(widget, QComboBox):
            return widget.currentData()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        return 0


def main():
    rclpy.init()
    app = QApplication(sys.argv)
    config_path = os.path.join(
        os.path.dirname(__file__), "../config/publish_anything_example.yaml"
    )
    gui = ROSPublisherGUI(config_path)
    gui.show()

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass
    finally:
        gui.ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
