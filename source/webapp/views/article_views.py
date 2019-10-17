
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode
from django.views.generic import ListView, DetailView, CreateView, \
    UpdateView, DeleteView
from webapp.forms import ArticleForm, ArticleCommentForm, SimpleSearchForm
from webapp.models import Article, Tag
from django.core.paginator import Paginator

class IndexView(ListView):
    context_object_name = 'articles'
    model = Article
    template_name = 'article/index.html'
    ordering = ['-created_at']
    paginate_by = 5
    paginate_orphans = 1

    def get(self, request, *args, **kwargs):
        self.form = self.get_search_form()
        self.search_query = self.get_search_query()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        if self.search_query:
            context['query'] = urlencode({'search': self.search_query})
        context['form'] = self.form
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.search_query:
            queryset = queryset.filter(
                Q(title__icontains=self.search_query)
                | Q(author__icontains=self.search_query)
            )
        return queryset

    def get_search_form(self):
        return SimpleSearchForm(self.request.GET)

    def get_search_query(self):
        if self.form.is_valid():
            return self.form.cleaned_data['search']
        return None


class ArticleView(DetailView):
    template_name = 'article/article.html'
    model = Article
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ArticleCommentForm()
        comments = context['article'].comments.order_by('-created_at')
        self.paginate_comments_to_context(comments, context)
        return context

    def paginate_comments_to_context(self, comments, context):
        paginator = Paginator(comments, 3, 0)
        page_number = self.request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        context['paginator'] = paginator
        context['page_obj'] = page
        context['comments'] = page.object_list
        context['is_paginated'] = page.has_other_pages()


class ArticleCreateView(CreateView):
    model = Article
    template_name = 'article/create.html'
    form_class = ArticleForm

    def form_valid(self, form):
        self.object = form.save()
        self.parser()
        return redirect(self.get_success_url())

    def parser(self):
        tags = self.request.POST.get('tags')
        tag_list = tags.split(',')
        for tag in tag_list:
            tag, created = Tag.objects.get_or_create(name=tag)
            self.object.tags.add(tag)

    def get_success_url(self):
        return reverse('article_view', kwargs={'pk': self.object.pk})

class ArticleUpdateView(UpdateView):
    model = Article
    template_name = 'article/update.html'
    context_object_name = 'article'
    form_class = ArticleForm

    def update_tag(self):
        tags = self.request.POST.get('tags')
        tags_list = tags.split(',')
        self.object.tags.clear()
        for tag in tags_list:
            tag, created = Tag.objects.get_or_create(name=tag)
            self.object.tags.add(tag)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        querry = self.object.tags.values('name')
        res = ''
        for tag in querry:
            res += tag['name'] + ','
        form.fields['tags'].initial = res.replace(' ', '').strip(',')
        return form

    def form_valid(self, form):
        self.object = form.save()
        self.update_tag()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('article_view', kwargs={'pk': self.object.pk})

class ArticleDeleteView(DeleteView):
    model = Article
    template_name = 'article/delete.html'
    context_object_name = 'article'
    success_url = reverse_lazy('index')
