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
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
from django.core.management.base import BaseCommand
import random
from lxml.etree import ElementTree, fromstring, tostring, Comment, parse, Element
from inspect import isfunction
import os
from shutil import copy, make_archive, copytree, move, rmtree
import glob


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-f", "--base-file", type=str, help="Base musicc file to modify")
        parser.add_argument("-n", "--number-of-scenarios", type=int, help="Number of scenarios to generate")
        parser.add_argument("-d", "--dir", type=str, help="Base directory")
        parser.add_argument("-c", "--catalog-dir", type=str, help="Directory of catalog files")

    def handle(self, *args, **options):
        directory = options["dir"]
        base_file = options["base_file"]
        number_of_scenarios = options["number_of_scenarios"]
        catalog_dir = options["catalog_dir"]

        self.generate_files(directory, base_file, number_of_scenarios, catalog_dir)

    def generate_files(self,directory, filename, number, catalog_dir):
        generated_directory = os.path.join(directory,"generated")
        catalog_dir_name = catalog_dir.split("/")[-1]
        
        et = parse(os.path.join(directory, filename))
        try:
            os.mkdir(generated_directory)
        except FileExistsError:
            for file in os.listdir(generated_directory):
                file_path = os.path.join(generated_directory, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
            if os.path.exists(os.path.join(generated_directory, catalog_dir_name)):
                rmtree(os.path.join(generated_directory, catalog_dir_name))
        if os.path.exists(os.path.join(directory, "generated.zip")):
            os.remove(os.path.join(directory, "generated.zip"))
        
        copytree(catalog_dir, os.path.join(generated_directory, catalog_dir_name))

        fileheader_node = et.getroot().find('FileHeader')
        revision = fileheader_node.get('revision')+'_test'

        for i in range(number):
            for modification in self.modification_map:
                field = modification["path"].split(".")

                if isfunction(modification["values"]):
                    value = str(modification["values"]())
                elif "occurences" in modification and "type" in modification:
                    elements = []
                    indices = random.sample(
                        range(0, len(modification["values"])),
                        random.randint(
                            modification["occurences"]["min"], modification["occurences"]["max"]
                        ),
                    )
                    for index in indices:
                        element = Element(modification["type"])
                        element.set("value", modification["values"][index])
                        elements.append(element)
                    value = elements
                else:
                    value = str(random.choice(modification["values"]))

                self.recursive_find_and_replace(et.getroot(), field, value)
            
            fileheader_node.set("revision", revision)

            et.write(os.path.join(generated_directory,"autogen_"+str(i)+"_"+filename), encoding="utf-8", xml_declaration = True)

        for file in glob.glob(os.path.join(directory,'*.xo*')):
            copy(file, generated_directory)

        make_archive(os.path.join(directory, "generated"), "zip", generated_directory)
        

    def recursive_find_and_replace(self,root, path, value):
        node = root.find(path[0])
        if node != None:
            if len(path) == 1:
                if isinstance(value, list):
                    node.clear()
                    node.extend(value)
                elif node.get("value") != None:
                    node.set("value", value)
            elif len(path) > 1:
                self.recursive_find_and_replace(node, path[1:], value)
        else:
            if(root.get(path[0])) != None:
                root.set(path[0], value)

    modification_map = [
        {"path": "FileHeader.label", "values": lambda: "UK CPC-Demo highway_test_double_lane_change-" + str(int(random.uniform(0, 200)))},
        {"path": "Metadata.CountryCode", "values": ["GB", "DE", "CH", "AT", "IE"]},
        {
            "path": "Metadata.UseCase",
            "values": ["Highway", "Urban", "InterUrban", "Parking"],
        },
        {"path": "Metadata.DriveOnRightOrLeft", "values": ["Left", "Right"]},
        {"path": "Metadata.Exposure", "values": ["E1", "E2", "E3", "E4"]},
        {
            "path": "Metadata.InitialSpeedLimit",
            "values": ["SlowUrban", "Urban", "FastUrban", "TrunkRoad", "Highway"],
        },
        {"path": "Metadata.RepresentsADASTest", "values": ["true", "false"]},
        {
            "path": "Metadata.SituationDemand",
            "values": ["Low", "Medium", "High", "VeryHigh", "Extreme"],
        },
        {
            "path": "Metadata.CollisionCategory",
            "values": ["Collision", "NearCollision", "NormalDriving"],
        },
        {
            "path": "Metadata.TrafficDensity",
            "values": ["EgoOnly", "Low", "FreeFlow", "MaxStable", "Unstable", "StopStart", "Jam"],
        },
        {
            "path": "Metadata.TrafficAverageSpeed",
            "values": ["Stationary", "Walking", "FastTrafficJam", "UrbanFlowing", "TrunkFlowing", "HighwayFlowing"],
        },
        {
            "path": "Metadata.RoadFeatures",
            "values": [
                "Roundabout",
                "HighwayEntranceRamp",
                "HighwayExitRamp",
                "TrafficLightControlledJunction",
                "3LegJunction",
                "4LegJunction",
                "MoreThan4LegJunction",
                "RailwayCrossing",
                "PedestrianCrossing",
                "StopSign",
                "GiveWaySign",
                "1Lane",
                "2Lane",
                "3Lane",
                "4Lane",
                "MoreThan4Lanes",
                "DividedCarriageway",
                "OneWayRoad",
                "BicycleLane",
                "HighGradient",
                "SharpBend",
                "Roadworks",
                "Tunnel",
            ],
            "occurences": {"min": 1, "max": 10},
            "type": "RoadFeature",
        },
        {
            "path": "Metadata.KeyActorTypes",
            "values": [
                "PassengerCar",
                "Truck",
                "Bus",
                "Motorcycle",
                "SmallLowSpeedVehicle",
                "EmergencyVehicle",
                "PedalCycle",
                "Trailer",
                "MotorizedOffRoadVehicle",
                "AnimalDrawnVehicle",
                "RailedVehicle",
                "RailRoadVehicle",
                "AnimalRider",
                "Pedestrian",
                "TrafficControlPerson",
                "Animal",
                "InanimateObstacle",
            ],
            "occurences": {"min": 1, "max": 10},
            "type": "KeyActorType",
        },
        {
            "path": "Metadata.KeyActorActions",
            "values": [
                "ActorCrossingRoad",
                "ActorStoppedInRoad",
                "EmergencyStop",
                "CutIn",
                "Overtake",
                "EmergencyStop",
                "WrongWayTravel",
            ],
            "occurences": {"min": 1, "max": 5},
            "type": "KeyActorAction",
        },
        {
            "path": "Metadata.EgoManeuverTypes",
            "values": [
                "RightTurn",
                "LeftTurn",
                "GoStraightAtJunction",
                "CrossTrafficTurn",
                "WithTrafficTurn",
                "UTurn",
                "TurnOntoMinorRoad",
                "TurnOntoMajorRoad",
                "HighwayMerge",
                "HighwayExit",
            ],
            "occurences": {"min": 1, "max": 4},
            "type": "EgoManeuverType",
        },
        {
            "path": "Metadata.ADASFeaturesTested",
            "values": [
                "ABS",
                "ACC",
                "AEB",
                "AFL",
                "BSM",
                "CSW",
                "CWS",
                "DMS",
                "DPP",
                "ESC",
                "FCW",
                "HUD",
                "ISA",
                "LDW",
                "LKA",
                "NVS",
                "PA",
                "PDS",
                "TPMS",
                "TSR",
            ],
            "occurences": {"min": 1, "max": 7},
            "type": "ADASFeature",
        },
        {
            "path": "Metadata.EnvironmentalConditions",
            "values": [
                "Rain",
                "NoRainButRoadWet",
                "Snow",
                "Ice",
                "Fog",
                "Cloudy",
                "Daylight",
                "Night",
                "Dawn",
                "Dusk",
            ],
            "occurences": {"min": 1, "max": 4},
            "type": "EnvironmentalCondition",
        },
    ]