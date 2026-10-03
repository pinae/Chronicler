from django.urls import path, re_path

from gm_ui import views

urlpatterns = [
    path("healthz", views.healthz, name="healthz"),
    # Everything the backend does not answer belongs to the frontend's router.
    re_path(r"^(?!api/|admin/|static/).*$", views.frontend_app, name="frontend_app"),
]
