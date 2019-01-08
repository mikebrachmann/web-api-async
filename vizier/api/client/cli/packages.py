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

"""Command line interface helper methods for parsing notebook cell commands."""

import os

from vizier.core.util import cast
from vizier.engine.packages.base import FILE_ID, FILE_NAME, FILE_URI

import vizier.api.client.command.pycell as pycell
import vizier.api.client.command.vizual as vizual


def get_script(script):
    """Return script code. If the script argument refers to an existing file on
    disk the file content is returned. Otherwise, the script value itself is
    assumed to contain the script code.

    Parameters
    ----------
    script: string
        Script code or reference to file on local disk

    Returns
    -------
    string
    """
    if os.path.isfile(script):
        with open(script, 'r') as f:
            return f.read()
    else:
        return script


def parse_command(tokens, notebook):
    """Parse command line tokens that represent a notebook cell command. The
    command is parse againts the given notebook state. Returns the module
    command or None if the token list does not specify a valid command.

    The function has side effects in case a dataset is loaded from local file.
    In this case the file is uploaded before the command object is returned.

    Parameters
    ----------
    tokens: list(string)
        Command line tokens specifying the command
    notebook: vizier.api.client.resources.notebook.Notebook
        Current notebook state

    Returns
    -------
    vizier.engine.module.command.ModuleCommand
    """
    if len(tokens) == 2:
        if tokens[0] == 'python':
            return pycell.python_cell(source=get_script(tokens[1]))
    elif len(tokens) == 5:
        if tokens[0] == 'load' and tokens[2] == 'from' and tokens[3] == 'file':
            # load <name> from file <file>
            filename = tokens[4]
            file_id = notebook.upload_file(filename=filename)
            return vizual.load_dataset(
                dataset_name=tokens[1],
                file={
                    FILE_ID: file_id,
                    FILE_NAME: os.path.basename(filename)
                }
            )
        elif tokens[0] == 'load' and tokens[2] == 'from' and tokens[3] == 'url':
            return vizual.load_dataset(
                dataset_name=tokens[1],
                file={FILE_URI: tokens[4]}
            )
        elif tokens[0] == 'update':
            # update <dataset-name> <column-name> <row-index>{ <value>}\
            dataset_name = tokens[1].lower()
            # Get the referenced dataset and column from the current notebook
            # state
            ds = notebook.get_dataset(dataset_name)
            col = ds.get_column(tokens[2])
            return vizual.update_cell(
                dataset_name=dataset_name,
                column=col.identifier,
                row=int(tokens[3]),
                value=cast(tokens[4])
            )

    return None


def print_commands():
    """Print command syntax listing for supported commands."""
    print '  load <name> from file <file>'
    print '  load <name> from url <url>'
    print '  python [<script> | <file>]'
    print '  update <dataset-name> <column-name> <row-index>{ <value>}'
