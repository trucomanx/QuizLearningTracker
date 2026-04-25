#!/usr/bin/python3

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt


class QuestionItemWidget(QFrame):
    def __init__(self, item_data):
        super().__init__()

        layout = QVBoxLayout()

        # question
        q_label = QLabel(f"<b>Question:</b> {item_data['question']}")
        q_label.setWordWrap(True)
        layout.addWidget(q_label)

        # selected
        s_label = QLabel(f"<b>Selected:</b> {item_data['selected']}")
        layout.addWidget(s_label)

        # correct set
        c_label = QLabel("<b>Correct options:</b>")
        layout.addWidget(c_label)

        list_widget = QListWidget()
        for val in item_data['correct_set']:
            QListWidgetItem(val, list_widget)
        layout.addWidget(list_widget)

        # color feedback
        if item_data['is_correct']:
            self.setStyleSheet("background-color: #c8f7c5; border: 1px solid #aaa;")
        else:
            self.setStyleSheet("background-color: #f7c5c5; border: 1px solid #aaa;")

        self.setLayout(layout)


class ReportWidget(QWidget):
    def __init__(self, report_data):
        super().__init__()

        main_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container_layout = QVBoxLayout()

        for item in report_data:
            widget = QuestionItemWidget(item)
            container_layout.addWidget(widget)

        container_layout.addStretch()
        container.setLayout(container_layout)

        scroll.setWidget(container)

        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

