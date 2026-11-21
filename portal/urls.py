from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.PortalLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),
    path("session/renew/", views.renew_session, name="renew-session"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/master-data/", views.master_records, name="master-records"),
    path("dashboard/master-data/mappings/", views.master_mappings, name="master-mappings"),
    path("dashboard/master-data/mappings/columns/", views.mapping_columns, name="mapping-columns"),
    path("dashboard/master-data/<int:mapping_id>/<str:record_id>/delete/", views.master_delete, name="master-delete"),
    path("dashboard/access-control/credential-manager/", views.credential_manager, name="credential-manager"),
    path("dashboard/access-control/<slug:tab>/", views.access_control, name="access-control"),
    path("dashboard/students/enrollment-request/", views.enrollment_request, name="enrollment-request"),
    path("dashboard/students/enrollment-request/new/", views.enrollment_new, name="enrollment-new"),
    path("dashboard/students/student-registration/", views.student_registration, name="student-registration"),
    path("dashboard/students/student-registration/new/", views.student_registration_new, name="student-registration-new"),
    path("dashboard/students/student-registration/<int:student_id>/edit/", views.student_registration_edit, name="student-registration-edit"),
    path("dashboard/students/student-registration/sibling/", views.student_sibling_lookup, name="student-sibling-lookup"),
    path("dashboard/menu/<slug:slug>/", views.module_detail, name="module"),
    path("dashboard/<slug:slug>/<slug:submenu_slug>/", views.submenu_detail, name="submenu"),
    path("dashboard/<slug:slug>/", views.module_detail, name="legacy-module"),
    path("api/me/", views.api_me, name="api-me"),
    path("api/modules/", views.api_modules, name="api-modules"),
    path("api/token/", obtain_auth_token, name="api-token"),
]