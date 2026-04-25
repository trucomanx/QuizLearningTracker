#!/usr/bin/env python3

import sys
import json
import random
from dataclasses import dataclass
from typing import List, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLineEdit,
    QFileDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QMessageBox, QRadioButton, QButtonGroup, QTextEdit
)

from PyQt5.QtGui import QFont

from quiz_learning_tracker.modules.report_widget_custom import ReportWidget

# --- pyqtgraph for plotting ---
import pyqtgraph as pg

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
                prompt=f"<b>[{n_q+1}/{n_questions}] Qual tópico pertence a:</b> {correct_title}?",
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
                prompt=f"<b>[{n_q+1}/{n_questions}] A qual categoria pertence:</b> {correct_topic}?",
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

        self.setTitle("Curva de aprendizado")
        self.setLabel('left', 'Acurácia')
        self.setLabel('bottom', 'Tentativa')
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

        self.next_button = QPushButton("Próxima")
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
            QMessageBox.warning(self, "Aviso", "Selecione uma opção")
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

        summary = QLabel(f"<b>Resultado</b>: {correct}/{total} : {correct*100.0/total:.2f}%")
        font = summary.font()
        font.setPointSize(font.pointSize() * 2)
        summary.setFont(font)
        layout.addWidget(summary)

        self.text = ReportWidget(report)
        layout.addWidget(self.text)

        save_btn = QPushButton("Salvar relatório")
        save_btn.clicked.connect(self.save_report)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar", "report.json", "JSON (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=4, ensure_ascii=False)


# ============================================================
# MAIN WINDOW
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Quiz Generator")

        self.accuracies = []

        central = QWidget()
        layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        browse_btn = QPushButton("Selecionar JSON")
        browse_btn.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        self.q_spin = QSpinBox()
        self.q_spin.setValue(5)
        layout.addWidget(QLabel("Número de perguntas:"))
        layout.addWidget(self.q_spin)

        self.opt_spin = QSpinBox()
        self.opt_spin.setValue(4)
        layout.addWidget(QLabel("Número de alternativas:"))
        layout.addWidget(self.opt_spin)

        start_btn = QPushButton("Iniciar teste")
        start_btn.clicked.connect(self.start_test)
        layout.addWidget(start_btn)

        # --- plot abaixo do botão ---
        self.plot_widget = LearningCurveWidget()
        layout.addWidget(self.plot_widget)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar JSON", "", "JSON (*.json)")
        if path:
            self.file_input.setText(path)

    def start_test(self):
        path = self.file_input.text()
        if not path:
            QMessageBox.warning(self, "Erro", "Selecione um arquivo JSON")
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
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

