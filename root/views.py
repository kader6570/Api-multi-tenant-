from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework import filters
from django.db.models import Q
from django.shortcuts import get_object_or_404  # ✅ AJOUTER

from . import serializer 
from . import models


# ========================================
# ✅ NOUVEAU : Mixin pour filtrage par domaine
# ========================================
class ClientFilterMixin:
    """
    Mixin pour filtrer automatiquement les données par client
    basé sur le domaine (HTTP_ORIGIN ou HTTP_REFERER)
    """
    def get_client_from_request(self):
        """
        Extrait le client depuis le domaine de la requête
        Utilise HTTP_ORIGIN en priorité, sinon HTTP_REFERER
        
        Returns:
            Client object ou None si domaine inconnu
        """
        # Récupérer le domaine depuis les headers
        origin = self.request.META.get('HTTP_ORIGIN')
        
        # Fallback sur REFERER si ORIGIN absent
        if not origin:
            referer = self.request.META.get('HTTP_REFERER', '')
            # Extraire le domaine du referer (format: https://example.com/page)
            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                origin = f"{parsed.scheme}://{parsed.netloc}"
        
        # Si toujours pas de domaine, retourner None
        if not origin:
            return None
        
        # Nettoyer le domaine (enlever les trailing slashes)
        origin = origin.rstrip('/')
        
        # Chercher le client correspondant
        try:
            client = models.Client.objects.get(domaine=origin, actif=True)
            return client
        except models.Client.DoesNotExist:
            return None
    
    def filter_queryset_by_client(self, queryset):
        """
        Filtre le queryset pour ne retourner que les données du client
        
        Args:
            queryset: Le queryset à filtrer
        
        Returns:
            Queryset filtré par client, ou vide si domaine inconnu
        """
        client = self.get_client_from_request()
        
        if client is None:
            # ⚠️ Domaine inconnu : retourner un queryset vide (sécurité)
            return queryset.none()
        
        # Filtrer par client
        return queryset.filter(client=client)


class ArticlePagination(PageNumberPagination):
    """
    Pagination pour les listes d'articles
    12 produits par page par défaut
    """
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


# ========================================
# ✅ MODIFIÉ : ViewSets avec filtrage client
# ========================================
class apiCategorie(ClientFilterMixin, ModelViewSet):
    """ViewSet pour les catégories - filtré par client"""
    queryset = models.Categorie.objects.all()
    serializer_class = serializer.CategorieSerializer
    
    def get_queryset(self):
        """Filtre les catégories par client"""
        queryset = super().get_queryset()
        return self.filter_queryset_by_client(queryset)


class apiArticle(ClientFilterMixin, ModelViewSet):
    """
    ViewSet pour les articles avec recherche, filtrage et pagination
    ✅ Filtré automatiquement par domaine (HTTP_ORIGIN)
    
    Endpoints disponibles:
    - GET /articles/ : Liste paginée (avec thumbnails)
    - GET /articles/{id}/ : Détail complet (images HD)
    - GET /articles/?search=iphone : Recherche
    - GET /articles/?marque=Apple : Filtre par marque
    - GET /articles/?categorie=Telephone : Filtre par catégorie
    """
    queryset = models.Article.objects.select_related('marque', 'categorie').all()
    pagination_class = ArticlePagination
    
    # Filtres de recherche
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['modele', 'marque__nom_marque', 'categorie__nom']
    ordering_fields = ['prix', 'date_ajout', 'modele']
    ordering = ['-date_ajout']
    
    def get_serializer_class(self):
        """
        Utilise le serializer approprié selon l'action
        """
        if self.action == 'list':
            return serializer.ArticleListSerializer
        return serializer.ArticleDetailSerializer
    
    def get_queryset(self):
        """
        ✅ Filtre par client + query params personnalisés
        """
        queryset = super().get_queryset()
        
        # ✅ CRITIQUE : Filtrer par client d'abord
        queryset = self.filter_queryset_by_client(queryset)
        
        # Filtre par marque
        marque = self.request.query_params.get('marque', None)
        if marque:
            queryset = queryset.filter(marque__nom_marque__iexact=marque)
        
        # Filtre par catégorie
        categorie = self.request.query_params.get('categorie', None)
        if categorie:
            queryset = queryset.filter(categorie__nom__icontains=categorie)
        
        # Filtre par prix min
        prix_min = self.request.query_params.get('prix_min', None)
        if prix_min:
            queryset = queryset.filter(prix__gte=prix_min)
        
        # Filtre par prix max
        prix_max = self.request.query_params.get('prix_max', None)
        if prix_max:
            queryset = queryset.filter(prix__lte=prix_max)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Endpoint personnalisé pour les produits phares
        GET /articles/featured/
        ✅ Retourne les 8 articles les plus récents DU CLIENT
        """
        articles = self.get_queryset()[:8]
        serializer_instance = serializer.ArticleListSerializer(articles, many=True)
        return Response(serializer_instance.data)


class apiMarque(ClientFilterMixin, ModelViewSet):
    """ViewSet pour les marques - filtré par client"""
    queryset = models.Marque.objects.all()
    serializer_class = serializer.MarqueSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Filtre les marques par client"""
        queryset = super().get_queryset()
        return self.filter_queryset_by_client(queryset)


class Filtreur(ClientFilterMixin, APIView):
    """
    Vue personnalisée pour filtrer les articles par catégorie
    ✅ Filtré par domaine automatiquement
    
    GET /filtrer/?categorie=Telephone
    GET /filtrer/?categorie=all (tous les produits DU CLIENT)
    """
    pagination_class = ArticlePagination
    
    def get(self, request):
        # Récupérer le paramètre de catégorie
        categorie_param = request.query_params.get('categorie', 'all')
        
        # Requête de base : tous les articles
        articles = models.Article.objects.select_related('marque', 'categorie').all()
        
        # ✅ CRITIQUE : Filtrer par client d'abord
        articles = self.filter_queryset_by_client(articles)
        
        # Filtrer par catégorie si spécifié
        if categorie_param.lower() not in ['all', 'tout', 'catalogue']:
            categorie_clean = categorie_param.replace('_', ' ')
            articles = articles.filter(
                Q(categorie__nom__icontains=categorie_clean) |
                Q(categorie__nom__iexact=categorie_clean)
            )
        
        # Pagination
        paginator = self.pagination_class()
        paginated_articles = paginator.paginate_queryset(articles, request)
        
        # Serializer léger
        article_serializer = serializer.ArticleListSerializer(paginated_articles, many=True)
        
        return paginator.get_paginated_response(article_serializer.data)


class RechercheArticles(ClientFilterMixin, APIView):
    """
    Vue dédiée à la recherche multi-critères
    ✅ Filtré par domaine automatiquement
    
    GET /recherche/?q=iphone&marque=Apple&prix_max=500000
    """
    pagination_class = ArticlePagination
    
    def get(self, request):
        # Récupérer le terme de recherche
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({
                'error': 'Le paramètre "q" est requis',
                'example': '/recherche/?q=iphone'
            }, status=400)
        
        # Recherche multi-champs
        articles = models.Article.objects.select_related('marque', 'categorie').filter(
            Q(modele__icontains=query) |
            Q(marque__nom_marque__icontains=query) |
            Q(categorie__nom__icontains=query)
        ).distinct()
        
        # ✅ CRITIQUE : Filtrer par client
        articles = self.filter_queryset_by_client(articles)
        
        # Filtres additionnels
        marque = request.query_params.get('marque', None)
        if marque:
            articles = articles.filter(marque__nom_marque__iexact=marque)
        
        prix_max = request.query_params.get('prix_max', None)
        if prix_max:
            articles = articles.filter(prix__lte=prix_max)
        
        # Pagination
        paginator = self.pagination_class()
        paginated_articles = paginator.paginate_queryset(articles, request)
        
        article_serializer = serializer.ArticleListSerializer(paginated_articles, many=True)
        
        return paginator.get_paginated_response(article_serializer.data)