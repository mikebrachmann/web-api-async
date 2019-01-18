"""Test the functionality to load projects for the container backend."""

import os
import shutil
import unittest

from vizier.config.app import AppConfig
from vizier.core.io.base import DefaultObjectStore
from vizier.engine.project.cache.container import ContainerProjectCache
from vizier.viztrail.base import PROPERTY_NAME
from vizier.viztrail.objectstore.repository import OSViztrailRepository


SERVER_DIR = './.tmp'
VIZTRAILS_DIR = SERVER_DIR + '/vt'


class TestContainerCache(unittest.TestCase):

    def setUp(self):
        """Create an instance of the default cache with an empty directory
        """
        if os.path.isdir(SERVER_DIR):
            shutil.rmtree(SERVER_DIR)
        os.makedirs(SERVER_DIR)

    def tearDown(self):
        """Remove the server directory."""
        if os.path.isdir(SERVER_DIR):
            shutil.rmtree(SERVER_DIR)

    def test_create_cache(self):
        """Test accessing and deleting projects for an empty repository."""
        viztrails = OSViztrailRepository(base_path=VIZTRAILS_DIR)
        vt1 = viztrails.create_viztrail(properties={PROPERTY_NAME: 'My Project'})
        vt2 = viztrails.create_viztrail(properties={PROPERTY_NAME: 'A Project'})
        filename = os.path.join(SERVER_DIR, 'container.json')
        DefaultObjectStore().write_object(
            object_path=filename,
            content=[
                {
                    'projectId': vt1.identifier,
                    'url': 'API1',
                    'port': 80,
                    'containerId': 'ID1'
                },
                {
                    'projectId': vt2.identifier,
                    'url': 'API2',
                    'port': 81,
                    'containerId': 'ID2'
                }
            ]
        )
        # Initialize the project cache
        viztrails = OSViztrailRepository(base_path=VIZTRAILS_DIR)
        projects = ContainerProjectCache(
            viztrails=viztrails,
            container_file=filename,
            config=AppConfig()
        )
        self.assertEquals(len(projects.list_projects()), 2)
        self.assertEquals(projects.get_project(vt1.identifier).container_api, 'API1')
        self.assertEquals(projects.get_project(vt2.identifier).container_api, 'API2')
        self.assertEquals(projects.get_project(vt1.identifier).container_id, 'ID1')
        self.assertEquals(projects.get_project(vt2.identifier).container_id, 'ID2')
        self.assertEquals(projects.get_project(vt1.identifier).port, 80)
        self.assertEquals(projects.get_project(vt2.identifier).port, 81)


if __name__ == '__main__':
    unittest.main()
