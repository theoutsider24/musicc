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
from django.contrib.auth.forms import UserCreationForm
from musicc.forms import SignUpForm, TermsAndConditionsUpdateForm
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.conf import settings
import os

def pdf_view(request, path):
    try:
        return FileResponse(open(os.path.join(settings.BASE_DIR, path), "rb"), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404()

def terms_and_conditions(request):
    return render(
        request,
        "registration/terms_and_conditions.html"
    ) 

def update_terms_and_conditions(request):
    if request.method == 'POST':
        form = TermsAndConditionsUpdateForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = TermsAndConditionsUpdateForm(request.user)

    return render(
        request,
        "registration/update_terms_and_conditions.html",
        {'form': form}
    ) 

def privacy_policy(request):
    try:
        return redirect('https://cp.catapult.org.uk/privacy-policy/')
    except:
        raise Http404()

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect('/accounts/login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})