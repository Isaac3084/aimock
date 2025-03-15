from django.urls import path
from . import views

urlpatterns = [
    path('interview/<str:mock_id>/save-answer/', views.save_answer, name='save_answer'),
] 