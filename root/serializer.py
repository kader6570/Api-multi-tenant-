from rest_framework import serializers
from . import models


class CategorieSerializer(serializers.ModelSerializer):
    """Serializer pour les catégories"""
    
    class Meta:
        model = models.Categorie
        fields = ('id', 'nom')


class MarqueSerializer(serializers.ModelSerializer):
    """Serializer pour les marques"""
    
    class Meta:
        model = models.Marque
        fields = ('id', 'nom_marque', 'logo')
        # ✅ AJOUTER : exclure 'client' de l'API publique


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour les articles
    Inclut les relations (marque, catégorie) et les thumbnails optimisés
    """
    marque = MarqueSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
    # ✅ Thumbnails optimisés
    image_thumbnail = serializers.ImageField(read_only=True)
    image1_thumbnail = serializers.ImageField(read_only=True)
    image2_thumbnail = serializers.ImageField(read_only=True)
    
    class Meta:
        model = models.Article
        fields = (
            'id',
            'categorie',
            'modele',
            'marque',
            # Images complètes
            'image',
            'image1',
            'image2',
            # Thumbnails optimisés
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
        # ✅ AJOUTER : exclure 'client' explicitement (sécurité)


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer léger pour les listes (grilles de produits)
    N'inclut QUE les thumbnails pour optimiser la bande passante
    """
    marque = MarqueSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
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



class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour la page produit individuelle
    Inclut toutes les images en haute résolution
    """
    marque = MarqueSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
    class Meta:
        model = models.Article
        fields = (
            'id',
            'categorie',
            'modele',
            'marque',
            # Images complètes pour les détails
            'image',
            'image1',
            'image2',
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


