from django.urls import path, include
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('interview/<uuid:mock_id>/start/', views.start_interview, name='start_interview'),
    path('interview/<uuid:mock_id>/results/', views.interview_results, name='interview_results'),
    path('interview/<uuid:mock_id>/save-answer/', views.save_answer, name='save_answer'),
    path('interview/<uuid:mock_id>/save-recording/', views.save_recording, name='save_recording'),
    path('howit/', views.how_it_works, name='howit'),
] 