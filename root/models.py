from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from PIL.Image import Resampling
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import os

# ========================================
# IMPORTS CLOUDINARY (AJOUTÉS)
# ========================================
from cloudinary.models import CloudinaryField


# ========================================
# NOUVEAU MODÈLE : Client (Tenant)
# ========================================
class Client(models.Model):
    """
    Représente un client (tenant) avec son propre espace admin
    """
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du client")
    domaine = models.URLField(
        unique=True, 
    )
    actif = models.BooleanField(default=True, verbose_name="Client actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    # Lien vers l'utilisateur Django admin de ce client
    utilisateur_admin = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='client',
        verbose_name="Compte admin Django"
    )

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['nom']


# ========================================
# MODÈLE : Categorie (avec client)
# ========================================
class Categorie(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='categories')
    nom = models.CharField(max_length=32, blank=True, default='Téléphone')

    def __str__(self):
        return f"{self.nom} ({self.client.nom})"
    
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        unique_together = ['client', 'nom']  # Unique par client


# ========================================
# MODÈLE : Marque (avec client)
# ========================================
class Marque(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='marques')
    nom_marque = models.CharField(verbose_name="Nom de la marque", max_length=20)
    # MODIFIÉ : Utilise CloudinaryField pour le logo
    logo = CloudinaryField('logo', folder='logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nom_marque} ({self.client.nom})"
    
    class Meta:
        verbose_name = 'Marque'
        verbose_name_plural = 'Marques'
        unique_together = ['client', 'nom_marque']


# ========================================
# MODÈLE : Article (avec client)
# ========================================
class Article(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='articles')
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE)
    modele = models.CharField(max_length=50)
    prix = models.DecimalField(decimal_places=2, max_digits=14)
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.CASCADE, 
        related_name='articlesLiees', 
        blank=True, 
        null=True
    )
    stokcage = models.IntegerField(null=True, blank=True, verbose_name="Stockage (Go)")
    ram = models.IntegerField(null=True, blank=True, verbose_name="RAM (Go)")
    
    # MODIFIÉ : Images stockées sur Cloudinary
    # Cloudinary gère automatiquement les transformations et optimisations
    image = CloudinaryField(
        'image',
        folder='articles/',
        transformation={
            'quality': 'auto:good',
            'fetch_format': 'auto'
        }
    )
    image1 = CloudinaryField(
        'image',
        folder='articles/',
        blank=True,
        null=True,
        transformation={
            'quality': 'auto:good',
            'fetch_format': 'auto'
        }
    )
    image2 = CloudinaryField(
        'image',
        folder='articles/',
        blank=True,
        null=True,
        transformation={
            'quality': 'auto:good',
            'fetch_format': 'auto'
        }
    )
    
    # Les thumbnails ne sont plus nécessaires car Cloudinary génère des URLs
    # avec les dimensions voulues à la volée via les transformations
    # Exemples d'URLs générées automatiquement :
    # - Image complète optimisée : article.image.url
    # - Thumbnail 300x300 : article.image.build_url(width=300, height=300, crop='fill')
    
    # Métadonnées
    date_ajout = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.marque.nom_marque} {self.modele}"

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-date_ajout']
    
    # AJOUTÉ : Méthodes helper pour obtenir les URLs des thumbnails
    def get_image_thumbnail_url(self):
        """Retourne l'URL du thumbnail 300x300 de l'image principale"""
        if self.image:
            return self.image.build_url(width=300, height=300, crop='fill', quality='auto:good')
        return None
    
    def get_image1_thumbnail_url(self):
        """Retourne l'URL du thumbnail 300x300 de image1"""
        if self.image1:
            return self.image1.build_url(width=300, height=300, crop='fill', quality='auto:good')
        return None
    
    def get_image2_thumbnail_url(self):
        """Retourne l'URL du thumbnail 300x300 de image2"""
        if self.image2:
            return self.image2.build_url(width=300, height=300, crop='fill', quality='auto:good')
        return None
    
    def get_image_optimized_url(self):
        """Retourne l'URL de l'image optimisée 1200px max"""
        if self.image:
            return self.image.build_url(width=1200, crop='limit', quality='auto:good')
        return None
    
    def get_image1_optimized_url(self):
        """Retourne l'URL de image1 optimisée 1200px max"""
        if self.image1:
            return self.image1.build_url(width=1200, crop='limit', quality='auto:good')
        return None
    
    def get_image2_optimized_url(self):
        """Retourne l'URL de image2 optimisée 1200px max"""
        if self.image2:
            return self.image2.build_url(width=1200, crop='limit', quality='auto:good')
        return None
    
    # NOTE : La méthode save() n'a plus besoin d'optimiser les images
    # car Cloudinary le fait automatiquement avec les transformations.
    # Vous pouvez supprimer les méthodes optimize_image et create_thumbnail
    # ou les garder pour compatibilité si vous avez d'autres usages.
