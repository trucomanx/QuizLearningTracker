#!/usr/bin/env python3

import os
import sys
import json
import random
import signal
import subprocess

from dataclasses import dataclass
from typing import List, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLineEdit,
    QFileDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QMessageBox, QRadioButton, QButtonGroup, QTextEdit, QAction, QSizePolicy
)

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices, QFont


import quiz_learning_tracker.about as about
import quiz_learning_tracker.modules.configure as configure 
from quiz_learning_tracker.modules.resources import resource_path

from quiz_learning_tracker.modules.wabout    import show_about_window
from quiz_learning_tracker.desktop import create_desktop_file, create_desktop_directory, create_desktop_menu

from quiz_learning_tracker.modules.report_widget_custom import ReportWidget

import pyqtgraph as pg

# ---------- Path to config file ----------
CONFIG_PATH = os.path.join( os.path.expanduser("~"),
                            ".config", 
                            about.__package__, 
                            "config.json" )

DEFAULT_CONTENT={   
    "toolbar_configure": "Configure",
    "toolbar_configure_tooltip": "Open the configure Json file of program GUI",
    "toolbar_about": "About",
    "toolbar_about_tooltip": "About the program",
    "toolbar_coffee": "Coffee",
    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",
    "question_topic_text": "Which topic belongs to:",
    "question_category_text": "Which category does it belong to:",
    "learning_curve_text": "Learning curve",
    "attempt_text": "Attempt",
    "accuracy_text": "Accuracy",
    "warning_text": "Warning",
    "next_text": "Next",
    "select_option_text": "Select an option",
    "result_text": "Result",
    "save_report_text": "Save report",
    "save_text": "Save",
    "select_json_text": "Select JSON",
    "number_questions_text": "Number of questions:",
    "number_alternatives_text": "Number of alternatives:",
    "start_test_text": "Start Test",
    "error_text": "Error",
    "window_width": 800,
    "window_height": 600
}

configure.verify_default_config(CONFIG_PATH,default_content=DEFAULT_CONTENT)

CONFIG=configure.load_config(CONFIG_PATH)

# ---------------------------------------

# ============================================================
# DATA MODELS
# ============================================================
@dataclass
class Question:
    prompt: str
    options: List[str]
    correct_index: int
    correct_answers: List[str]  # <-- NOVO


# ============================================================
# DATA LOADER
# ============================================================
def load_json(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# QUESTION GENERATOR
# ============================================================
def generate_questions(data, n_questions, n_options):
    questions = []

    titles = []
    topics = []

    for item in data:
        titles.extend(item['title'])
        topics.extend(item['topics'])

    for n_q in range(n_questions):
        if random.choice([True, False]):
            # title -> topics
            item = random.choice(data)
            correct_title = random.choice(item['title'])

            # TODOS os tópicos válidos
            correct_answers = item['topics']
            correct_topic = random.choice(correct_answers)

            wrong_topics = random.sample(
                [t for t in topics if t != correct_topic],
                min(n_options - 1, len(topics) - 1)
            )

            options = wrong_topics + [correct_topic]
            random.shuffle(options)

            questions.append(Question(
                prompt=f"<b>[{n_q+1}/{n_questions}] {CONFIG['question_topic_text']}</b> {correct_title}?",
                options=options,
                correct_index=options.index(correct_topic),
                correct_answers=correct_answers
            ))

        else:
            # topic -> titles
            item = random.choice(data)
            correct_topic = random.choice(item['topics'])

            # TODOS os títulos válidos
            correct_answers = item['title']
            correct_title = random.choice(correct_answers)

            wrong_titles = random.sample(
                [t for t in titles if t != correct_title],
                min(n_options - 1, len(titles) - 1)
            )

            options = wrong_titles + [correct_title]
            random.shuffle(options)

            questions.append(Question(
                prompt=f"<b>[{n_q+1}/{n_questions}] {CONFIG['question_category_text']}</b> {correct_topic}?",
                options=options,
                correct_index=options.index(correct_title),
                correct_answers=correct_answers
            ))

    return questions


# ============================================================
# PLOT WIDGET
# ============================================================
class LearningCurveWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()

        self.setTitle(CONFIG["learning_curve_text"])
        self.setLabel('left', CONFIG["accuracy_text"])
        self.setLabel('bottom', CONFIG["attempt_text"])
        self.setYRange(0, 1)

        self.curve = self.plot([], [], pen=pg.mkPen(width=2), symbol='o')

    def update_curve(self, accuracies: List[float]):
        if not accuracies:
            self.curve.setData([], [])
            return

        x = list(range(1, len(accuracies) + 1))
        self.curve.setData(x, accuracies)


# ============================================================
# TEST WINDOW
# ============================================================
class TestWindow(QWidget):
    def __init__(self, questions, callback_on_finish):
        super().__init__()
        self.questions = questions
        self.index = 0
        self.answers = []
        self.callback_on_finish = callback_on_finish

        self.layout = QVBoxLayout()

        self.label = QLabel()
        self.layout.addWidget(self.label)

        self.button_group = QButtonGroup(self)
        self.options_layout = QVBoxLayout()
        self.layout.addLayout(self.options_layout)

        self.next_button = QPushButton(CONFIG["next_text"])
        self.next_button.clicked.connect(self.next_question)
        self.layout.addWidget(self.next_button)

        self.setLayout(self.layout)

        self.load_question()

    def load_question(self):
        q = self.questions[self.index]
        self.label.setText(q.prompt)

        # clear old
        for i in reversed(range(self.options_layout.count())):
            self.options_layout.itemAt(i).widget().deleteLater()

        self.button_group = QButtonGroup(self)

        for i, option in enumerate(q.options):
            btn = QRadioButton(option)
            self.button_group.addButton(btn, i)
            self.options_layout.addWidget(btn)

    def next_question(self):
        selected = self.button_group.checkedId()
        if selected == -1:
            QMessageBox.warning(self, CONFIG["warning_text"], CONFIG["select_option_text"])
            return

        self.answers.append(selected)
        self.index += 1

        if self.index >= len(self.questions):
            self.finish()
        else:
            self.load_question()

    def finish(self):
        correct = 0
        report = []

        for i, q in enumerate(self.questions):
            selected_text = q.options[self.answers[i]]

            # <-- NOVA LÓGICA
            is_correct = selected_text in q.correct_answers

            if is_correct:
                correct += 1

            report.append({
                "question": q.prompt,
                "selected": selected_text,
                "correct_set": list(set(q.correct_answers) & set(q.options)),
                "is_correct": is_correct
            })

        accuracy = correct / len(self.questions)

        # callback para atualizar curva
        self.callback_on_finish(accuracy)

        self.report_window = ReportWindow(report, correct, len(self.questions))
        self.report_window.show()
        self.close()


# ============================================================
# REPORT WINDOW
# ============================================================
class ReportWindow(QWidget):
    def __init__(self, report, correct, total):
        super().__init__()

        self.report = report

        layout = QVBoxLayout()

        summary = QLabel(f"<b>{CONFIG['result_text']}</b>: {correct}/{total} : {correct*100.0/total:.2f}%")
        font = summary.font()
        font.setPointSize(font.pointSize() * 2)
        summary.setFont(font)
        layout.addWidget(summary)

        self.text = ReportWidget(report)
        layout.addWidget(self.text)

        save_btn = QPushButton(CONFIG["save_report_text"])
        save_btn.clicked.connect(self.save_report)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_report(self):
        path, _ = QFileDialog.getSaveFileName(self, CONFIG["save_text"], "report.json", "JSON (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=4, ensure_ascii=False)


# ============================================================
# MAIN WINDOW
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(about.__program_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])
        
        ## Icon
        # Get base directory for icons
        self.icon_path = resource_path("icons", "logo.png")
        self.setWindowIcon(QIcon(self.icon_path)) 

        self._create_toolbar()

        self.accuracies = []

        central = QWidget()
        layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        browse_btn = QPushButton(CONFIG["select_json_text"])
        browse_btn.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        self.q_spin = QSpinBox()
        self.q_spin.setValue(5)
        layout.addWidget(QLabel(CONFIG["number_questions_text"]))
        layout.addWidget(self.q_spin)

        self.opt_spin = QSpinBox()
        self.opt_spin.setValue(4)
        layout.addWidget(QLabel(CONFIG["number_alternatives_text"]))
        layout.addWidget(self.opt_spin)

        start_btn = QPushButton(CONFIG["start_test_text"])
        start_btn.clicked.connect(self.start_test)
        layout.addWidget(start_btn)

        # --- plot abaixo do botão ---
        self.plot_widget = LearningCurveWidget()
        layout.addWidget(self.plot_widget)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def _create_toolbar(self):
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # Adicionar o espaçador
        self.toolbar_spacer = QWidget()
        self.toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar.addWidget(self.toolbar_spacer)
        
        #
        self.configure_action = QAction(QIcon.fromTheme("document-properties"), 
                                        CONFIG["toolbar_configure"], 
                                        self)
        self.configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        self.configure_action.triggered.connect(self.open_configure_editor)
        self.toolbar.addAction(self.configure_action)
        
        #
        self.about_action = QAction(QIcon.fromTheme("help-about"), 
                                    CONFIG["toolbar_about"], 
                                    self)
        self.about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        self.about_action.triggered.connect(self.open_about)
        self.toolbar.addAction(self.about_action)
        
        # Coffee
        self.coffee_action = QAction(   QIcon.fromTheme("emblem-favorite"), 
                                        CONFIG["toolbar_coffee"], 
                                        self)
        self.coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        self.coffee_action.triggered.connect(self.on_coffee_action_click)
        self.toolbar.addAction(self.coffee_action)

        # Conectar ao sinal de mudança de orientação
        self.toolbar.orientationChanged.connect(self.on_update_spacer_policy)
        self.on_update_spacer_policy()

    def on_update_spacer_policy(self):
        """Atualiza a política do espaçador baseado na orientação da toolbar"""
        if self.toolbar.orientation() == Qt.Horizontal:
            # Horizontal: expande na largura
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        else:
            # Vertical: expande na altura
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def _open_file_in_text_editor(self, filepath):
        if os.name == 'nt':  # Windows
            os.startfile(filepath)
        elif os.name == 'posix':  # Linux/macOS
            subprocess.run(['xdg-open', filepath])
    
    def open_url_usage_editor(self):
        QDesktopServices.openUrl(QUrl(CONFIG_GPT["usage"]))
        
    def open_configure_editor(self):
        self._open_file_in_text_editor(CONFIG_PATH)

    def open_about(self):
        data={
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_name__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data,self.icon_path)

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, CONFIG["select_json_text"], "", "JSON (*.json)")
        if path:
            self.file_input.setText(path)

    def start_test(self):
        path = self.file_input.text()
        if not path:
            QMessageBox.warning(self, CONFIG["error_text"], CONFIG["select_json_text"])
            return

        data = load_json(path)

        questions = generate_questions(
            data,
            self.q_spin.value(),
            self.opt_spin.value()
        )

        self.test_window = TestWindow(questions, self.on_test_finished)
        self.test_window.show()

    def on_test_finished(self, accuracy):
        self.accuracies.append(accuracy)
        self.plot_widget.update_curve(self.accuracies)


# ============================================================
# MAIN
# ============================================================

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_name__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
    
    
    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__) 
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

