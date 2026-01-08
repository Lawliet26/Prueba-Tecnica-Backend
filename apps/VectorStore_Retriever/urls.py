from django.urls import path
from .views import retriever_view

urlpatterns = [
    path('search/', retriever_view, name='retriever_search')
]