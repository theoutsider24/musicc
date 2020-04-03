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
# Sample usage:
# python migration.py --dir migration_folder --mus-zip query_results_2_1.zip --xsd-zip musicc_0.1.0.zip --zip migrated_files_0.1.0.zip --script example_migration_module.py

def migrate(context):
    print("Starting to run custom migration!")
    context.mus_etree.xpath("//FileHeader")[0].set("revision","0.1.0")
    return context