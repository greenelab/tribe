"""
Utility methods for collaborators.

This module has methods to get collaborators, users you've invited, and users who have invited you.
"""

from django.contrib.auth.models import User

def get_collaborators(user):
    return User.objects.filter(to_users__from_user=user).filter(from_users__to_user=user)

def get_invites(user):
    return User.objects.filter(to_users__from_user=user).exclude(from_users__to_user=user)

def get_inviteds(user):
    return User.objects.filter(from_users__to_user=user).exclude(to_users__from_user=user)
