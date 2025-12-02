from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

# ✅ Router pour les ViewSets
router = DefaultRouter()
router.register('categories', views.apiCategorie, basename='categorie')
router.register('marques', views.apiMarque, basename='marque')
router.register('articles', views.apiArticle, basename='article')

# ✅ URLs personnalisées
urlpatterns = [
    path('filtrer/', views.Filtreur.as_view(), name='filtreur'),
    path('recherche/', views.RechercheArticles.as_view(), name='recherche'),
]
urlpatterns += router.urls

