"""Test validation and external representation for commands in the Vizual
package.
"""

import os
import shutil
import unittest

from vizier.engine.packages.vizual.command import delete_column, load_dataset
from vizier.engine.packages.vizual.command import projection, sort_dataset, update_cell
from vizier.datastore.dataset import DatasetColumn, DatasetDescriptor
from vizier.filestore.fs.base import FileSystemFilestore, METADATA_FILENAME

import vizier.engine.packages.base as pckg
import vizier.engine.packages.vizual.base as vizual
import vizier.filestore.base as fs
import vizier.viztrail.command as md


DATASETS = {
    'ds': DatasetDescriptor(
        identifier='0000',
        name='ds',
        columns=[
            DatasetColumn(identifier=2, name='Some Name'),
            DatasetColumn(identifier=1, name='Street')
        ]
    )
}
PACKAGE = pckg.PackageIndex(vizual.VIZUAL_COMMANDS)

SERVER_DIR = './.tmp'
CSV_FILE = './tests/viztrail/module/.files/dataset.csv'


class TestValidateVizual(unittest.TestCase):

    def setUp(self):
        """Create an empty file server repository."""
        # Drop project descriptor directory
        if os.path.isdir(SERVER_DIR):
            shutil.rmtree(SERVER_DIR)

    def tearDown(self):
        """Clean-up by dropping file server directory.
        """
        if os.path.isdir(SERVER_DIR):
            shutil.rmtree(SERVER_DIR)

    def test_delete_column(self):
        """Test validation of delete column command."""
        cmd = delete_column(
            dataset_name='ds',
            column=2,
            validate=True
        ).to_external_form(
            command=PACKAGE.get(vizual.VIZUAL_DEL_COL),
            datasets=DATASETS
        )
        self.assertEqual(cmd, 'DELETE COLUMN \'Some Name\' FROM ds')

#     def test_load_dataset(self):
#         """Test validation of load dataset command."""
#         db = FileSystemFilestore(SERVER_DIR)
#         fh = db.upload_file(CSV_FILE)
#         cmd = load_dataset(
#             dataset_name='ds',
#             file={
#                 pckg.FILE_ID: fh.identifier,
#                 pckg.FILE_NAME: fh.file_name
#             },
#             validate=True
#         ).to_external_form(
#             command=PACKAGE.get(vizual.VIZUAL_LOAD),
#             datasets=DATASETS
#         )
#         self.assertEqual(cmd, 'LOAD DATASET ds FROM ' + fh.file_name)
#         cmd = load_dataset(
#             dataset_name='ds',
#             file={pckg.FILE_URL: 'http://some.file.url'},
#             validate=True
#         ).to_external_form(
#             command=PACKAGE.get(vizual.VIZUAL_LOAD),
#             datasets=DATASETS
#         )
#         self.assertEqual(cmd, 'LOAD DATASET ds FROM http://some.file.url')
#         cmd = load_dataset(
#             dataset_name='ds',
#             file={pckg.FILE_ID: fh.identifier, pckg.FILE_URL: 'http://some.file.url'},
#             validate=True
#         ).to_external_form(
#             command=PACKAGE.get(vizual.VIZUAL_LOAD),
#             datasets=DATASETS
#         )
#         self.assertEqual(cmd, 'LOAD DATASET ds FROM http://some.file.url')
#         cmd = load_dataset(
#             dataset_name='ds',
#             file={pckg.FILE_ID: 'Some File'},
#             validate=True
#         ).to_external_form(
#             command=PACKAGE.get(vizual.VIZUAL_LOAD),
#             datasets=DATASETS
#         )
#         self.assertEqual(cmd, 'LOAD DATASET ds FROM \'Some File\'')

    def test_projection(self):
        """Test validation of projection command."""
        cmd = projection(
            dataset_name='ds',
            columns=[{'column': 1, 'name': 'TheName'}, {'column': 2}],
            validate=True
        ).to_external_form(
            command=PACKAGE.get(vizual.VIZUAL_PROJECTION),
            datasets=DATASETS
        )
        self.assertEqual(cmd, 'FILTER COLUMNS Street, \'Some Name\' FROM ds')

    def test_sort_dataset(self):
        """Test validation of sort command."""
        cmd = sort_dataset(
            dataset_name='ds',
            columns=[{'column': 1, 'order': 'A-Z'}, {'column': 2, 'order': 'Z-A'}],
            validate=True
        ).to_external_form(
            command=PACKAGE.get(vizual.VIZUAL_SORT),
            datasets=DATASETS
        )
        self.assertEqual(cmd, 'SORT ds BY Street (A-Z), \'Some Name\' (Z-A)')

    def test_update_cell(self):
        """Test validation of update cell command."""
        cmd = update_cell(
            dataset_name='ds',
            column=2,
            row=1,
            value='Some Value',
            validate=True
        ).to_external_form(
            command=PACKAGE.get(vizual.VIZUAL_UPD_CELL),
            datasets=DATASETS
        )
        self.assertEqual(cmd, 'UPDATE ds SET [\'Some Name\', 1] = \'Some Value\'')


if __name__ == '__main__':
    unittest.main()
