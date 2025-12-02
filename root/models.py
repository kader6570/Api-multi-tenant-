from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from PIL.Image import Resampling
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import os


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
    logo = models.ImageField(upload_to='images_logo/')

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
    
    # Images originales (taille complète optimisée à 1200px max)
    image = models.ImageField(upload_to='image_articles/')
    image1 = models.ImageField(upload_to='image_articles/', blank=True, null=True)
    image2 = models.ImageField(upload_to='image_articles/', blank=True, null=True)
    
    # Thumbnails pour les grilles (300x300px)
    image_thumbnail = models.ImageField(
        upload_to='image_articles/thumbnails/', 
        blank=True, 
        null=True,
        editable=False
    )
    image1_thumbnail = models.ImageField(
        upload_to='image_articles/thumbnails/', 
        blank=True, 
        null=True,
        editable=False
    )
    image2_thumbnail = models.ImageField(
        upload_to='image_articles/thumbnails/', 
        blank=True, 
        null=True,
        editable=False
    )
    
    # Métadonnées
    date_ajout = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.marque.nom_marque} {self.modele}"

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-date_ajout']
    
    def save(self, *args, **kwargs):
        """
        Surcharge de save() pour optimiser et créer les thumbnails automatiquement
        """
        # Optimiser l'image principale
        if self.image and hasattr(self.image, 'file'):
            self.image = self.optimize_image(self.image, max_size=(1200, 1200), quality=85)
            self.image_thumbnail = self.create_thumbnail(self.image, size=(300, 300))
        
        # Optimiser image1
        if self.image1 and hasattr(self.image1, 'file'):
            self.image1 = self.optimize_image(self.image1, max_size=(1200, 1200), quality=85)
            self.image1_thumbnail = self.create_thumbnail(self.image1, size=(300, 300))
        
        # Optimiser image2
        if self.image2 and hasattr(self.image2, 'file'):
            self.image2 = self.optimize_image(self.image2, max_size=(1200, 1200), quality=85)
            self.image2_thumbnail = self.create_thumbnail(self.image2, size=(300, 300))
        
        super().save(*args, **kwargs)
    
    def optimize_image(self, image_field, max_size=(1200, 1200), quality=85):
        """
        Optimise une image : redimensionne et compresse
        """
        try:
            img = Image.open(image_field)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            img.thumbnail(max_size, Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            original_name = os.path.splitext(image_field.name)[0]
            
            return InMemoryUploadedFile(
                output, 
                'ImageField', 
                f"{original_name}_optimized.jpg",
                'image/jpeg',
                sys.getsizeof(output), 
                None
            )
        except Exception as e:
            print(f"Erreur lors de l'optimisation de l'image : {e}")
            return image_field
    
    def create_thumbnail(self, image_field, size=(300, 300), quality=80):
        """
        Crée un thumbnail carré pour les grilles de produits
        """
        try:
            if isinstance(image_field, InMemoryUploadedFile):
                image_field.seek(0)
                img = Image.open(image_field)
            else:
                img = Image.open(image_field)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            img.thumbnail(size, Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            if isinstance(image_field, InMemoryUploadedFile):
                original_name = os.path.splitext(image_field.name)[0]
            else:
                original_name = os.path.splitext(image_field.name)[0]
            
            return InMemoryUploadedFile(
                output,
                'ImageField',
                f"{original_name}_thumb.jpg",
                'image/jpeg',
                sys.getsizeof(output),
                None
            )
        except Exception as e:
            print(f"Erreur lors de la création du thumbnail : {e}")
            return None
