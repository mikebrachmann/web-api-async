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

import json
import requests

from vizier.api.client.datastore.base import DatastoreClient
from vizier.api.client.resources.module import ModuleResource
from vizier.api.client.resources.workflow import WorkflowResource
from vizier.api.routes.datastore import DatastoreClientUrlFactory


class Notebook(object):
    """A notebook is a wrapper around a workflow instance for a particular
    project.
    """
    def __init__(self, project_id, workflow, urls):
        """Initialize the internal components.

        Parameters
        ----------
        project_id: string
            Unique project identifier
        workflow: vizier.api.client.resources.workflow.WorkflowResource
            Workflow that defines the notebook
        urls: vizier.api.routes.base.UrlFactory
            Factory for request urls
        """
        self.project_id = project_id
        self.workflow = workflow
        self.urls = urls

    def append_cell(self, command):
        """Append a new module to the notebook that executes te given command.

        Parameters
        ----------
        command: vizier.viztrail.command.ModuleCommand

        Returns
        -------
        ???
        """
        # Get append url and create request body
        url = self.workflow.links['workflow:append']
        data = {
            'packageId': command.package_id,
            'commandId': command.command_id,
            'arguments': command.arguments.to_list()
        }
        # Send request. Raise exception if status code indicates that the
        # request was not successful
        r = requests.post(url, json=data)
        r.raise_for_status()
        # The result is undefined by now. We may need to update the maintained
        # internal workflow state here.
        return json.loads(r.text)

    def cancel_exec(self):
        """Cancel exection of tasks for the notebook.

        Returns
        -------
        vizier.api.client.resources.workflow.WorkflowResource
        """
        url = self.workflow.links['workflow:cancel']
        r = requests.post(url)
        r.raise_for_status()
        # The result is the workflow handle
        return WorkflowResource.from_dict(json.loads(r.text))

    def delete_module(self, module_id):
        """Delete the notebook module with the given identifier.

        Returns
        -------
        list(vizier.api.client.resources.module.ModuleResource)
        """
        modules = list()
        for m in self.workflow.modules:
            if m.identifier == module_id:
                url = m.links['module:delete']
                r = requests.delete(url)
                r.raise_for_status()
                # The result is the workflow handle
                for obj in json.loads(r.text)['modules']:
                    modules.append(ModuleResource.from_dict(obj))
                return modules
            else:
                modules.append(m)

    def fetch_dataset(self, identifier):
        """Fetch handle for the dataset with the given identifier.

        Parameters
        ----------
        identifier: string
            Unique dataset identifier

        Returns
        -------
        vizier.datastore.base.DatasetHandle
        """
        # Use the remote datastore client to get the dataset handle
        return DatastoreClient(
            urls=DatastoreClientUrlFactory(
                urls=self.urls,
                project_id=self.project_id
            )
        ).get_dataset(identifier)

    def get_dataset(self, name):
        """Get descriptor for dataset with given name from the database state of
        the last module in the notebook workflow. If the dataset does not exist
        a ValueError exception is raised.

        Parameters
        ----------
        name: string
            User-provided dataset name

        Returns
        -------
        """
        if len(self.workflow.modules) > 0:
            module = self.workflow.modules[-1]
            if name in module.datasets:
                return self.workflow.datasets[module.datasets[name]]
        raise ValueError('unknown datasets \'' + name + '\'')

    def upload_file(self, filename):
        """Upload a file from local disk to notebooks filestore. Returns the
        identifier of the uploaded file.

        Parameters
        ----------
        filename: string
            Path to file on local disk

        Returns
        -------
        string
        """
        # Get the request Url and create the request body
        url = self.urls.upload_file(self.project_id)
        files = {'file': open(filename,'rb')}
        # Send request. The result is the handle for the uploaded file.
        r = requests.post(url, files=files)
        r.raise_for_status()
        # The result is the file identifier
        return json.loads(r.text)['id']
