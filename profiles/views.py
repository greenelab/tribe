from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from allauth.utils import generate_unique_username

from profiles.models import Profile
from profiles.forms import UpgradeUserForm, CreateTempAcctForm

def create_temporary_acct(request):
    if request.method == 'POST':
        form = CreateTempAcctForm(request.POST)
        latest_temp_user = User.objects.filter(username__startswith='TemporaryUser').latest('date_joined')
        if form.is_valid():
            try:
                # The next few lines number Temporary Users's usernames.
                # If we have a lot of traffic, we might have to change this in case multiple temporary
                # accounts want to be created at the exact same time (as this would violate the
                # unique=True constraint for username)
                latest_temp_num = int(latest_temp_user.username[13:])
                latest_temp_num += 1
                username = 'TemporaryUser' + str(latest_temp_num)

                import uuid
                password = str(uuid.uuid4())
                new_user = User.objects.create_user(username, None, password=password, first_name='Temporary', last_name='User')
                Profile.objects.create(user=new_user, temporary_acct=True)
                user = authenticate(username=username, password=password)
                login(request, user)
                request.session.set_expiry(31536000) # Make session persistent for a year
                return HttpResponseRedirect('/')

            except:
                return HttpResponseRedirect('/')
    else:
        form = CreateTempAcctForm()
    return render(request, 'create_temp_acct.html', {'form': form})

def convert_to_full_acct(request):
    user = request.user

    if request.method == 'POST':
        form = UpgradeUserForm(request.POST)

        try:
            profile = Profile.objects.get(user=user) # Check that there is a profile for this user
        except:
            return render(request, 'invalid_acct.html', {})

        if (user.is_authenticated() and profile.temporary_acct):
            if form.is_valid():
                email = form.cleaned_data['email']
                new_password = form.cleaned_data['password']

                user.email = email
                user.set_password(new_password)
                user.username = generate_unique_username((email, ))
                user.save()

                profile.temporary_acct = False
                profile.save()

                request.session.set_expiry(0) # Make user logged in for the duration of the session, as would be the
                                              # case when logged in with any other regular account.
                return HttpResponseRedirect('/')

        else:
            return render(request, 'invalid_acct.html', {})

    elif (user.is_authenticated() == False):
        return render(request, 'invalid_acct.html', {})

    else:
        form = UpgradeUserForm()
    return render(request, 'upgrade_temp_acct.html', {'form': form})
