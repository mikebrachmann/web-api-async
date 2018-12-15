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

"""Implementation of commands that interact with the Api's viztrails
repository.
"""

from vizier.api.client.base import KEY_DEFAULT_BRANCH, KEY_DEFAULT_PROJECT
from vizier.api.client.base import MSG_NO_DEFAULT_BRANCH, MSG_NO_DEFAULT_PROJECT
from vizier.api.client.cli.command import Command
from vizier.core.timestamp import utc_to_local
from vizier.viztrail.base import PROPERTY_NAME


"""Default timestamp format."""
TIME_FORMAT = '%d-%m-%Y %H:%M:%S'


class ViztrailsCommands(Command):
    """"Collection of commands that interact with the viztrails repository."""
    def __init__(self, api):
        """Initialize the viztrails API.

        Parameters
        ----------
        api: vizier.api.client.base.VizierApiClient
            Vizier API client
        """
        self.api = api
        self.default_project = api.default_project
        self.default_branch = api.default_branch

    def create_branch(self, name):
        """Create a new branch in the default project."""
        if self.default_project is None:
            print MSG_NO_DEFAULT_PROJECT
            return True
        branch = self.viztrails.create_branch(
            project_id=self.default_project.identifier,
            properties={PROPERTY_NAME: name}
        )
        print 'Branch ' + name + ' created with identifier ' + branch.identifier
        return True

    def create_project(self, name):
        """Create a new project with given name."""
        vt = self.viztrails.create_project(
            properties={PROPERTY_NAME: name}
        )
        print 'Project ' + name + ' created with identifier ' + vt.identifier
        return True

    def delete_branch(self, branch_id):
        """Delete branch with given idnetifier from default project."""
        if self.default_project is None:
            print MSG_NO_DEFAULT_PROJECT
            return True
        result = self.viztrails.delete_branch(
            project_id=self.default_project.identifier,
            branch_id=branch_id
        )
        if result:
            print 'Branch deleted'
        else:
            print 'Unknown branch ' + branch_id
        return True

    def delete_project(self, project_id):
        """Delete project with given idnetifier."""
        result = self.viztrails.delete_project(project_id=project_id)
        if result:
            if not self.default_project is None:
                if self.default_project.identifier == project_id:
                    self.default_project = None
                    self.defaults.delete(KEY_DEFAULT_PROJECT)
            print 'Project deleted'
        else:
            print 'Unknown project ' + project_id
        return True

    def eval(self, tokens):
        """Currently supports the following commands:

        list projects: Print a listing of all viztrails in the repository

        Parameters
        ----------
        tokans: list(string)
            List of tokens in the command line
        """
        if len(tokens) == 2:
            # list branches
            if tokens[0] == 'list' and tokens[1] == 'branches':
                return self.list_branches()
            # list projects
            elif tokens[0] == 'list' and tokens[1] == 'projects':
                return self.list_projects()
            # show history
            elif tokens[0] == 'show' and tokens[1] in ['history', 'notebooks']:
                return self.list_workflows()
            # show workflow
            elif tokens[0] == 'show' and tokens[1] == 'notebook':
                return self.show_notebook()
        elif len(tokens) == 3:
            # create branch <name>
            if tokens[0] == 'create' and tokens[1] == 'branch':
                return self.create_branch(tokens[2])
            # create project <name>
            elif tokens[0] == 'create' and tokens[1] == 'project':
                return self.create_project(tokens[2])
            # delete branch <branch-id>
            elif tokens[0] == 'delete' and tokens[1] == 'branch':
                return self.delete_branch(tokens[2])
            # delete project <project-id>
            elif tokens[0] == 'delete' and tokens[1] == 'project':
                return self.delete_project(tokens[2])
            # rename branch <name>
            elif tokens[0] == 'rename' and tokens[1] == 'branch':
                return self.rename_branch(tokens[2])
            # rename project <name>
            elif tokens[0] == 'rename' and tokens[1] == 'project':
                return self.rename_project(tokens[2])
            # show workflow <workflow-id>
            elif tokens[0] == 'show' and tokens[1] == 'notebook':
                return self.show_notebook(workflow_id=tokens[2])
            # show workflow <workflow-id>
            elif tokens[0] == 'run' and tokens[1] == 'python':
                return self.run_python(code=tokens[2])
        return False

    def help(self):
        """Print help statement."""
        print '\nProjects'
        print '  create branch <name>'
        print '  create project <name>'
        print '  delete branch <branch-id>'
        print '  delete project <project-id>'
        print '  list branches'
        print '  list projects'
        print '  rename branch <name>'
        print '  rename project <name>'
        print '  show [history | notebooks]'
        print '  show notebook {<workflow-id>}'
        print '  run python [<file> | <script-code>]'

    def list_branches(self):
        """Print listing of branches for default project in tabular format."""
        if self.default_project is None:
            print MSG_NO_DEFAULT_PROJECT
            return True
        branches = self.api.list_branches(self.default_project)
        rows = list()
        rows.append(['Identifier', 'Name', 'Created at', 'Last modified'])
        for branch in branches:
            rows.append([
                branch.identifier,
                branch.name,
                ts(branch.created_at),
                ts(branch.last_modified_at)
            ])
        print
        self.output(rows)
        print '\n' + str(len(branches)) + ' branch(es)\n'
        return True

    def list_projects(self):
        """Print listing of active projects in tabular format."""
        projects = self.api.list_projects()
        rows = list()
        rows.append(['Identifier', 'Name', 'Created at', 'Last modified'])
        for project in projects:
            rows.append([
                project.identifier,
                project.name,
                ts(project.created_at),
                ts(project.last_modified_at)
            ])
        print
        self.output(rows)
        print '\n' + str(len(projects)) + ' project(s)\n'
        return True

    def list_workflows(self):
        """Print listing of workflows in the history of the default branch in
        tabular format.
        """
        if self.default_project is None:
            print MSG_NO_DEFAULT_PROJECT
            return True
        if self.default_branch is None:
            print MSG_NO_DEFAULT_BRANCH
            return True
        branch = self.api.get_branch(
            project_id=self.default_project,
            branch_id=self.default_branch
        )
        rows = list()
        rows.append(['Identifier', 'Action', 'Command', 'Created at'])
        for workflow in branch.workflows:
            rows.append([
                workflow.identifier,
                workflow.action.upper(),
                workflow.command,
                ts(workflow.created_at)
            ])
        print
        self.output(rows)
        print '\n' + str(len(branch.workflows)) + ' workflow(s)\n'
        return True

    def rename_branch(self, name):
        """Rename the default branch."""
        self.viztrails.update_branch_properties(
            project_id=self.default_project.identifier,
            branch_id=self.default_branch.identifier,
            properties={PROPERTY_NAME: name}
        )
        print 'Branch renamed to ' + name
        return True

    def rename_project(self, name):
        """Rename the default project."""
        if self.default_project is None:
            print MSG_NO_DEFAULT_PROJECT
            return True
        self.api.update_project(
            project_id=self.default_project,
            properties={PROPERTY_NAME: name}
        )
        print 'Project renamed to ' + name
        return True

    def show_notebook(self, workflow_id=None):
        """List all modules for a given workflow. If the workflow identifier is
        not given the branch head is used as the workflow.
        """
        if self.default_project is None:
            print MSG_NO_DEFAULT_PROJECT
            return True
        if self.default_branch is None:
            print MSG_NO_DEFAULT_BRANCH
            return True
        workflow = self.api.get_workflow(
            project_id=self.default_project,
            branch_id=self.default_branch,
            workflow_id=workflow_id
        )
        print 'Workflow ' + workflow.identifier + ' (created at ' + ts(workflow.created_at) + ')'
        for i in range(len(workflow.modules)):
            module = workflow.modules[i]
            print '\n[' + str(i+1) + '] (' + module.state.upper() + ') ' + module.identifier
            timestamps = 'Created @ ' + ts(module.timestamp.created_at)
            if not module.timestamp.started_at is None:
                timestamps += ', Started @ ' + ts(module.timestamp.started_at)
            if not module.timestamp.finished_at is None:
                timestamps += ', Finished @ ' + ts(module.timestamp.finished_at)
            print timestamps
            print '--'
            print module.external_form
            if len(module.outputs) > 0:
                print '--'
                for line in module.outputs:
                    print line
            print '.'
        return True


# ------------------------------------------------------------------------------
# Helper Methods
# ------------------------------------------------------------------------------

def ts(timestamp):
    """Convert datatime timestamp to string."""
    return  utc_to_local(timestamp).strftime(TIME_FORMAT)