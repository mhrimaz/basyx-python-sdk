# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import os
import unittest

import aas.compliance_tool.compliance_check_xml as compliance_tool
from aas.compliance_tool.state_manager import ComplianceToolStateManager, Status


class ComplianceToolXmlTest(unittest.TestCase):
    def test_check_schema(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)
        file_path_1 = os.path.join(script_dir, 'files/test_not_found.xml')
        compliance_tool.check_schema(file_path_1, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[2].status)
        self.assertIn("No such file or directory", manager.format_step(0, verbose_level=1))

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_missing_submodels.xml')
        compliance_tool.check_schema(file_path_3, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_empty.xml')
        compliance_tool.check_schema(file_path_4, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)

        manager.steps = []
        file_path_5 = os.path.join(script_dir, 'files/test_demo_full_example.xml')
        compliance_tool.check_schema(file_path_5, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)

    def test_check_deserialization(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_found.xml')
        compliance_tool.check_deserialization(file_path_1, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.FAILED, manager.steps[0].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[1].status)
        self.assertIn("No such file or directory", manager.format_step(0, verbose_level=1))

        manager.steps = []
        file_path_2 = os.path.join(script_dir, 'files/test_not_deserializable_aas.xml')
        compliance_tool.check_deserialization(file_path_2, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("child of aas:assetAdministrationShells", manager.format_step(1, verbose_level=1))
        self.assertIn("doesn't match the expected tag aas:assetAdministrationShell",
                      manager.format_step(1, verbose_level=1))

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_deserializable_aas_warning.xml')
        compliance_tool.check_deserialization(file_path_3, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertIn("ValueError: A revision requires a version", manager.format_step(1, verbose_level=1))

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_empty.xml')
        compliance_tool.check_deserialization(file_path_4, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)

        manager.steps = []
        file_path_4 = os.path.join(script_dir, 'files/test_empty.xml')
        compliance_tool.check_deserialization(file_path_4, manager)
        self.assertEqual(2, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)

    def test_check_aas_example(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_2 = os.path.join(script_dir, 'files/test_demo_full_example.xml')
        compliance_tool.check_aas_example(file_path_2, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)

        manager.steps = []
        file_path_1 = os.path.join(script_dir, 'files/test_not_deserializable_aas.xml')
        compliance_tool.check_aas_example(file_path_1, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[2].status)
        self.assertIn("child of aas:assetAdministrationShells", manager.format_step(1, verbose_level=1))
        self.assertIn("doesn't match the expected tag aas:assetAdministrationShell",
                      manager.format_step(1, verbose_level=1))

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.xml')
        compliance_tool.check_aas_example(file_path_3, manager)
        self.assertEqual(3, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.FAILED, manager.steps[2].status)
        self.assertIn('Asset administration shell AssetAdministrationShell[Identifier(IRI=https://acplt.org/'
                      'Test_AssetAdministrationShell)] must exist in given asset administrationshell list',
                      manager.format_step(2, verbose_level=1))

    def test_check_xml_files_equivalence(self) -> None:
        manager = ComplianceToolStateManager()
        script_dir = os.path.dirname(__file__)

        file_path_1 = os.path.join(script_dir, 'files/test_not_deserializable_aas.xml')
        file_path_2 = os.path.join(script_dir, 'files/test_empty.xml')
        compliance_tool.check_xml_files_equivalence(file_path_1, file_path_2, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.FAILED, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

        manager.steps = []
        compliance_tool.check_xml_files_equivalence(file_path_2, file_path_1, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.FAILED, manager.steps[3].status)
        self.assertEqual(Status.NOT_EXECUTED, manager.steps[4].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.xml')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example.xml')
        compliance_tool.check_xml_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.SUCCESS, manager.steps[4].status)

        manager.steps = []
        file_path_3 = os.path.join(script_dir, 'files/test_demo_full_example.xml')
        file_path_4 = os.path.join(script_dir, 'files/test_demo_full_example_wrong_attribute.xml')
        compliance_tool.check_xml_files_equivalence(file_path_3, file_path_4, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)

        manager.steps = []
        compliance_tool.check_xml_files_equivalence(file_path_4, file_path_3, manager)
        self.assertEqual(5, len(manager.steps))
        self.assertEqual(Status.SUCCESS, manager.steps[0].status)
        self.assertEqual(Status.SUCCESS, manager.steps[1].status)
        self.assertEqual(Status.SUCCESS, manager.steps[2].status)
        self.assertEqual(Status.SUCCESS, manager.steps[3].status)
        self.assertEqual(Status.FAILED, manager.steps[4].status)
        self.assertIn('Asset administration shell AssetAdministrationShell[Identifier(IRI=https://acplt.org/'
                      'Test_AssetAdministrationShell)] must exist in given asset administrationshell list',
                      manager.format_step(4, verbose_level=1))
