#!/usr/bin/env python3

import os
import click
from dotenv import find_dotenv, load_dotenv
import logging
from pathlib import Path
import pandas as pd

import tensorflow as tf
from tensorflow.data import AUTOTUNE


# load custom libraries from src
from src.data import mapfile, load_data
from src.img.tfreader import tf_imread
from src.img.augment import apply_transforms
from src.data import load_params
from src.models import networks

# set tf warning options
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def train(
    mapfile_path,
    cv_idx_path,
    params_filepath="params.yaml",
    results_dir="./results",
    model_dir="./models",
    debug=False,
):  # sourcery skip: inline-immediately-returned-variable
    """Accept filepaths to the mapfile and train-dev split, train mode, and return
    training history."""
    assert type(mapfile_path) is str, TypeError(f"MAPFILE must be type STR")

    # read files
    mapfile_df, cv_idx = load_data(
        [mapfile_path, cv_idx_path], sep=",", header=0, index_col=0, dtype=str
    )

    # load params
    params = load_params(params_filepath)["flow_from_dataframe"]
    random_seed = load_params(params_filepath)["random_seed"]
    batch_size = params["batch_size"]
    target_size = params["target_size"]
    n_classes = params["n_classes"]
    epochs = params["epochs"]

    # set random seed
    tf.random.set_seed(random_seed)

    # create dataset using tf.data
    data_records = [list(elem) for elem in mapfile_df.to_records(index=False)]
    dataset = tf.data.Dataset.from_tensor_slices(data_records)

    # build tf.data pipeline
    dataset = (
        dataset.map(tf_imread, num_parallel_calls=AUTOTUNE)
        # .map(apply_transforms, num_parallel_calls=AUTOTUNE)
        .cache()  # cache after mapping
        .shuffle(  # shuffle after caching to randomize order
            buffer_size=100,
            seed=random_seed,
            reshuffle_each_iteration=True,
        )
        .repeat()  # infinite cardinality
        .batch(
            batch_size=batch_size,
            drop_remainder=True,
            num_parallel_calls=AUTOTUNE,
            deterministic=debug,
        )
        .prefetch(AUTOTUNE)
    )

    # create model
    model = networks.simple_nn(input_shape=target_size, n_classes=n_classes)

    # train model
    logger = logging.getLogger(__name__)
    logger.info(f"Training model for {epochs} epochs")
    history = model.fit(x=dataset, steps_per_epoch=100, epochs=epochs, verbose=1)

    return history


@click.command()
@click.argument(
    "mapfile_path",
    default=Path("./data/interim/mapfile_df.csv").resolve(),
    type=click.Path(exists=True),
    # help="Filepath to the CSV with image filenames and class labels.",
)
@click.argument(
    "cv_idx_path",
    default=Path("./data/processed/split_train_dev.csv").resolve(),
    type=click.Path(exists=True),
    # help="Filepath to the CSV with the cross validation train/dev splits.",
)
@click.option("--params_filepath", "-p", default="params.yaml")
@click.option(
    "--results-dir",
    default=Path("./results").resolve(),
    type=click.Path(),
)
@click.option(
    "--model-dir",
    default=Path("./models").resolve(),
    type=click.Path(),
)
@click.option(
    "--debug",
    is_flag=True,
    help="Debug switch that turns off augmentation, shuffle, and makes runs deterministic.",
)
def main(
    mapfile_path,
    cv_idx_path,
    params_filepath="params.yaml",
    results_dir="./results",
    model_dir="./models",
    debug=False,
):
    train(
        mapfile_path,
        cv_idx_path,
        params_filepath=params_filepath,
        results_dir=results_dir,
        model_dir=model_dir,
        debug=debug,
    )


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
