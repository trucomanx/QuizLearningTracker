# quiz-learning-tracker

A simple application to generate quizzes from structured data and track learning performance over time.

![logo](https://raw.githubusercontent.com/trucomanx-desktop/QuizLearningTracker/main/screenshot.png)

## 1. Installing

To install the package from [PyPI](https://pypi.org/project/quiz_learning_tracker/), follow the instructions below:


```bash
pip install --upgrade quiz_learning_tracker
```

Execute `which quiz-learning-tracker` to see where it was installed, probably in `/home/USERNAME/.local/bin/quiz-learning-tracker`.

### Using

To start, use the command below:

```bash
quiz-learning-tracker
```

and load a JSON file in the next format

```
[
  {
    "title": ["Data Preprocessing"],
    "topics": [
      "Clean missing values",
      "Normalize or scale data",
      "Categóricos: one-hot encoding, label encoding",
    ]
  },
  {
    "title": ["Data Visualization", "Visualization"],
    "topics": [
      "Use charts to explore data",
      "Examples: bar, scatter"
    ]
  },
  {
    "title": ["EDA", "Exploratory Analysis"],
    "topics": [
      "Understand patterns",
      "Check correlations"
    ]
  }
]
```

## 2. More information

If you want more information go to [doc](https://github.com/trucomanx-desktop/QuizLearningTracker/blob/main/doc) directory.

## 3. Buy me a coffee

If you find this tool useful and would like to support its development, you can buy me a coffee!  
Your donations help keep the project running and improve future updates.  

[☕ Buy me a coffee](https://ko-fi.com/trucomanx) 

## 4. License

This project is licensed under the GPL license. See the `LICENSE` file for more details.
