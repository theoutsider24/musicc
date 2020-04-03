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
# Generated by Django 2.2 on 2019-08-05 10:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('musicc', '0002_auto_20190802_1224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='system',
            name='system_id',
            field=models.UUIDField(editable=False),
        ),
        migrations.CreateModel(
            name='RegisteredSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('instance_id', models.UUIDField()),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
