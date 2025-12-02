from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from . import models


# ========================================
# ✅ FILTRES PERSONNALISÉS PAR CLIENT
# ========================================
class ClientMarqueFilter(admin.SimpleListFilter):
    """Filtre les marques selon le client de l'utilisateur"""
    title = 'marque'
    parameter_name = 'marque'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            marques = models.Marque.objects.all()
        else:
            try:
                client = request.user.client
                marques = models.Marque.objects.filter(client=client)
            except models.Client.DoesNotExist:
                marques = models.Marque.objects.none()
        return [(marque.id, marque.nom_marque) for marque in marques]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(marque_id=self.value())
        return queryset


class ClientCategorieFilter(admin.SimpleListFilter):
    """Filtre les catégories selon le client de l'utilisateur"""
    title = 'catégorie'
    parameter_name = 'categorie'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            categories = models.Categorie.objects.all()
        else:
            try:
                client = request.user.client
                categories = models.Categorie.objects.filter(client=client)
            except models.Client.DoesNotExist:
                categories = models.Categorie.objects.none()
        return [(cat.id, cat.nom) for cat in categories]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(categorie_id=self.value())
        return queryset

# ========================================
# ✅ MIXIN : Filtrage automatique par client (CORRIGÉ)
# ========================================
class ClientFilterMixin:
    """
    Mixin pour filtrer automatiquement l'admin par client
    Chaque utilisateur admin ne voit QUE les données de son client
    """
    
    def get_queryset(self, request):
        """
        Filtre le queryset selon le client de l'utilisateur
        Les superusers voient tout, les autres ne voient que leur client
        """
        qs = super().get_queryset(request)
        
        # Si superuser → voir tout
        if request.user.is_superuser:
            return qs
        
        # Sinon, filtrer par client
        try:
            client = request.user.client
            return qs.filter(client=client)
        except models.Client.DoesNotExist:
            return qs.none()
    
    def get_fields(self, request, obj=None):
        """
        ✅ NOUVEAU : Masque le champ 'client' pour les non-superusers
        (il sera rempli automatiquement)
        """
        fields = super().get_fields(request, obj)
        
        # Si non-superuser, retirer 'client' des champs visibles
        if not request.user.is_superuser and 'client' in fields:
            fields = tuple(f for f in fields if f != 'client')
        
        return fields
    
    def get_fieldsets(self, request, obj=None):
        """
        ✅ NOUVEAU : Adapte les fieldsets pour masquer 'client' aux non-superusers
        """
        fieldsets = super().get_fieldsets(request, obj)
        
        if not request.user.is_superuser:
            # Parcourir les fieldsets et retirer 'client'
            new_fieldsets = []
            for name, data in fieldsets:
                fields = list(data.get('fields', []))
                if 'client' in fields:
                    fields.remove('client')
                data['fields'] = tuple(fields)
                new_fieldsets.append((name, data))
            return new_fieldsets
        
        return fieldsets
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtre les ForeignKey dans les formulaires
        Ex: Quand on crée un Article, ne montrer que les Marques du client
        """
        if not request.user.is_superuser:
            try:
                client = request.user.client
                
                # Filtrer les marques par client
                if db_field.name == "marque":
                    kwargs["queryset"] = models.Marque.objects.filter(client=client)
                
                # Filtrer les catégories par client
                if db_field.name == "categorie":
                    kwargs["queryset"] = models.Categorie.objects.filter(client=client)
                
            except models.Client.DoesNotExist:
                kwargs["queryset"] = db_field.related_model.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        ✅ CORRIGÉ : Associe automatiquement le client lors de la création
        """
        # Si c'est une création (pas une modification) et que l'objet n'a pas de client
        if not change:
            if not request.user.is_superuser:
                try:
                    # Assigner automatiquement le client de l'utilisateur
                    obj.client = request.user.client
                except models.Client.DoesNotExist:
                    pass
        
        super().save_model(request, obj, form, change)


# ========================================
# ✅ ADMIN : Client (visible uniquement pour superuser)
# ========================================
@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Gestion des clients - RÉSERVÉ AUX SUPERUSERS
    """
    list_display = ('nom', 'domaine', 'utilisateur_admin', 'actif', 'date_creation')
    list_filter = ('actif', 'date_creation')
    search_fields = ('nom', 'domaine', 'utilisateur_admin__username')
    readonly_fields = ('date_creation',)
    
    fieldsets = (
        ('Informations du client', {
            'fields': ('nom', 'domaine', 'actif')
        }),
        ('Compte admin Django', {
            'fields': ('utilisateur_admin',),
            'description': 'Utilisateur qui gère ce client dans l\'admin'
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    def has_module_permission(self, request):
        """Seuls les superusers peuvent voir les clients"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ========================================
# ✅ ADMIN : Catégorie (filtré par client)
# ========================================
@admin.register(models.Categorie)
class CategorieAdmin(ClientFilterMixin, admin.ModelAdmin):
    """
    Gestion des catégories - Filtré par client
    """
    list_display = ('nom', 'get_client_display', 'nombre_articles')
    search_fields = ('nom',)
    
    # Champs visibles dans le formulaire (client masqué pour non-superusers)
    fields = ('nom',)
    
    def get_client_display(self, obj):
        """Affiche le nom du client (utile pour les superusers)"""
        return obj.client.nom if hasattr(obj, 'client') else '-'
    get_client_display.short_description = 'Client'
    
    def nombre_articles(self, obj):
        """Compte le nombre d'articles dans cette catégorie"""
        count = obj.articlesLiees.count()
        return format_html('<strong>{}</strong>', count)
    nombre_articles.short_description = 'Articles'
    
    def get_list_display(self, request):
        """
        Masque la colonne 'Client' pour les non-superusers
        (ils ne voient que leur propre client)
        """
        if request.user.is_superuser:
            return ('nom', 'get_client_display', 'nombre_articles')
        return ('nom', 'nombre_articles')


# ========================================
# ✅ ADMIN : Marque (filtré par client)
# ========================================
@admin.register(models.Marque)
class MarqueAdmin(ClientFilterMixin, admin.ModelAdmin):
    """
    Gestion des marques - Filtré par client
    """
    list_display = ('nom_marque', 'get_client_display', 'apercu_logo', 'nombre_articles')
    search_fields = ('nom_marque',)
    
    fields = ('nom_marque', 'logo')
    
    def get_client_display(self, obj):
        return obj.client.nom if hasattr(obj, 'client') else '-'
    get_client_display.short_description = 'Client'
    
    def apercu_logo(self, obj):
        """Affiche une miniature du logo"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.logo.url
            )
        return '-'
    apercu_logo.short_description = 'Logo'
    
    def nombre_articles(self, obj):
        """Compte le nombre d'articles de cette marque"""
        count = obj.article_set.count()
        return format_html('<strong>{}</strong>', count)
    nombre_articles.short_description = 'Articles'
    
    def get_list_display(self, request):
        """Masque la colonne Client pour les non-superusers"""
        if request.user.is_superuser:
            return ('nom_marque', 'get_client_display', 'apercu_logo', 'nombre_articles')
        return ('nom_marque', 'apercu_logo', 'nombre_articles')


# ========================================
# ✅ ADMIN : Article (filtré par client)
# ========================================
@admin.register(models.Article)
class ArticleAdmin(ClientFilterMixin, admin.ModelAdmin):
    """
    Gestion des articles - Filtré par client
    Interface complète avec aperçus d'images
    """
    list_display = (
        'modele', 
        'marque', 
        'categorie', 
        'prix', 
        'stokcage', 
        'ram',
        'get_client_display',
        'apercu_image',
        'date_ajout'
    )
    list_filter = (ClientCategorieFilter, ClientMarqueFilter, 'date_ajout')
    search_fields = ('modele', 'marque__nom_marque')
    readonly_fields = ('date_ajout', 'date_modification', 'apercu_images_complet')
    list_per_page = 20
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('marque', 'modele', 'prix', 'categorie')
        }),
        ('Caractéristiques', {
            'fields': ('stokcage', 'ram')
        }),
        ('Images principales', {
            'fields': ('image', 'image1', 'image2'),
            'description': 'Les images seront automatiquement optimisées et redimensionnées'
        }),
        ('Aperçu des images', {
            'fields': ('apercu_images_complet',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_ajout', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def get_client_display(self, obj):
        return obj.client.nom if hasattr(obj, 'client') else '-'
    get_client_display.short_description = 'Client'
    
    def apercu_image(self, obj):
        """Miniature de l'image principale dans la liste"""
        if obj.image_thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.image_thumbnail.url
            )
        elif obj.image:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'
    apercu_image.short_description = 'Image'
    
    def apercu_images_complet(self, obj):
        """Affiche toutes les images du produit dans le formulaire"""
        html = '<div style="display: flex; gap: 20px; flex-wrap: wrap;">'
        
        images = [
            ('Image principale', obj.image, obj.image_thumbnail),
            ('Image 2', obj.image1, obj.image1_thumbnail),
            ('Image 3', obj.image2, obj.image2_thumbnail),
        ]
        
        for label, img, thumb in images:
            if img:
                html += f'''
                <div style="text-align: center;">
                    <strong>{label}</strong><br>
                    <img src="{img.url}" style="max-width: 200px; margin-top: 10px; border: 1px solid #ddd; border-radius: 4px;" />
                    <br><small>Taille complète</small>
                </div>
                '''
                if thumb:
                    html += f'''
                    <div style="text-align: center;">
                        <strong>Thumbnail</strong><br>
                        <img src="{thumb.url}" style="max-width: 100px; margin-top: 10px; border: 1px solid #ddd; border-radius: 4px;" />
                        <br><small>Miniature</small>
                    </div>
                    '''
        
        html += '</div>'
        return format_html(html)
    apercu_images_complet.short_description = 'Aperçu de toutes les images'
    
    def get_list_display(self, request):
        """Masque la colonne Client pour les non-superusers"""
        if request.user.is_superuser:
            return (
                'modele', 
                'marque', 
                'categorie', 
                'prix', 
                'stokcage', 
                'ram',
                'get_client_display',
                'apercu_image',
                'date_ajout'
            )
        return (
            'modele', 
            'marque', 
            'categorie', 
            'prix', 
            'stokcage', 
            'ram',
            'apercu_image',
            'date_ajout'
        )


# ========================================
# ✅ PERSONNALISATION : Titre de l'admin
# ========================================
admin.site.site_header = "Administration Multi-Clients"
admin.site.site_title = "Admin Produits"
admin.site.index_title = "Gestion de votre catalogue"