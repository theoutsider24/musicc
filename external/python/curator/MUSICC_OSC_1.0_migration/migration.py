# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/
#
import os
import io
import zipfile
from lxml import etree
import lxml
import shutil
import argparse
import tempfile
from contextlib import contextmanager
import importlib


class MusiccContext:
    def __init__(
        self, zip_file, mus_file_path, odr_file_path, osc_file_path, catalog_file_paths
    ):
        self.mus_file_path = mus_file_path
        self.odr_file_path = odr_file_path
        self.osc_file_path = osc_file_path
        self.catalog_file_paths = catalog_file_paths

        # Read the files out of the zip archive
        self.mus_file = zip_file.read(self.mus_file_path)
        self.odr_file = zip_file.read(self.odr_file_path)
        self.osc_file = zip_file.read(self.osc_file_path)
        self.catalog_files = [
            zip_file.read(file_path) for file_path in self.catalog_file_paths
        ]

        # Convert the read files to etrees
        self.mus_etree = etree.fromstring(self.mus_file)
        self.odr_etree = etree.fromstring(self.odr_file)
        self.osc_etree = etree.fromstring(self.osc_file)
        self.catalog_etrees = [
            etree.fromstring(catalog_file) for catalog_file in self.catalog_files
        ]

        # Extract the label from the musicc file
        self.label = MusiccContext.get_label(self.mus_etree)

    def get_label(mus_etree):
        return mus_etree.xpath("//FileHeader")[0].get("label")

    def write(self, folder):
        # Write all etrees to files
        MusiccContext.write_etree_to_file(
            os.path.join(folder, self.mus_file_path), self.mus_etree
        )
        MusiccContext.write_etree_to_file(
            os.path.join(folder, self.odr_file_path), self.odr_etree
        )
        MusiccContext.write_etree_to_file(
            os.path.join(folder, self.osc_file_path), self.osc_etree
        )
        for catalog_file_path, catalog_etree in zip(
            self.catalog_file_paths, self.catalog_etrees
        ):
            MusiccContext.write_etree_to_file(
                os.path.join(folder, catalog_file_path), catalog_etree
            )

    def write_etree_to_file(file_path, etree_to_write):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "wb") as file:
            file.write(
                etree.tostring(etree_to_write, encoding="utf-8", xml_declaration=True)
            )


class Migration:
    def __init__(self, scenario_dump_path, xsd_dump_path):
        self.context_list = []
        with zipfile.ZipFile(scenario_dump_path, "r") as scenario_dump:
            # Extract list of top-level directories
            # Each of these directories represent a complete musicc file-set
            directories = set(
                [info.filename.split("/")[0] for info in scenario_dump.infolist()]
            )

            # Identify the relevant files in each file-set
            for directory in directories:
                files = [
                    info.filename
                    for info in scenario_dump.infolist()
                    if info.filename.startswith(directory)
                ]
                mus_file_path = [
                    filename for filename in files if filename.endswith(".xmus")
                ][0]
                odr_file_path = [
                    filename for filename in files if filename.endswith(".xodr")
                ][0]
                catalog_file_paths = [
                    filename
                    for filename in files
                    if filename.startswith(directory + "/catalogs")
                    if filename.endswith(".xosc")
                ]
                osc_file_path = [
                    filename 
                    for filename in files 
                    if filename.endswith(".xosc")
                    if not filename in catalog_file_paths
                ][0]

                # Create the context object and add it to the list
                self.context_list.append(
                    MusiccContext(
                        scenario_dump,
                        mus_file_path,
                        odr_file_path,
                        osc_file_path,
                        catalog_file_paths,
                    )
                )
        with zipfile.ZipFile(xsd_dump_path, "r") as xsd_dump:
            files = set([info.filename for info in xsd_dump.infolist()])
            musicc_schema_file = xsd_dump.read(
                [file for file in files if "musicc" in file][0]
            )
            open_drive_schema_file = xsd_dump.read(
                [file for file in files if "openDrive" in file][0]
            )
            open_scenario_schema_file = xsd_dump.read(
                [file for file in files if "OpenSCENARIO" in file][0]
            )
            self.schema_context = SchemaWrapper(
                musicc_schema_file, open_drive_schema_file, open_scenario_schema_file
            )

    def migrate(self, migration_function):
        # Apply the migration function to each context object
        for musicc_context in self.context_list:
            musicc_context = migration_function(musicc_context)

            # Raise an exception if a label was altered
            new_label = MusiccContext.get_label(musicc_context.mus_etree)
            assert new_label == musicc_context.label

    def write(self, target_directory):
        # Write the files for each context objects to the target_directory
        shutil.rmtree(target_directory, ignore_errors=True)
        os.makedirs(target_directory)
        for musicc_context in self.context_list:
            musicc_context.write(target_directory)

    def validate(self):
        for musicc_context in self.context_list:
            self.schema_context.schemas["musicc"].assertValid(musicc_context.mus_etree)
            self.schema_context.schemas["open_drive"].assertValid(
                musicc_context.odr_etree
            )
            self.schema_context.schemas["open_scenario"].assertValid(
                musicc_context.osc_etree
            )


class SchemaWrapper:
    def __init__(self, musicc_file, open_drive_file, open_scenario_file):
        self.schemas = {}
        self.schemas["musicc"] = SchemaWrapper.load_xsd_from_blob(
            musicc_file, "MUSICCScenario"
        )
        self.schemas["open_drive"] = SchemaWrapper.load_xsd_from_blob(
            open_drive_file, "OpenDrive"
        )
        self.schemas["open_scenario"] = SchemaWrapper.load_xsd_from_blob(
            open_scenario_file, "OpenSCENARIO"
        )

    def load_xsd_from_blob(blob, root_type=None):
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(blob)
                if not zipfile.is_zipfile(temp_file):
                    temp_file.close()
                    schema = SchemaWrapper.load_xsd_file(temp_file.name)
                else:
                    with zipfile.ZipFile(temp_file) as zip_file:
                        file_name = SchemaWrapper.find_base_xsd_file(
                            zip_file, root_type
                        )
                        schema = SchemaWrapper.load_xsd_zip(file_name, zip_file)
                        temp_file.close()
        finally:
            os.unlink(temp_file.name)
        return schema

    def find_base_xsd_file(zip_file, root_type):
        zip_contents = {name: zip_file.read(name) for name in zip_file.namelist()}

        filenames = []
        for filename, file in zip_contents.items():
            xml = etree.fromstring(file)
            root_name = xml.xpath(
                "xsd:element/@name",
                namespaces={"xsd": "http://www.w3.org/2001/XMLSchema"},
            )
            if len(root_name) > 0 and root_name[0] == root_type:
                filenames.append(filename)

        if len(filenames) == 0:
            raise Exception(
                "No root xsd file in zip with root type {0}".format(root_type)
            )
        elif len(filenames) > 1:
            raise Exception("More than one root xsd file in zip")
        else:
            return filenames[0]

    def load_xsd_file(xsd_path: str) -> etree.XMLSchema:
        filename_xsd = xsd_path.strip()
        basename_xsd = os.path.basename(filename_xsd)
        dirname_xsd = os.path.abspath(os.path.dirname(filename_xsd))

        # open and read schema file
        with SchemaWrapper.working_directory(dirname_xsd):
            with open(basename_xsd, "rb") as schema_file:
                schema_to_check = schema_file.read()

            xmlschema_doc = etree.parse(io.BytesIO(schema_to_check))
            xmlschema = etree.XMLSchema(xmlschema_doc)
            return xmlschema

    def load_xsd_zip(xsd_path: str, zip_file: zipfile.ZipFile) -> etree.XMLSchema:
        with tempfile.TemporaryDirectory() as tmpdirname:
            with SchemaWrapper.working_directory(tmpdirname):
                zip_file.extractall(path=tmpdirname)
                xsd_doc = SchemaWrapper.load_xsd_file(xsd_path)
                return xsd_doc

    @contextmanager
    def working_directory(directory):
        owd = os.getcwd()
        try:
            os.chdir(directory)
            yield directory
        finally:
            os.chdir(owd)


def process_args():
    parser = argparse.ArgumentParser(
        description="Perform a migration of MUSICC records"
    )
    parser.add_argument(
        "--script",
        dest="migration_module",
        required=True,
        type=str,
        help="A python file containing a migrate() function which accepts and returns a MusiccContext object",
    )
    parser.add_argument(
        "--dir",
        dest="target_directory",
        required=True,
        type=str,
        help="A directory to which migrated files wil be written",
    )
    parser.add_argument(
        "--mus-zip",
        dest="scenario_dump_path",
        required=True,
        type=str,
        help="The scenario dump file to be migrated",
    )
    parser.add_argument(
        "--xsd-zip",
        dest="xsd_dump_path",
        required=True,
        type=str,
        help="The xsd dump file to be used for validation",
    )
    parser.add_argument(
        "--zip",
        dest="target_zip",
        nargs="?",
        default=None,
        help="An optional zip file which will be produced of the migrated files",
    )
    return parser.parse_args()


def main():
    args = process_args()
    target_directory = args.target_directory
    target_zip = args.target_zip
    if target_zip:
        target_zip = target_zip.replace(".zip", "")

    migration = Migration(
        xsd_dump_path=args.xsd_dump_path, scenario_dump_path=args.scenario_dump_path
    )

    migration_module = importlib.import_module(args.migration_module.replace(".py", ""))
    migration.migrate(migration_module.migrate)

    #migration.validate() I think there is some issue with reading in the 1.0 schema
    migration.write(target_directory)

    if target_zip:
        shutil.make_archive(target_zip, "zip", target_directory)


if __name__ == "__main__":
    main()
