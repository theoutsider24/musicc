This repository provides source code for [MUSICC](https://cp.catapult.org.uk/case-studies/musicc/),
a project run by the [Connected Places Catapult](https://cp.catapult.org.uk/)
on behalf of the [Department for Transport](https://www.gov.uk/government/organisations/department-for-transport).

[[_TOC_]]

# MUSICC Project Overview

As highly automated vehicles (HAVs) are deployed on public roads, regulators need to make sure that these systems are safe. This challenge requires coordination between regulators and system developers – with common (or at least aligned) approaches to validation desirable. 

One of the big challenges is achieving enough coverage of real-world situations to know that Automated Driving Systems (ADS) are acceptably safe. ADS developers have indicated that testing by driving vehicles on public roads is not enough, due to: 
* The large number of miles needed to cover all situations which could be encountered.
* A lack of control of the test parameters.

The solution is likely to involve more than one technology but will almost certainly include an element of simulation. [MUSICC](https://cp.catapult.org.uk/case-studies/musicc/) has created a system to store and share scenarios: an ADS will be expected to demonstrate its performance in these before release to market. As far as we know, MUSICC is the first project of its type to build a proof of concept system specifically designed for regulatory use.

The project is led by a regulator ([Department for Transport](https://www.gov.uk/government/organisations/department-for-transport)) and an impartial, neutral mediator ([Connected Places Catapult](https://cp.catapult.org.uk/)). It is influenced by a highly credible industrial advisory group, including representatives of several major OEMs, tool providers, ADS developers, research and innovation organisations, CAV testbeds and insurers. 

A [working prototype](https://musicc.ts-catapult.org.uk/) has been built and interested stakeholders are invited to sign up and try out the system. We are particularly interested in feedback on  how test scenarios might be used in a future regulatory regime, which can be provided either by [email](mailto:musicc-support@cp.catapult.org.uk) or on [GitLab](https://gitlab.com/connected-places-catapult/musicc/-/issues).


# Motivation for Open Release / User Installs

Our aim is to create a central scenario repository for regulatory use (as prototyped [at CPC](https://musicc.ts-catapult.org.uk)). However, many organisations would like a tool to store and manage their own test scenarios without having to make those scenarios publicly available. We've made this possible by enabling users to install their own instance of MUSICC, using Docker and/or the code in this repository. From our point-of-view, the benefits are:
* If MUSICC is used operationally, we get better feedback on how it needs to evolve, and better evidence that it is a useful, practical tool.
* Other organisations can contribute to the codebase.
* It encourages the industry to adopt MUSICC's scenario format.
* Regulators other than the DfT have the opportunity to try out MUSICC in a test environment.

User installations of MUSICC can synchronise the regulatory scenario set from the master instance with the click of a button.

We have released this code under the [AGPL](https://www.gnu.org/licenses/#AGPL), but would like to assure anyone who wishes to integrate their tools with MUSICC that a well-defined API exists for this, and there should not be any risk to their existing IP.

# Quick Start Installation

## Building from Docker

1. Pull the latest MUSICC Docker image and Postgres 12 from Docker Hub
```bash
docker pull connectedplacescatapult/musicc:latest
docker pull postgres:12
```
2. Create a network for the database and MUSICC and run the containers
```bash
docker network create musicc_net
docker run -d --name=db --network=musicc_net -e POSTGRES_PASSWORD=postgres postgres:12
docker run -d -p 80:80 --name=web --network=musicc_net connectedplacescatapult/musicc:latest
```
3. Navigate to [localhost](http://localhost)

The default admin account details are
- username: *admin*
- password: *admin*

To access the admin panel navigate to [localhost/admin](http://localhost/admin)

## Building from source

You will need the following:
- Postgres 12
- Python 3.6 or greater
Postgres should be configured with the default settings.

1. Clone the repository
```bash
git clone https://gitlab.com/connected-places-catapult/musicc.git
```
2. Install required Python libraries
```
cd musicc
pip install -r requirements.txt
```
3. Perform Django migrations
```bash
python manage.py migrate
```
4. Open the Django shell and create new user with account details - username: *admin*, password: *admin*
```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@myproject.com', 'admin', first_name = 'System', last_name = 'Admin')
exit()
```
5. (Optional) Register local system as master
```bash
python manage.py shell
```
```python
from musicc.models.System import System
System.register_as_master()
exit()
```
6. Launch MUSICC
```bash
python manage.py runserver
```

- To access the admin panel navigate to [localhost/admin](http://localhost/admin)
- Sync from the master to access the MUSICC SDL revisions, or upload them from the curation interface manually


# Guide to Other Documentation

* [User guide](docs/MUSICC_User_Guide.pdf) (PDF) - this is the best place to start
* Guide to [MUSICC's scenario format](docs/MUSICC_SDL_Specification_0.1.5.pdf) (PDF), aka the SDL (scenario description language)
* [Docker configuration](docs/docker_installation.md)
* Guide on [how to contribute to the project](CONTRIBUTING.md)
* [Roadmap for future development](docs/roadmap.md)
* Doxygen for code

# Useful Links

* [ASAM OpenSCENARIO](https://www.asam.net/standards/detail/openscenario/)
* [ASAM OpenDRIVE](https://www.asam.net/standards/detail/opendrive/)
* [ASAM OpenLABEL](https://www.asam.net/project-detail/scenario-storage-and-labelling/)
* [Es Mini](https://github.com/esmini/esmini), an OpenSCENARIO visualisation/simulation tool
