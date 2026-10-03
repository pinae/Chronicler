from django.urls import path

from gm_ui import views

urlpatterns = [
    path("healthz", views.healthz, name="healthz"),
]
