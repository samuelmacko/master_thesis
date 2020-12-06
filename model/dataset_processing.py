
from typing import Optional

from numpy import empty, histogram, ndarray, searchsorted
from pandas import DataFrame, read_csv
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class ProcessedDataset:

    def __init__(
        self, maintained_path: str, unmaintained_path: str,
        test_size: Optional[float] = None
    ) -> None:
        maintained = read_csv(filepath_or_buffer=maintained_path)
        unmaintained = read_csv(filepath_or_buffer=unmaintained_path)

        maintained_transformed = self.transform_dataframe(dataset=maintained)
        unmaintained_transformed = self.transform_dataframe(
            dataset=unmaintained
        )
        centroid = self.compute_centroid(dataset=maintained_transformed)
        distances = self.distances_from_centroid(
            dataset=unmaintained_transformed, centroid=centroid
        )
        self.X: ndarray = unmaintained_transformed
        self.y: ndarray = self.create_labels(distances=distances)

        if test_size:
            self.create_split(test_size=test_size)
        else:
            self.X_train, self.X_test, self.y_train, self.y_test = None

    def transform_dataframe(self, dataset: DataFrame) -> ndarray:
        all_cols_to_drop = ['repo_name', 'url']
        all_cols_to_encode = [
            'owner_type', 'has_test', 'has_doc', 'has_example', 'has_readme'
        ]

        cols_to_drop = [
            col for col in all_cols_to_drop if col in dataset.columns
        ]
        cols_to_encode = [
            col for col in all_cols_to_encode if col in dataset.columns
        ]
        cols_to_scale = [
            col for col in dataset.columns if (
                col not in cols_to_encode and col not in cols_to_drop
            )
        ]

        transformer = ColumnTransformer([
            ('OHE', OneHotEncoder(), cols_to_encode),
            ('StScaler', StandardScaler(), cols_to_scale)
        ])

        return transformer.fit_transform(dataset)

    def compute_centroid(self, dataset: ndarray) -> ndarray:
        model = KMeans(n_clusters=1)
        model.fit(X=dataset)
        return model.cluster_centers_

    def distances_from_centroid(
        self, dataset: ndarray, centroid: ndarray
    ) -> ndarray:
        distances = pairwise_distances(X=dataset, Y=centroid, metric='l2')
        return distances

    def create_labels(self, distances: ndarray) -> ndarray:
        labels = empty(shape=distances.size)
        _, edges = histogram(a=distances, bins=10)
        for i, distance in enumerate(distances):
            label = searchsorted(a=edges, v=distance, side='left')
            # the smallest distance will get the label of 0
            # which is not a supported value for a label
            # the correct label for this distance is 1
            if not label:
                label = 1
            labels[i] = label
        return labels

    def create_split(self, test_size: float) -> None:
        self.X_train, self.X_test,
        self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=0
        )

    # todo implement better choosing of classifiers
    # also add other parameters like threshold and so on
    def detect_outliers(self) -> ndarray:
        from sklearn.ensemble import IsolationForest
        clf = IsolationForest(random_state=0)
        return clf.fit_predict(X=self.X)

    def remove_outliers(self, outliers: ndarray) -> None:
        self.X = self.X[~outliers]
