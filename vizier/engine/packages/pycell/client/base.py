# Copyright (C) 2018 New York University,
#                    University at Buffalo,
#                    Illinois Institute of Technology.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The vizier datastore client enables access to and manipulation of datasets in
a datastore from within a python script.
"""

from vizier.core.util import is_valid_name
from vizier.datastore.dataset import DatasetColumn, DatasetDescriptor
from vizier.datastore.metadata import DatasetMetadata
from vizier.engine.packages.pycell.client.dataset import DatasetClient


class VizierDBClient(object):
    """The Vizier DB Client provides access to datasets that are identified by
    a unique name. The client is a wrapper around a given database state.
    """
    def __init__(self, datastore, datasets):
        """Initialize the reference to the workflow context and the datastore.

        Parameters
        ----------
        datastore: vizier.datastore.base.Datastore
            Data store to access and manipulate datasets
        datasets: dict
            Mapping of dataset names to unique persistent dataset identifier
            generated by the data store.
        """
        self.datastore = datastore
        self.datasets = dict(datasets)
        # Keep track of datasets that are read and written.
        self.read = set()
        self.write = set()
        self.delete = None

    def create_dataset(self, name, dataset):
        """Create a new dataset with given name.

        Raises ValueError if a dataset with given name already exist.

        Parameters
        ----------
        name : string
            Unique dataset name
        dataset : vizier.datastore.base.Dataset
            Dataset object

        Returns
        -------
        vizier.datastore.client.DatasetClient
        """
        # Raise an exception if a dataset with the given name already exists or
        # if the name is not valid
        if self.has_dataset_identifier(name):
            # Record access to the datasets
            self.read.add(name.lower())
            raise ValueError('dataset \'' + name + '\' already exists')
        if not is_valid_name(name):
            raise ValueError('invalid dataset name \'' + name + '\'')
        # Create list of columns for new dataset. Ensure that every column has
        # a positive identifier
        columns = list()
        if len(dataset.columns) == 0:
            column_counter = 0
        else:
            column_counter = max(max([col.identifier for col in dataset.columns]) + 1, 0)
            for col in dataset.columns:
                if col.identifier < 0:
                    col.identifier = column_counter
                    column_counter += 1
                columns.append(
                    DatasetColumn(
                        identifier=col.identifier,
                        name=col.name,
                        data_type=col.data_type
                    )
                )
        rows = dataset.rows
        if len(rows) == 0:
            row_counter = 0
        else:
            # Ensure that all rows have positive identifier
            row_counter = max(max([row.identifier for row in rows]) + 1, 0)
            for row in rows:
                if row.identifier < 0:
                    row.identifier = row_counter
                    row_counter += 1
        # Write dataset to datastore and add new dataset to context
        ds = self.datastore.create_dataset(
            columns=columns,
            rows=rows,
            column_counter=column_counter,
            row_counter=row_counter,
            annotations=dataset.annotations
        )
        self.set_dataset_identifier(name, ds.identifier)
        return DatasetClient(dataset=ds)

    def drop_dataset(self, name):
        """Remove the dataset with the given name.

        Raises ValueError if no dataset with given name exist.

        Parameters
        ----------
        name : string
            Unique dataset name
        """
        # Remove the context dataset identifier for the given name. Will raise
        # a ValueError if dataset does not exist
        if self.delete is None:
            self.delete = set()
        self.delete.add(name)
        self.remove_dataset_identifier(name)

    def get_dataset(self, name):
        """Get dataset with given name.

        Raises ValueError if the specified dataset does not exist.

        Parameters
        ----------
        name : string
            Unique dataset name

        Returns
        -------
        vizier.datastore.client.DatasetClient
        """
        # Make sure to record access idependently of whether the dataset exists
        # or not. Ignore read access to datasets that have been written.
        if not name.lower() in self.write:
            self.read.add(name.lower())
        # Get identifier for the dataset with the given name. Will raise an
        # exception if the name is unknown
        identifier = self.get_dataset_identifier(name)
        # Read dataset from datastore and return it.
        dataset = self.datastore.get_dataset(identifier)
        if dataset is None:
            raise ValueError('unknown dataset \'' + identifier + '\'')
        return DatasetClient(dataset=dataset)

    def get_dataset_identifier(self, name):
        """Returns the unique identifier for the dataset with the given name.

        Raises ValueError if no dataset with the given name exists.

        Parameters
        ----------
        name: string
            Dataset name

        Returns
        -------
        string
        """
        # Datset names should be case insensitive
        key = name.lower()
        if not key in self.datasets:
            raise ValueError('unknown dataset \'' + name + '\'')
        return self.datasets[key]

    def has_dataset_identifier(self, name):
        """Test whether a mapping for the dataset with the given name exists.

        Parameters
        ----------
        name: string
            Dataset name

        Returns
        -------
        bool
        """
        # Dataset names are case insensitive
        return name.lower() in self.datasets

    def new_dataset(self):
        """Get a dataset client instance for a new dataset.

        Returns
        -------
        vizier.datastore.client.DatasetClient
        """
        return DatasetClient()

    def remove_dataset_identifier(self, name):
        """Remove the entry in the dataset dictionary that is associated with
        the given name. Raises ValueError if not dataset with name exists.

        Parameters
        ----------
        name: string
            Dataset name
        identifier: string
            Unique identifier for persistent dataset
        """
        # Convert name to lower case to ensure that names are case insensitive
        key = name.lower()
        if not key in self.datasets:
            raise ValueError('unknown dataset \'' + name + '\'')
        del self.datasets[key]

    def rename_dataset(self, name, new_name):
        """Rename an existing dataset.

        Raises ValueError if a dataset with given name already exist.

        Raises ValueError if dataset with name does not exist or if dataset with
        new_name already exists.

        Parameters
        ----------
        name : string
            Unique dataset name
        new_name : string
            New dataset name
        """
        # Make sure to record access idependently of whether the dataset exists
        # or not. Ignore read access to datasets that have been written.
        if not name.lower() in self.write:
            self.read.add(name.lower())
        # Add the new name to the written datasets
        self.write.add(new_name.lower())
        # Raise exception if new_name exists or is not valid.
        if self.has_dataset_identifier(new_name):
            raise ValueError('dataset \'' + new_name + '\' exists')
        if not is_valid_name(new_name):
            raise ValueError('invalid dataset name \'' + new_name + '\'')
        # Raise an exception if no dataset with the given name exists
        identifier = self.get_dataset_identifier(name)
        self.remove_dataset_identifier(name)
        self.set_dataset_identifier(new_name, identifier)

    def set_dataset_identifier(self, name, identifier):
        """Sets the identifier to which the given dataset name points.

        Parameters
        ----------
        name: string
            Dataset name
        identifier: string
            Unique identifier for persistent dataset
        """
        # Convert name to lower case to ensure that names are case insensitive
        self.datasets[name.lower()] = identifier
        self.write.add(name.lower())

    def update_dataset(self, name, dataset):
        """Update a given dataset.

        Raises ValueError if the specified dataset does not exist.

        Parameters
        ----------
        name : string
            Unique dataset name
        dataset : vizier.datastore.base.Dataset
            Dataset object

        Returns
        -------
        vizier.datastore.client.DatasetClient
        """
        # Get identifier for the dataset with the given name. Will raise an
        # exception if the name is unknown
        identifier = self.get_dataset_identifier(name)
        # Read dataset from datastore to get the column and row counter.
        source_dataset = self.datastore.get_dataset(identifier)
        if source_dataset is None:
            # Record access to the datasets
            self.read.add(name.lower())
            raise ValueError('unknown dataset \'' + identifier + '\'')
        column_counter = source_dataset.column_counter
        row_counter = source_dataset.row_counter
        # Update column and row identifier
        columns = dataset.columns
        rows = dataset.rows
        # Ensure that all columns has positive identifier
        for col in columns:
            if col.identifier < 0:
                col.identifier = column_counter
                column_counter += 1
        # Ensure that all rows have positive identifier
        for row in rows:
            if row.identifier < 0:
                row.identifier = row_counter
                row_counter += 1
        # Write dataset to datastore and add new dataset to context
        ds = self.datastore.create_dataset(
            columns=columns,
            rows=rows,
            column_counter=column_counter,
            row_counter=row_counter,
            annotations=dataset.annotations
        )
        self.set_dataset_identifier(name, ds.identifier)
        return DatasetClient(dataset=ds)
