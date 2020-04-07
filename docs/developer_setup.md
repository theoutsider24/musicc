# How to set up a development environment

If you don't want to [build from Docker](https://gitlab.com/connected-places-catapult/musicc#building-from-docker), you can build the system from source. Please also see the [project roadmap](roadmap.md).

## Building from source

You will need the following:
- Postgres 12
- Python 3.6 (MUSICC will not work with older or newer Python versions)
- Git

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
5. (Not recommended) Register local system as master. This can be done if you are sure you won't ever want to synchronise scenarios and SDL revisions from the CPC MUSICC instance.
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

- The system should be running on http://localhost:8000/
- To access the admin panel navigate to http://localhost:8000/admin/
- [Sync from the master](https://gitlab.com/connected-places-catapult/musicc#synchronise-scenarios-and-sdl-revisions-from-master) to access the MUSICC SDL revisions, or upload them from the curation interface manually


