from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('create-interview/', views.create_interview, name='create_interview'),
    path('interview/<uuid:mock_id>/', views.interview_detail, name='interview_detail'),
] 