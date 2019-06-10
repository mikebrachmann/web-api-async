# Copyright (C) 2017-2019 New York University,
#                         University at Buffalo,
#                         Illinois Institute of Technology.
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

"""Classes to manipulate vizier datasets from within the Python workflow cell.
"""

from vizier.datastore.dataset import DatasetColumn, DatasetRow, get_column_index
from vizier.datastore.annotation.dataset import DatasetMetadata
from bokeh.models.sources import ColumnDataSource

class DatasetClient(object):
    """Client to interact with a Vizier dataset from within a Python workflow
    cell. Provides access to the columns and rows. Allows to insert and delete
    rows, and to update cell values.

    Attributes
    ----------
    columns: list(vizier.datastore.base.DatasetColumns)
        List of dataset columns
    identifier : string
        Unique dataset identifier
    rows : list(vizier.datastore.client.MutableDatasetRow)
        List of rows in the dataset
    """
    def __init__(self, dataset=None):
        """Initialize the client for a given dataset.

        Raises ValueError if dataset columns or rows do not have unique
        identifiers.

        Parameters
        ----------
        dataset: vizier.datastore.base.DatasetHandle, optional
            Handle to the dataset for which this is a client. If None this is a
            new dataset.
        """
        self.dataset = dataset
        if not dataset is None:
            self.identifier = dataset.identifier
            self.columns = dataset.columns
            # Delay fetching rows and dataset annotations for now
            self._annotations = None
            self._rows = None
        else:
            self.identifier = None
            self.columns = list()
            self._annotations = DatasetMetadata()
            self._rows = list()

    @property
    def annotations(self):
        """Get all dataset annotations.

        Returns
        -------
        vizier.datastore.annotation.dataset.DatasetMetadata
        """
        if self._annotations is None:
            self._annotations = DatasetMetadata.from_list(
                self.dataset.get_annotations()
            )
        return self._annotations

    def column_index(self, column_id):
        """Get position of a given column in the dataset schema. The given
        column identifier could either be of type int (i.e., the index position
        of the column), or a string (either the column name or column label). If
        column_id is of type string it is first assumed to be a column name.
        Only if no column matches the column name or if multiple columns with
        the given name exist will the value of column_id be interpreted as a
        label.

        Raises ValueError if column_id does not reference an existing column in
        the dataset schema.

        Parameters
        ----------
        column_id : int or string
            Column index, name, or label

        Returns
        -------
        int
        """
        return get_column_index(self.columns, column_id)

    def delete_column(self, name):
        """Delete column from the dataset.

        Parameters
        ----------
        name: string or int
            Name or index position of the new column
        """
        # It is important to fetch the rows before the column is deleted.
        # Otherwise, the list of returned values per row will be missing the
        # value for the deleted columns (for Mimir datasets).
        ds_rows = self.rows
        col_index = self.column_index(name)
        # Delete column from schema
        del self.columns[col_index]
        # Delete all value for the deleted column
        for row in ds_rows:
            del row.values[col_index]

    def get_column(self, name):
        """Get the fist column in the dataset schema that matches the given
        name. If no column matches the given name None is returned.

        Parameters
        ----------
        name: string
            Column name

        Returns
        -------
        vizier.datastore.dataset.DatasetColumn
        """
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def insert_column(self, name, position=None):
        """Add a new column to the dataset schema.

        Parameters
        ----------
        name: string
            Name of the new column
        position: int, optional
            Position in the dataset schema where new column is inserted. If
            None, the column is appended to the list of dataset columns.

        Returns
        DatasetColumn
        """
        column = DatasetColumn(name=name)
        self.columns = list(self.columns)
        if not position is None:
            self.columns.insert(position, column)
            # Add a null value to each row for the new column
            for row in self.rows:
                row.values.insert(position, None)
        else:
            self.columns.append(column)
            # Add a null value to each row for the new column
            for row in self.rows:
                row.values.append(None)
        return column

    def insert_row(self, values=None, position=None):
        """Add a new row to the dataset. Expects a list of string values, one
        for each of the columns.

        Raises ValueError if the length of the values list does not match the
        number of columns in the dataset.

        Parameters
        ----------
        values: list(string), optional
            List of column values. Use empty string if no values are given
        position: int, optional
            Position where row is inserted. If None, the new row is appended to
            the list of dataset rows.

        Returns
        -------
        DatasetRow
        """
        # Ensure that there is exactly one value for each column in the dataset
        if not values is None:
            if len(values) != len(self.columns):
                raise ValueError('invalid number of values for dataset schema')
            row = MutableDatasetRow(
                values=[str(v) for v in values],
                dataset=self
            )
        else:
            # All values in the new row are set to the empty string by default.
            row = MutableDatasetRow(
                values = [None] * len(self.columns),
                dataset=self
            )
        if not position is None:
            self.rows.insert(position, row)
        else:
            self.rows.append(row)
        return row

    def get_cell(self, column, row):
        """Get dataset value for specified cell.

        Raises ValueError if [column, row] does not reference an existing cell.

        Parameters
        ----------
        column : int or string
            Column identifier
        row : int
            Row index

        Returns
        -------
        string
        """
        if row < 0 or row > len(self.rows):
            raise ValueError('unknown row \'' + str(row) + '\'')
        return self.rows[row].get_value(column)

    def move_column(self, name, position):
        """Move a column within a given dataset.

        Raises ValueError if no dataset with given identifier exists or if the
        specified column is unknown or the target position invalid.

        Parameters
        ----------
        name: string or int
            Name or index position of the new column
        position: int
            Target position for the column
        """
        # Get dataset. Raise exception if dataset is unknown
        # Make sure that position is a valid column index in the new dataset
        if position < 0 or position > len(self.columns):
            raise ValueError('invalid target position \'' + str(position) + '\'')
        # Get index position of column that is being moved
        source_idx = self.column_index(name)
        # No need to do anything if source position equals target position
        if source_idx != position:
            self.columns.insert(position, self.columns.pop(source_idx))
            for row in self.rows:
                row.values.insert(position, row.values.pop(source_idx))

    @property
    def rows(self):
        """Fetch rows on demand.

        Returns
        -------
        list(vizier.datastore.client.MutableDatasetRow)
        """
        if self._rows is None:
            self._rows = list()
            for row in self.dataset.fetch_rows():
                # Create mutable dataset row and set reference to this dataset
                # for updates
                self._rows.append(
                    MutableDatasetRow(
                        identifier=row.identifier,
                        values=row.values,
                        dataset=self
                    )
                )
        return self._rows

    def to_bokeh(self, columns = None):
        """Convert the dataset to a bokeh ColumnDataSource

        Parameters
        ----------
        columns: list(string or int) (optional)
            The columns to include.  (default: All columns)

        Returns
        -------
        bokeh.models.sources.ColumnDataSource  
        """

        if columns == None:
            columns = self.columns
        return ColumnDataSource(dict([
            (
                column.name, 
                [ row.get_value(column.identifier if column.identifier >= 0 else column.name) for row in self.rows ]
            )
            for column in self.columns
        ]))


class MutableDatasetRow(DatasetRow):
    """Row in a Vizier DB dataset.

    Attributes
    ----------
    identifier: int
        Unique row identifier
    values : list(string)
        List of column values in the row
    """
    def __init__(self, identifier=None, values=None, dataset=None):
        """Initialize the row object.

        Parameters
        ----------
        identifier: int, optional
            Unique row identifier
        values : list(string), optional
            List of column values in the row
        dataset : vizier.datastore.client.DatasetClient, optional
            Reference to dataset that contains the row
        """
        super(MutableDatasetRow, self).__init__(
            identifier=identifier,
            values=values
        )
        self.dataset = dataset

    def annotations(self, column):
        """Get annotation object for given row cell.

        Parameters
        ----------
        column : int or string
            Column index, name, or label

        Returns
        -------
        vizier.engine.packages.pycell.client.ObjectMetadataSet
        """
        col_index = self.dataset.column_index(column)
        column_id = self.dataset.columns[col_index].identifier
        return ObjectMetadataSet(
            annotations=self.dataset.annotations.for_cell(
                column_id=column_id,
                row_id=self.identifier
            )
        )

    def get_value(self, column):
        """Get the row value for the given column.

        Parameters
        ----------
        column : int or string
            Column index, name, or label

        Returns
        -------
        string
        """
        col_index = self.dataset.column_index(column)
        return self.values[col_index]

    def set_value(self, column, value, clear_annotations=False):
        """Set the row value for the given column.

        Parameters
        ----------
        column : int or string
            Column index, name, or label
        value : string
            New cell value
        keep_annotations: bool, optional
            Flag indicating whether to keep or clear the annotations that are
            associated with this cell
        """
        col_index = self.dataset.column_index(column)
        self.values[col_index] = value
        if clear_annotations:
            self.dataset.annotations.clear_cell(
                column_id=self.dataset.columns[col_index].identifier,
                row_id=self.identifier
            )


class ObjectMetadataSet(object):
    """Query annotations for a dataset resource."""
    def __init__(self, annotations):
        """initialize the list of resource annotations.

        Parameters
        ----------
        annotations: list(vizier.datastore.annotation.base.DatasetAnnotation)
            List of resource annotations
        """
        self.annotations = annotations

    def contains(self, key):
        """Test if an annotation with given key exists for the resource.

        Parameters
        ----------
        key: string
            Annotation key

        Returns
        -------
        bool
        """
        return not self.find_one(key) is None

    def count(self):
        """Number of annotations for this resource.

        Returns
        -------
        int
        """
        return len(self.annotations)

    def find_all(self, key):
        """Get a list with all annotations that have a given key. Returns an
        empty list if no annotation with the given key exists.

        Parameters
        ----------
        key: string
            Key value for new annotation

        Returns
        -------
        list(vizier.datastore.annotation.base.DatasetAnnotation)
        """
        result = list()
        for anno in self.annotations:
            if anno.key == key:
                result.append(anno)
        return result

    def find_one(self, key):
        """Find the first annotation with given key. Returns None if no
        annotation with the given key exists.

        Parameters
        ----------
        key: string
            Key value for new annotation

        Returns
        -------
        vizier.datastore.annotation.base.DatasetAnnotation
        """
        for anno in self.annotations:
            if anno.key == key:
                return anno

    def keys(self):
        """List of existing annotation keys for the object.

        Returns
        -------
        list(string)
        """
        result = set()
        for anno in self.annotations:
            result.add(anno.key)
        return list(result)
