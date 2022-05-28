from import_export.fields import Field
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin

from .models import Author, Journal, Organization, Paper


class PaperInline(admin.TabularInline):
    model = Paper
    fields = ('title', 'doi', 'url')
    extra = 1


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    actions_on_top = True
    actions_on_bottom = True
    date_hierarchy = 'modified_at'
    fieldsets = (
        (None,               {'fields': ('name', 'rank')}),
        ('Date information', {'classes': ('collapse',),
                              'fields': ('created_at', 'modified_at')}),
    )
    inlines = (PaperInline,)
    list_display = ('name', 'rank', 'created_at', 'modified_at')
    # list_display_links = ('name', 'rank')
    list_editable = ('rank',)
    list_filter = ('rank', 'created_at', 'modified_at')
    ordering = ('name', '-rank', '-created_at', '-modified_at')
    readonly_fields = ('created_at', 'modified_at')
    search_fields = ('name', 'rank')


class AuthorInline(admin.TabularInline):
    model = Author
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    actions_on_top = True
    actions_on_bottom = True
    date_hierarchy = 'modified_at'
    fieldsets = (
        (None,               {
            'classes': ('wide',),
            'fields': ('name', 'rank')}),
        ('Date information', {'classes': ('collapse',),
                              'fields': ('created_at', 'modified_at')}),
    )
    inlines = (AuthorInline,)
    list_display = ('name', 'rank', 'created_at', 'modified_at')
    # list_display_links = ('name', 'rank')
    list_editable = ('rank',)
    list_filter = ('rank', 'created_at', 'modified_at')
    ordering = ('name', '-rank', '-created_at', '-modified_at')
    readonly_fields = ('created_at', 'modified_at')
    search_fields = ('name', 'rank')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    actions_on_top = True
    actions_on_bottom = True
    date_hierarchy = 'modified_at'
    fieldsets = (
        (None,               {
            'classes': ('wide',),
            'fields': (('forename', 'surname'), 'email', 'organization')}),
        ('Date information', {
            'classes': ('collapse',),
            'fields': ('created_at', 'modified_at')}),
    )
    list_display = ('__str__', 'forename', 'surname', 'email',
                    'organization', 'created_at', 'modified_at')
    list_display_links = ('__str__', 'email')
    list_editable = ('forename', 'surname')
    list_filter = ('created_at', 'modified_at', 'organization')
    ordering = ('forename', 'surname', '-created_at', '-modified_at')
    readonly_fields = ('created_at', 'modified_at')
    search_fields = ('name', 'rank')


class ImportPaperResource(resources.ModelResource):

    class Meta:
        model = Paper
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('doi',)
        
        fields = ('tei', 'doi', 'url',)


class ExportPaperResource(resources.ModelResource):
    contents = Field()

    def dehydrate_contents(self, paper):
        return '%s\n%s' % (paper.title, paper.abstract)

    class Meta:
        model = Paper
        fields = ('id', 'contents')


@admin.register(Paper)
class PaperAdmin(ImportExportActionModelAdmin):
    resource_class = ImportPaperResource
    actions = ['parse_tei']
    actions_on_top = True
    #dinasayed added this line
    list_per_page=500
    # actions_on_bottom = True
    date_hierarchy = 'modified_at'
    fieldsets = (
        (None,                {
            'fields': (('pdf', 'grobid_button'), ('tei', 'parse_button'))}),
        ('Paper information', {
            'fields': ('title', 'abstract', 'journal', 'published_at', 'doi', 'url', 'authors')}),
        ('Date information',  {
            'classes': ('collapse',),
            'fields': ('created_at', 'modified_at')}),
    )
    filter_horizontal = ('authors',)
    list_display = ('title', 'doi', 'url', 'journal', 'published_at',
                    'created_at', 'modified_at')
    list_display_links = ('title', 'doi')
    list_filter = ('published_at', 'created_at',
                   'modified_at', 'journal', 'authors')
    ordering = ('title', '-created_at', '-modified_at')
    readonly_fields = ('grobid_button', 'parse_button',
                       'created_at', 'modified_at')
    search_fields = ('title', 'abstract', 'doi', 'url', 'authors', 'journal')

    def get_export_resource_class(self):
        return ExportPaperResource

    @staticmethod
    def button(label, enabled):
        return f'<a class="button default" {"href={}" if enabled else "disabled"}>{label}</a>'

    @admin.display(description='Extract')
    def grobid_button(self, obj):
        return format_html(PaperAdmin.button('using Grobid', obj.pdf), '')

    @admin.display(description='Parse')
    def parse_button(self, obj):
        return format_html(PaperAdmin.button('from TEI', obj.tei), reverse('admin:webapp_paper_parse_tei', args=(obj.id,)))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/parse_tei/', self.admin_site.admin_view(self.parse_tei_view),
                 name='webapp_paper_parse_tei')
        ]
        return custom_urls + urls

    def parse_tei_view(self, request, **kwargs):
        paper_id = kwargs['object_id']
        paper = get_object_or_404(Paper, pk=paper_id)
        paper.parse_tei().save()
        return HttpResponseRedirect(reverse('admin:webapp_paper_change', args=(paper_id,)))

    @admin.action(description='Parse TEI of selected papers')
    def parse_tei(self, request, queryset):
        for paper in queryset.all():
            try:
                paper.parse_tei().save()
            except:
                pass

