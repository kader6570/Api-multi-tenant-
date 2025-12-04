from rest_framework import serializers
from . import models


class CategorieSerializer(serializers.ModelSerializer):
    """Serializer pour les catégories"""
    
    class Meta:
        model = models.Categorie
        fields = ('id', 'nom')
        # Exclut automatiquement 'client' pour l'API publique


class MarqueSerializer(serializers.ModelSerializer):
    """Serializer pour les marques"""
    # ✅ logo retourne l'URL Cloudinary automatiquement
    
    class Meta:
        model = models.Marque
        fields = ('id', 'nom_marque', 'logo')
        # Exclut automatiquement 'client' pour l'API publique


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour les articles
    Inclut les relations (marque, catégorie) et les thumbnails optimisés
    ✅ ADAPTÉ CLOUDINARY : Les thumbnails sont générés via SerializerMethodField
    """
    marque = MarqueSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
    # ✅ Thumbnails optimisés (300x300) - générés par Cloudinary à la volée
    image_thumbnail = serializers.SerializerMethodField()
    image1_thumbnail = serializers.SerializerMethodField()
    image2_thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Article
        fields = (
            'id',
            'categorie',
            'modele',
            'marque',
            # Images complètes (URLs Cloudinary optimisées)
            'image',
            'image1',
            'image2',
            # Thumbnails optimisés (URLs générées)
            'image_thumbnail',
            'image1_thumbnail',
            'image2_thumbnail',
            # Autres champs
            'prix',
            'stokcage',
            'ram',
            'date_ajout',
            'date_modification',
        )
        read_only_fields = ('date_ajout', 'date_modification',)
    
    # ✅ Méthodes pour générer les URLs des thumbnails
    def get_image_thumbnail(self, obj):
        """Retourne l'URL du thumbnail 300x300 de l'image principale"""
        return obj.get_image_thumbnail_url()
    
    def get_image1_thumbnail(self, obj):
        """Retourne l'URL du thumbnail 300x300 de image1"""
        return obj.get_image1_thumbnail_url()
    
    def get_image2_thumbnail(self, obj):
        """Retourne l'URL du thumbnail 300x300 de image2"""
        return obj.get_image2_thumbnail_url()


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer léger pour les listes (grilles de produits)
    N'inclut QUE les thumbnails pour optimiser la bande passante
    ✅ ADAPTÉ CLOUDINARY
    """
    marque = MarqueSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
    # ✅ Thumbnail optimisé pour les listes
    image_thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Article
        fields = (
            'id',
            'modele',
            'marque',
            'categorie',
            # ✅ Seulement le thumbnail pour les listes
            'image_thumbnail',
            'prix',
            'ram',
            'stokcage',
        )
    
    def get_image_thumbnail(self, obj):
        """Retourne l'URL du thumbnail 300x300"""
        return obj.get_image_thumbnail_url()


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour la page produit individuelle
    Inclut toutes les images en haute résolution
    ✅ ADAPTÉ CLOUDINARY : Images optimisées + thumbnails pour galerie
    """
    marque = MarqueSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
    # ✅ Thumbnails pour miniatures de galerie
    image_thumbnail = serializers.SerializerMethodField()
    image1_thumbnail = serializers.SerializerMethodField()
    image2_thumbnail = serializers.SerializerMethodField()
    
    # ✅ BONUS : Images optimisées 1200px pour affichage détail
    image_optimized = serializers.SerializerMethodField()
    image1_optimized = serializers.SerializerMethodField()
    image2_optimized = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Article
        fields = (
            'id',
            'categorie',
            'modele',
            'marque',
            # Images complètes (URLs Cloudinary brutes)
            'image',
            'image1',
            'image2',
            # Images optimisées 1200px (pour affichage principal)
            'image_optimized',
            'image1_optimized',
            'image2_optimized',
            # Thumbnails (pour les miniatures de galerie)
            'image_thumbnail',
            'image1_thumbnail',
            'image2_thumbnail',
            # Specs
            'prix',
            'stokcage',
            'ram',
            'date_ajout',
            'date_modification',
        )
    
    # Méthodes pour thumbnails
    def get_image_thumbnail(self, obj):
        return obj.get_image_thumbnail_url()
    
    def get_image1_thumbnail(self, obj):
        return obj.get_image1_thumbnail_url()
    
    def get_image2_thumbnail(self, obj):
        return obj.get_image2_thumbnail_url()
    
    # Méthodes pour images optimisées
    def get_image_optimized(self, obj):
        return obj.get_image_optimized_url()
    
    def get_image1_optimized(self, obj):
        return obj.get_image1_optimized_url()
    
    def get_image2_optimized(self, obj):
        return obj.get_image2_optimized_url()
