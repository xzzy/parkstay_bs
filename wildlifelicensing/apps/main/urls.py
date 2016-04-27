from django.conf.urls import url

from .views import ListProfilesView, CreateProfilesView, EditProfilesView, IdentificationView


urlpatterns = [
    url('^profiles/$', ListProfilesView.as_view(), name='list_profiles'),
    url('^profiles/create/$', CreateProfilesView.as_view(), name='create_profile'),
    url('^profiles/edit/$', EditProfilesView.as_view(), name='edit_profile_prefix'),
    url('^profiles/edit/([0-9]+)/$', EditProfilesView.as_view(), name='edit_profile'),
    url('^identification/$', IdentificationView.as_view(), name='identification'),
]