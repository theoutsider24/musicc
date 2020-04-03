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
    context.mus_etree.xpath("/MUSICCScenario")[0].set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation","MUSICC_0.1.4.xsd")
    context.mus_etree.xpath("//FileHeader")[0].set("revision","0.1.5")

    #Add a new test case weighting element
    tcw = lxml.etree.Element("TestcaseWeighting",value="1")
    try:
        prevElement = context.mus_etree.xpath("//Exposure")
        exposure0 = prevElement[0]
        exposure0.addnext(tcw)
        print("added TestcaseWeighting after exposure")

    except:
        prevElement = context.mus_etree.xpath("//ScenarioType")
        scenariotype0=prevElement[0]
        scenariotype0.addnext(tcw)
        print("added TestCaseWeighting after ScenarioType")

    #Revise ObjectGoalPositions section
    #rename
    objectGoalPositions = context.mus_etree.xpath("//ObjectGoalPositions")
    objectGoalPositions[0].tag = "EntityUnderTest"

    #private => entityRef
    item = context.mus_etree.xpath("/MUSICCScenario/EntityUnderTest/Private")
    vehicleName = context.mus_etree.xpath("/MUSICCScenario/EntityUnderTest/Private/@object")
    entRefElement = lxml.etree.Element("EntityRef",entityRef=vehicleName[0])
    item[0].addnext(entRefElement)

    #Move and rename position element, remove empty action tag
    positionElement = context.mus_etree.xpath("/MUSICCScenario/EntityUnderTest/Private/Action/Position")
    positionElement[0].tag = "GoalPosition"
    prevElement = context.mus_etree.xpath("/MUSICCScenario/EntityUnderTest/EntityRef")
    prevElement[0].addnext(positionElement[0])
    
    entityUnderTest = context.mus_etree.xpath("/MUSICCScenario/EntityUnderTest")[0]
    private = context.mus_etree.xpath("/MUSICCScenario/EntityUnderTest/Private")[0]
    entityUnderTest.remove(private)


    return context