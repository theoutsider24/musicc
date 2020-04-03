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
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from musicc.models.Profile import Profile


class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=50, required=False, help_text='Required. E.g. \'firstname.lastname.\'')
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Input a valid email address.')
    has_agreed = forms.BooleanField(label='',required=False, help_text=mark_safe('Required. Check here to indicate you have read and agree to the <a href="/privacy_policy">CPC Privacy Policy</a> and <a href="/terms_and_conditions">MUSICC Terms and Conditions</a>.'))
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_has_agreed(self):
        agree = self.cleaned_data['has_agreed']
        if (agree != True):
            raise forms.ValidationError('You must agree to the Terms and Conditions to sign up.',
        code='terms_and_conditions')
        return agree
    
    def save(self, commit=True):
        if not commit:
            raise NotImplementedError("Can't create User and UserProfile without database save")
        user = super(SignUpForm, self).save(commit=True)
        has_agreed = self.cleaned_data['has_agreed']
        profile = Profile.create(user=user, has_agreed=has_agreed)
        return user, profile

class TermsAndConditionsUpdateForm(forms.Form):
    has_agreed = forms.BooleanField(label='',required=False, help_text=mark_safe('Check here to indicate you have read and agree to the <a href="/terms_and_conditions">MUSICC Terms and Conditions</a> and <a href="/privacy_policy">CPC Privacy Policy</a>.'))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(TermsAndConditionsUpdateForm, self).__init__(*args, **kwargs)

    def clean_has_agreed(self):
        agree = self.cleaned_data['has_agreed']
        if (agree != True):
            raise forms.ValidationError('You must agree to the Terms and Conditions and Privacy Policy to continue.',
        code='terms_and_conditions')
        return agree
    
    def save(self, commit=True):
        if not commit:
            raise NotImplementedError("Can't update UserProfile without database save")
        has_agreed = self.cleaned_data['has_agreed']
        if self.user.profile.first():
            profile = self.user.profile.first()
            profile.has_agreed = has_agreed
            profile.save()
        else:
            profile = Profile.create(user=self.user, has_agreed=has_agreed)
        return profile