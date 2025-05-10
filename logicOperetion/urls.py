"""
URL configuration for logicOperetion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from appLogicModel.views import IndexView, SessionStartView, LevelsView, ResultsView, InstructionsView, next_run, \
    save_comment, download_session_report

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    path('session_start/', SessionStartView.as_view(), name='session_start'),
    path('levels/', LevelsView.as_view(), name='levels'),
    path('results/', ResultsView.as_view(), name='results_view'),
    path('instructions/', InstructionsView.as_view(), name='instructions'),
    path('next_run/', next_run, name='next_run'),
    path('save_comment/', save_comment, name='save_comment'),
    path('download_report/', download_session_report, name='download_report'),
]
