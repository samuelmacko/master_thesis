
import logging

from configs.model_grids import GRIDS
import models as md
from s3_handler import S3Handler


log = logging.getLogger(__name__)
log.setLevel('DEBUG')

converted_level = logging.getLevelName('DEBUG')
file_handler = logging.FileHandler('main_log.log')
file_handler.setLevel(converted_level)
console_handler = logging.StreamHandler()
console_handler.setLevel(converted_level)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(fmt=formatter)
console_handler.setFormatter(fmt=formatter)

log.addHandler(hdlr=file_handler)
log.addHandler(hdlr=console_handler)


X_train = md.load_dataset(file_path='datasets/X_train.npy', log=log)
y_train = md.load_dataset(file_path='datasets/y_train.npy', log=log)

s3 = S3Handler(region_name='us-west-2')

for model_grid in GRIDS:
    model = md.compute_model(
        X=X_train, y=y_train, model_grid=model_grid, log=log
    )

    md.save_model(
        model=model, file_path=f'models/{model_grid["name"]}.pkl', log=log
    )

    # s3.upload_file(
    #     file_name='models/' + model_grid['name'], log=log,
    #     prefix='samuelmacko-thesis/trained_models/'
    # )
