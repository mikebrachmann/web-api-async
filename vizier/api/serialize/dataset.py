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

"""This module contains helper methods for the webservice that are used to
serialize datasets.
"""

import vizier.api.serialize.labels as labels


def DATASET_DESCRIPTOR(dataset, name):
    """Dictionary serialization for a dataset descriptor.

    Parameters
    ----------
    dataset: vizier.datastore.dataset.DatasetDescriptor
        Dataset descriptor
    name : string
        User-defined dataset name

    Returns
    -------
    dict
    """
    return {
        labels.ID: dataset.identifier,
        labels.NAME: name,
        'columns': [
            {labels.ID: col.identifier, labels.NAME: col.name} for col in dataset.columns
        ],
        'rows': dataset.row_count
    }
