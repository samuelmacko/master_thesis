
from typing import List, Tuple

import numpy as np
from pandas import DataFrame, read_csv
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import pairwise_distances
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler


#
# ATTENTION!!!
#
# This is all UNTESTED and unused
# almost certainly needs a check before using
# it is here just for completeness
#
class Datasets:

    def __init__(self, maintained_path: str, unmaintained_path: str):
        self.maintained_path: str = maintained_path
        self.unmaintained_path: str = unmaintained_path

        self.maintained_df: DataFrame = None
        self.unmaintained_df: DataFrame = None
        self.centroid: np.ndarray = None
        self.X_train: np.ndarray = None
        self.X_test: np.ndarray = None
        self.y_train: np.ndarray = None
        self.y_test: np.ndarray = None

    def process_datasets(
            self, all_cols_to_drop: List[str], all_cols_to_encode: List[str],
            threshold: float
    ):
        self.maintained_df = read_csv(filepath_or_buffer=self.maintained_path)
        self.unmaintained_df = read_csv(
            filepath_or_buffer=self.unmaintained_path
        )

        correlated_cols = self.correlated_columns(
            dataset=self.unmaintained_df, threshold=threshold
        )
        self.maintained_df = self.maintained_df.drop(columns=correlated_cols)
        self.unmaintained_df = self.unmaintained_df.drop(
            columns=correlated_cols
        )

        maintained_tr = self.transform_dataframe(
            dataset=self.maintained_df, all_cols_to_drop=all_cols_to_drop,
            all_cols_to_encode=all_cols_to_encode
        )

        self.centroid = self.compute_centroid(dataset=maintained_tr)

        X_train_df, X_test_df = train_test_split(
            self.unmaintained_df, test_size=0.2, random_state=2
        )
        self.X_train = self.transform_dataframe(
            dataset=X_train_df, all_cols_to_drop=all_cols_to_drop,
            all_cols_to_encode=all_cols_to_encode
        )
        self.X_test = self.transform_dataframe(
            dataset=X_test_df, all_cols_to_drop=all_cols_to_drop,
            all_cols_to_encode=all_cols_to_encode
        )
        self.X_train, self.y_train = self.create_labels(
            X=self.X_train, centroid=self.centroid
        )
        self.X_test, self.y_test = self.create_labels(
            X=self.X_test, centroid=self.centroid
        )

    @classmethod
    def transform_dataframe(
            cls, dataset: DataFrame, all_cols_to_drop: List[str],
            all_cols_to_encode: List[str]
    ) -> np.ndarray:
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

    @classmethod
    def correlated_columns(cls, dataset: DataFrame, threshold: float) -> list:
        corr_matrix = dataset.corr().abs()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        correlated_columns_list = [
            col for col in upper_triangle.columns
            if any(upper_triangle[col] > threshold)
        ]
        return correlated_columns_list

    @classmethod
    def remove_correlated_columns(
            cls, dataset: DataFrame, corr_cols: List[str]
    ) -> DataFrame:
        return dataset.drop(columns=corr_cols)

    @classmethod
    def compute_centroid(cls, dataset: np.ndarray) -> np.ndarray:
        km = KMeans(n_clusters=1)
        km.fit(X=dataset)
        return km.cluster_centers_

    @classmethod
    def create_labels(
            cls, X: np.ndarray, centroid: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        distances = pairwise_distances(X=X, Y=centroid, metric='l2')
        distances = distances.reshape(distances.shape[0], 1)
        X_d = np.append(arr=X, values=distances, axis=1)

        lower_bound, upper_bound = cls.outlier_ranges(dataset=distances)
        X_r = X_d[
            (X_d[:, X_d.shape[1] - 1] > lower_bound) & \
            (X_d[:, X_d.shape[1] - 1] < upper_bound)
        ]

        _, edges = np.histogram(a=X_r[:, -1], bins=10)

        for i in range(X_d.shape[0]):
            distance = X_d[i, -1]
            label = np.searchsorted(a=edges, v=distance, side='left')
            if label == 0:
                label = 1
            if label > 10:
                label = 10

            X_d[i, X_d.shape[1] - 1] = label

        return X_d[:, :-1], X_d[:, -1]

    @classmethod
    def outlier_ranges(cls, dataset: np.ndarray) -> Tuple[float, float]:
        dataset.sort()
        Q1, Q3 = np.percentile(dataset, [25, 75])
        IQR = Q3 - Q1
        lower_range = Q1 - (1.5 * IQR)
        upper_range = Q3 + (1.5 * IQR)

        return lower_range, upper_range
