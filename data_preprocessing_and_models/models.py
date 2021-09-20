
from logging import Logger
from typing import Dict

from numpy import load as np_load, ndarray, save as np_save
from pickle import dump as pickle_dump, load as pickle_load
from sklearn.base import BaseEstimator
from sklearn.model_selection._search import BaseSearchCV
from sklearn.model_selection import GridSearchCV


def save_model(model: BaseEstimator, file_path: str, log: Logger) -> None:
    log.info(msg='Saving model: ' + file_path)
    with open(file_path, 'wb') as f:
        pickle_dump(model, f)
    log.debug(msg='Model successfully saved: ' + file_path)


def load_model(file_path: str, log: Logger) -> BaseEstimator:
    log.info(msg='Loading model: ' + file_path)
    with open(file_path, 'rb') as f:
        return pickle_load(f)


def save_dataset(dataset: ndarray, file_path: str, log: Logger) -> None:
    log.info(msg='Saving dataset: ' + file_path)
    with open(file_path, 'wb') as f:
        np_save(f, dataset)
    log.debug(msg='Dataset successfully saved: ' + file_path)


def load_dataset(file_path: str, log: Logger) -> ndarray:
    log.info(msg='Loading dataset: ' + file_path)
    with open(file_path, 'rb') as f:
        return np_load(f)


def compute_model(
        X: ndarray, y: ndarray, model_grid: Dict, log: Logger
) -> BaseSearchCV:
    log.info(msg='Started computing model: ' + model_grid['name'])

    scoring = {
        'accuracy': 'accuracy',
    }

    clf = GridSearchCV(
        estimator=model_grid['class'](), param_grid=model_grid['parameters'],
        scoring=scoring, refit='accuracy'
    )
    clf.fit(X=X, y=y)

    log.debug(msg='Successfully computed model: ' + model_grid['name'])

    return clf.best_estimator_
