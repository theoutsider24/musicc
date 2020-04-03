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

import lxml

def migrate(context):
    print("Starting to run custom migration!")
    context.mus_etree.xpath("/MUSICCScenario")[0].set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation","MUSICC_1.0.xsd")
    context.mus_etree.xpath("//FileHeader")[0].set("revision","1.0")

    #Assign any step changes a 0 duration
    for i, dtag in enumerate(context.osc_etree.xpath('//Dynamics[@shape="step"]')):
        dtag.attrib.clear()
        dtag.attrib["shape"]="step"
        dtag.attrib["time"]="0"

    #Do XSLT translation
    xslt = lxml.etree.parse("translation.xslt")
    transform = lxml.etree.XSLT(xslt)
    context.osc_etree = transform (context.osc_etree)
    print("Main file etree transform complete")

    #Add a value for max acceleration (new requirement for 1.0)
    performanceElements = context.osc_etree.xpath("/OpenSCENARIO/Entities/ScenarioObject/Vehicle/Performance")
    for ptag in performanceElements:
        ptag.attrib["maxAcceleration"]="10"

    #Do the same for catalogs
    for i, item in enumerate(context.catalog_etrees):
        context.catalog_etrees[i] = transform (item)
        print("Catalog file XSLT transform complete")        
        #untested
        performanceElements = context.osc_etree.xpath("/OpenSCENARIO/Catalog/Vehicle/Performance")
        for ptag in performanceElements:
            ptag.attrib["maxAcceleration"]="10"

    #Rename position elements in MUSICC file
    try:
        objectGoalPositions = context.mus_etree.xpath("//World")
        objectGoalPositions[0].tag = "WorldPosition"
    except:
        print("File does not use world position")
        
    try:
        objectGoalPositions = context.mus_etree.xpath("//Road")
        objectGoalPositions[0].tag = "RoadPosition"
    except:
        print("File does not use road position")
        
    try:
        objectGoalPositions = context.mus_etree.xpath("//Lane")
        objectGoalPositions[0].tag = "LanePosition"
    except:
        print("File does not use lane position")

        
    return context