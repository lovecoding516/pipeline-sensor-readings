from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("upload", views.UploadView.as_view(), name="upload"),
    path("readings", views.ReadingsView.as_view(), name="readings"),
    path("summary", views.SummaryView.as_view(), name="summary"),
]
