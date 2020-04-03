# Motivation

MUSICC is a system to store and share a *library of scenarios*.  It demonstrates the concept of a regulatory scenario database for use in type approval of highly automated vehicles. More detailed background information on the project can be found in the [README document](docs/README.md).

There are three main parts to MUSICC:
* The system itself, a piece of software which stores and tracks scenarios to make them accessible to registered users.
* The Scenario Description Language (SDL), the format which scenarios are stored in. This brings together and extends [OpenSCENARIO](https://www.asam.net/standards/detail/openscenario/), [OpenDRIVE](https://www.asam.net/standards/detail/opendrive/) and [OpenSceneGraph](http://www.openscenegraph.org/).
* A set of example scenarios to demonstrate the system.

This repository stores source code for the system and definitions for the SDL. Example scenarios are available to download from the [master system](https://musicc.ts-catapult.org.uk/).

# Philosophy

As far as possible, MUSICC uses open standards. The core system and SDL should be tool agnostic (though export conversion tools to other formats are welcome).

# Features: Integrations with simulation tools

Very welcome. As above, no SDL changes please.

# Features: System enhancements

## Include OpenSCENARIO and OpenDRIVE in diff views (curator interface)
When approving a change, the curator can only see changes to MUSICC files in-browser. Ideally, they would be able to see all changes without having to download the scenarios.

## View Catalog files in the GUI
OpenSCENARIO catalog files are an important part of the scenario definition. Users should be able to see these files (and compare versions) in the same way they can with the main scenario file.

# Features: Scenario representation

## Functional scenario support

A *functional scenario* is the highest level of scenario abstration. Two scenarios with different definitions but the same "story" could be considered to belong to the same functional scenario. There is no perfect way to represent this in MUSICC at the moment (though global tags are a start). Some thought is required to define exactly how this should work, and what information should be stored at functoinal scenario level.

## Independence of scenarios + maps

Ideally, any scenario could be automatically run on any appropriate map. For example, it may be desirable to simulate a pull-out scenario at every junction within the ODD. OpenSCENARIO 1.0 was not designed with this in mind, so it may be challenging to implement. OpenSCENARIO 2.0 (see below) may contain features which help with this.

## Support for OpenSCENARIO 2 (and/or M-SDL)

OpenSCENARIO 2.0 will be a significant change: it is expected to be based on [M-SDL](https://www.foretellix.com/open-language/) rather than XML. The system will need to be modified to store scenarios in the new language. New features in 2.0 may also create opportunities for adding extra functionality.

## ODD representation enhancement

For the foreseeable future, CAVs will not be ‘go anywhere’vehicles: they will have a defined Operational Design Domain (ODD) which defines the conditions under which they can operate. When testing these vehicles, it is important to be able to identify which scenarios fall within their ODD. MUSICC supports a basic form of ODD description which can be written in the form of a search query. However, it has become clear that this simple approach will not support all likely use cases.

A document outlining some of the design considerations for ODD design is available on the [MUSICC web page](https://cp.catapult.org.uk/case-studies/musicc/).

The CAV community has recognised the importance of ODD description and several projects are doing work in this area. These include:
* [BSI PAS 1883](https://standardsdevelopment.bsigroup.com/projects/2019-03092#/section): Operational design domain (ODD) taxonomy for an automated driving system (ADS)
* ASAM OpenODD: defining a standard file format for ODD specification
* [WISE Drive framework](https://uwaterloo.ca/waterloo-intelligent-systems-engineering-lab/projects/wise-drive-requirements-analysis-framework-automated-driving): primarily intended for specifying requirements, but also has relevance to ODD definition

Connected Places Catapult may do further work in this area.

# Features: Scenario processing

## Storage of scenario results

Two possible use cases:
* Anonymised feedback on the difficulty of each scenario. Not implemented so far due to low demand.
* Full results stored alongside scenarios - either for internal use or regulatory audit.

## Semantic validation of scenarios

Static validation of XML files is carried out at upload. This could be extended to include some checks of the content itself.

## Auto-generate thumbnails of scenarios

We have created an [ES-mini runner tool](https://github.com/matthewcoyle-cpc/esmini-visualiser) to automatically produce images of the scenario running. This could be integrated into the upload process (note: some way of generating inputs for externally controlled vehicles will be required).

## Search for scenarios on the boundary of an ODD

It is important that vehicles are tested against scenarios right at the edge of their ODD. Some thought is required about how to select these in MUSICC.

## Randomisation of OpenDRIVE features

The SDL provides for introducing parameters into OpenDRIVE files, but due to the way the file is structured, this does not enable substantial randomisation.  Some possibilities for further development are:
* Allowing random selection of an OpenDRIVE file from a list
* Allowing a more meaningful set of parameters to be introduced to an OpenDRIVE file
* Storing road networks in an abstract format, with OpenDRIVE files automatically generated as required

This is related to the 'Independence of scenarios + maps' feature.
 
 