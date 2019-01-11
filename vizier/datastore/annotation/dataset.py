# Copyright (C) 2019 New York University,
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

"""Dataset maintain annotations for three type of resources: columns, rows, and
cells. Vizier does not reason about annotations at this point and therefore
there is only limited functionality provided to query annotations. The dataset
metadata object is barely a wrapper around three lists of resource annotations.
"""

import json
import os

from vizier.datastore.annotation.base import CellAnnotation, ColumnAnnotation, RowAnnotation


class DatasetMetadata(object):
    """Collection of annotations for a dataset object. For each of the three
    resource types a list of annotations is maintained.
    """
    def __init__(self, columns=None, rows=None, cells=None):
        """Initialize the metadata lists for the three different types of
        dataset resources that can be annotated.

        Parameters
        ----------
        columns: list(vizier.datastpre.annotation.base.ColumnAnnotation), optional
            Annotations for dataset columns
        rows: list(vizier.datastpre.annotation.base.RowAnnotation), optional
            Annotations for dataset rows
        cells: list(vizier.datastpre.annotation.base.CellAnnotation), optional
            Annotations for dataset cells
        """
        self.columns = columns if not columns is None else list()
        self.rows = rows if not rows is None else list()
        self.cells = cells if not cells is None else list()

    def add(self, key, value, column_id=None, row_id=None):
        """Add a new annotation for a dataset resource. The resource type is
        determined based on the column and row identifier values. At least one
        of them has to be not None. Otherwise, a ValueError is raised.

        Parameters
        ----------
        key: string
            Annotation key
        value: scalar
            Annotation value
        column_id: int, optional
            Unique column identifier
        row_id: int, optional
            Unique row identifier
        """
        if column_id is None and row_id is None:
            raise ValueError('must specify at least one dataset resource identifier')
        elif row_id is None:
            self.columns.append(
                ColumnAnnotation(key=key, value=value, column_id=column_id)
            )
        elif column_id is None:
            self.rows.append(RowAnnotation(key=key, value=value, row_id=row_id))
        else:
            self.cells.append(
                CellAnnotation(
                    key=key,
                    value=value,
                    column_id=column_id,
                    row_id=row_id
                )
            )

    def find_all(self, values, key):
        """Get the list of annotations that are associated with the given key.
        If no annotation is associated with the key an empty list is returned.

        Parameters
        ----------
        values: list(vizier.datastore.annotation.base.Annotation)
            List of annotations
        key: string
            Unique property key

        Returns
        -------
        list(vizier.datastore.annotation.base.Annotation)
        """
        result = list()
        for anno in values:
            if anno.key == key:
                result.append(anno)
        return result

    def filter(self, columns=None, rows=None):
        """Filter annotations to keep only those that reference existing
        resources. Returns a new dataset metadata object.

        Parameters
        ----------
        columns: list(int), optional
            List of dataset column identifier
        rows: list(int), optional
            List of dataset row identifier, optional

        Returns
        -------
        vizier.datastore.annotation.dataset.DatasetMetadata
        """
        result = DatasetMetadata(
            columns=self.columns if columns is None else list(),
            rows=self.rows if rows is None else list(),
            cells=self.cells if columns is None and rows is None else list()
        )
        if not columns is None:
            for anno in self.columns:
                if anno.column_id in columns:
                    result.columns.append(anno)
        if not rows is None:
            for anno in self.rows:
                if anno.row_id in rows:
                    result.rows.append(anno)
        if not columns is None or not rows is None:
            for anno in self.cells:
                if not columns is None and not anno.column_id in columns:
                    continue
                elif not rows is None and not anno.row_id in rows:
                    continue
                result.cells.append(anno)
        return result

    def find_one(self, values, key, raise_error_on_multi_value=True):
        """Get a single annotation that is associated with the given key. If no
        annotation is associated with the keyNone is returned. If multiple
        annotations are associated with the given key a ValueError is raised
        unless the raise_error_on_multi_value flag is False. In the latter case
        one of the found annotations is returned.

        Parameters
        ----------
        values: list(vizier.datastore.annotation.base.Annotation)
            List of annotations
        key: string
            Unique property key
        raise_error_on_multi_value: bool, optional
            Raises a ValueError if True and the given key is associated with
            multiple values.

        Returns
        -------
        vizier.datastore.annotation.base.Annotation
        """
        result = self.find_all(values=values, key=key)
        if len(result) == 0:
            return None
        elif len(result) == 1 or not raise_error_on_multi_value:
            return result[0]
        else:
            raise ValueError('multiple annotation values for \'' + str(key) + '\'')

    def for_cell(self, column_id, row_id):
        """Get list of annotations for the specified cell

        Parameters
        ----------
        column_id: int
            Unique column identifier
        row_id: int
            Unique row identifier

        Returns
        -------
        list(vizier.datastpre.annotation.base.CellAnnotation)
        """
        result = list()
        for anno in self.cells:
            if anno.column_id == column_id and anno.row_id == row_id:
                result.append(anno)
        return result

    def for_column(self, column_id):
        """Get object metadata set for a dataset column.

        Parameters
        ----------
        column_id: int
            Unique column identifier

        Returns
        -------
        list(vizier.datastpre.annotation.base.ColumnAnnotation)
        """
        result = list()
        for anno in self.columns:
            if anno.column_id == column_id:
                result.append(anno)
        return result

    def for_row(self, row_id):
        """Get object metadata set for a dataset row.

        Parameters
        ----------
        row_id: int
            Unique row identifier

        Returns
        -------
        list(vizier.datastpre.annotation.base.RowAnnotation)
        """
        result = list()
        for anno in self.rows:
            if anno.row_id == row_id:
                result.append(anno)
        return result

    @staticmethod
    def from_file(filename):
        """Read dataset annotations from file. Assumes that the file has been
        created using the default serialization (to_file), i.e., is in Json
        format.

        Parameters
        ----------
        filename: string
            Name of the file to read from

        Returns
        -------
        vizier.database.annotation.dataset.DatsetMetadata
        """
        # Return an empty annotation set if the file does not exist
        if not os.path.isfile(filename):
            return DatasetMetadata()
        with open(filename, 'r') as f:
            doc = json.loads(f.read())
        cells = None
        columns = None
        rows = None
        if 'cells' in doc:
            cells = [CellAnnotation.from_dict(a) for a in doc['cells']]
        if 'columns' in doc:
            columns = [ColumnAnnotation.from_dict(a) for a in doc['columns']]
        if 'rows' in doc:
            rows = [RowAnnotation.from_dict(a) for a in doc['rows']]
        return DatasetMetadata(
            cells=cells,
            columns=columns,
            rows=rows
        )

    def remove(self, key=None, value=None, column_id=None, row_id=None):
        """Remove annotations for a dataset resource. The resource type is
        determined based on the column and row identifier values. At least one
        of them has to be not None. Otherwise, a ValueError is raised.

        If the key and/or value are given they are used as additional filters.
        Otherwise, all annotations for the resource are removed.

        Parameters
        ----------
        key: string, optional
            Annotation key
        value: scalar, optional
            Annotation value
        column_id: int, optional
            Unique column identifier
        row_id: int, optional
            Unique row identifier
        """
        # Get the resource annotations list and the indices of the candidates
        # that match the resource identifier.
        candidates = list()
        if column_id is None and row_id is None:
            raise ValueError('must specify at least one dataset resource identifier')
        elif row_id is None:
            elements = self.columns
            for i in range(len(elements)):
                anno = elements[i]
                if anno.column_id == column_id:
                    candidates.append(i)
        elif column_id is None:
            elements = self.rows
            for i in range(len(elements)):
                anno = elements[i]
                if anno.row_id == row_id:
                    candidates.append(i)
        else:
            elements = self.cells
            for i in range(len(elements)):
                anno = elements[i]
                if anno.column_id == column_id and anno.row_id == row_id:
                    candidates.append(i)
        # Get indices of all annotations that are being deleted. Use key and
        # value as filter if given. Otherwise, remove all elements in the list
        del_idx_list = list()
        if key is None and value is None:
            del_idx_list = candidates
        elif key is None:
            for i in candidates:
                if elements[i].value == value:
                    del_idx_list.append(i)
        elif value is None:
            for i in candidates:
                if elements[i].key == key:
                    del_idx_list.append(i)
        else:
            for i in candidates:
                el = elements[i]
                if el.key == key and el.value == value:
                    del_idx_list.append(i)
        # Remove all elements at the given index positions. Make sure to adjust
        # indices as elements are deleted.
        for j in range(len(del_idx_list)):
            i = del_idx_list[j] - j
            del elements[i]

    def to_file(self, filename):
        """Write current annotations to file in default file format. The default
        serializartion format is Json.

        Parameters
        ----------
        filename: string
            Name of the file to write
        """
        doc = dict()
        if len(self.cells) > 0:
            doc['cells'] = [a.to_dict() for a in self.cells]
        if len(self.columns) > 0:
            doc['columns'] = [a.to_dict() for a in self.columns]
        if len(self.rows) > 0:
            doc['rows'] = [a.to_dict() for a in self.rows]
        with open(filename, 'w') as f:
            json.dump(doc, f)
