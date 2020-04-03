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
from musicc.models.Profile import Profile
from musicc.models.System import System
from django.test import TestCase
from musicc.tests.utilities import (
    initialise_super_user,
    initialise_user,
    set_media_root,
    clear_media_root
)
from django.contrib.auth import get_user_model
import django.http.response as django_response

class UserSignUpTestCase(TestCase):
    def setUp(self):
        set_media_root()
        initialise_super_user()
        login = self.client.login(username="admin", password="password")
        self.assertTrue(login)
        User = get_user_model()
        current_user = User.objects.get(id=self.client.session["_auth_user_id"])
        System.register_as_master()
        initialise_user(5)

    def tearDown(self):
        clear_media_root()
    


    

class ProfileTest(UserSignUpTestCase):
    def test_initialised_users_not_agreed(self):
        self.assertEqual(1, Profile.objects.count())
        User = get_user_model()
        self.assertEqual(6, User.objects.count())

    def test_change_all_non_agreed_users_to_false(self):
        Profile.update_all_users(False, ignore_users_with_agreements=True)
        self.assertEqual(5, Profile.objects.filter(has_agreed=False).count())
        self.assertEqual(1, Profile.objects.filter(has_agreed=True).count())
    
    def test_change_all_agreed_users_to_false(self):
        Profile.update_all_users(False)
        self.assertEqual(6, Profile.objects.filter(has_agreed=False).count())
    
    def test_update_user_agreement(self):
        User = get_user_model()
        user = User.objects.filter(username='user0').first()
        Profile.create(user, False)
        self.assertFalse(user.profile.first().has_agreed)
        profile = user.profile.first()
        profile.has_agreed = True
        profile.save()
        self.assertTrue(user.profile.first().has_agreed)

class UserSignUp(UserSignUpTestCase):
    def test_get_signup_form(self):
        response = self.client.get("http://localhost:8000/signup/")
        self.assertEqual(
            response.status_code, django_response.HttpResponseBase.status_code
        )
    
    def test_get_terms_and_conditions(self):
        response = self.client.get("http://localhost:8000/terms_and_conditions")
        self.assertEqual(
            response.status_code, django_response.HttpResponseBase.status_code
        )

    def test_get_privacy_policy(self):
        response = self.client.get("http://localhost:8000/privacy_policy")
        self.assertEqual(
            response.status_code, django_response.HttpResponseRedirect.status_code
        )