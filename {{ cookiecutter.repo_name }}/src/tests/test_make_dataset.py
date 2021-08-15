#!/usr/bin/env python3
import os.path

import pytest
from pathlib import Path
from click.testing import CliRunner

from src.data import make_dataset


@pytest.fixture
def input_dir():
    return "./src/tests/test_data/mnist_small_train"


@pytest.fixture
def output_dir():
    return "./src/tests/test_data"


@pytest.fixture
def output_filename():
    return "pytest_mapfile.csv"


@pytest.fixture
def test_params():
    return "./src/tests/test_data/test_params.yaml"


def test_make_dataset(input_dir, output_dir, output_filename, test_params):
    """TODO"""
    # delete existing file
    if Path(output_dir).joinpath(output_filename).exists():
        os.remove(Path(output_dir).joinpath(output_filename))

    runner = CliRunner()
    result = runner.invoke(
        make_dataset.main,
        [
            input_dir,
            output_dir,
            output_filename,
            "-p",
            "./src/tests/test_data/test_params.yaml",
            "--force",
        ],
    )

    assert result.exit_code == 0
    assert not result.exception
    assert (
        result.output.strip()
        == "Found 100 images belonging to 10 classes.\nProcessed 100 images."
    )
    assert Path(output_dir).joinpath(output_filename).exists()
    assert Path(output_dir).joinpath("label_encoding.yaml").exists()
    assert Path(output_dir).joinpath("split_train_dev.csv").exists()
