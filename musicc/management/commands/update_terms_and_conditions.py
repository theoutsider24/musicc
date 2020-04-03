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
from musicc.models.Profile import Profile

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

class Command(BaseCommand):
    help = 'Updates the terms and conditions agreement status of all or a subset users'

    def add_arguments(self, parser):
        parser.add_argument('-a', '--has_agreed', type=str2bool)
        parser.add_argument('-i', '--ignore_existing', type=str2bool, default=False)

    def handle(self, *args, **options):
        try:
            has_agreed = options['has_agreed']
        except:
            raise CommandError('Must specify whether to set the agreed status to \'True\' or \'False\' using the -a command')

        try:
            ignore_existing = options['ignore_existing']
            print(ignore_existing)
        except:
            ignore_existing = False
        
        Profile.update_all_users(has_agreed, ignore_users_with_agreements=ignore_existing)

        self.stdout.write(self.style.SUCCESS('Successfully updated users agreement status'))