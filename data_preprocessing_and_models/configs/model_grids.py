
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC


GRIDS = [
    {
        'name': 'RandomForest',
        'class': RandomForestClassifier,
        'parameters': {
            # 'n_estimators': [*range(50, 160, 25)],
            # 'criterion': ['gini', 'entropy'],
            # 'max_features': ['auto', 'sqrt'],
            # 'max_depth': [*range(10, 60, 10)] + [None],
            # 'min_samples_split': [2, 5, 10],
            # 'min_samples_leaf': [1, 2, 4],
            # 'max_features': ['auto', 'sqrt', 'log2'],
            'bootstrap': [True, False],
            'n_jobs': [-1]
        }
    },
    # {
    #     'name': 'SVC',
    #     'class': SVC,
    #     'parameters': {
    #         'C': [0.1, 1, 10, 100, 1000],
    #         'kernel': ['linear', 'poly', 'rbf', 'sigmoid'],
    #         'gamma': ['scale', 'auto', 1, .1, .01, .001, .0001],
    #         'shrinking': [True, False],
    #         'decision_function_shape': ['ovo', 'ovr']
    #     }
    # },
    # {
    #     'name': 'kNN',
    #     'class': KNeighborsClassifier,
    #     'parameters': {
    #         'n_neighbors': [*range(1, 6)],
    #         'weights': ['uniform', 'distance'],
    #         'algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute'],
    #         'leaf_size': [*range(20, 41, 5)],
    #         'p': [1, 2],
    #         'metric': ['minkowski', 'chebyshev'],
    #         'n_jobs': [-1]
    #     }
    # },
    # {
    #     'name': 'MLP',
    #     'class': MLPClassifier,
    #     'parameters': {
    #         'hidden_layer_sizes': [*range(175, 260, 25)],
    #         'activation': ['logistic', 'relu'],
    #         'alpha': [.001, .0001],
    #         'learning_rate': ['constant', 'adaptive'],
    #         'warm_start': [True, False]
    #     }
    # }
]
