from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.generic import ListView
from django.db.models import Count

from taggit.models import Tag
from haystack.query import SearchQuerySet

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm


def post_list(request, tag_slug=None):
	object_list = Post.published.all()
	tag = None
	if tag_slug:
		tag = get_object_or_404(Tag, slug=tag_slug)
		object_list = object_list.filter(tags__in=[tag])
	paginator = Paginator(object_list, 5)
	page = request.GET.get('page')
	try:
		posts = paginator.page(page)
	except PageNotAnInteger:
		posts = paginator.page(1)
	except EmptyPage:
		posts = paginator.page(paginator.num_pages)
	return render(
		request,
		'blog/post/list.html',
		{
			'page': page,
			'posts': posts,
			'tag': tag,
		}
	)

def post_detail(request, year, month, day, post):
	post = get_object_or_404(
		Post,
		slug=post,
		status='published',
		publish__year=year,
		publish__month=month,
		publish__day=day
	)

	comments = post.comments.filter(active=True)
	if request.method == 'POST':
		comment_form = CommentForm(data=request.POST)
		if comment_form.is_valid():
			new_comment = comment_form.save(commit=False)
			new_comment.post = post
			new_comment.save()
	else:
		comment_form = CommentForm()

	post_tags_ids = post.tags.values_list('id', flat=True)
	similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
	similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

	return render(
		request,
		'blog/post/detail.html',
		{
			'post': post,
			'comments': comments,
			'comment_form': comment_form,
			'similar_posts': similar_posts,
		}
	)

def post_share(request, post_id):
	post = get_object_or_404(Post, id=post_id, status='published')
	sent = False
	if request.method == 'POST':
		form = EmailPostForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			post_url = request.build_absolute_uri(post.get_absolute_url())
			subject = '{} ({}) recommends you reading "{}"'.format(
				cd['name'], cd['email'], post.title
			)
			message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(
				post.title, post_url, cd['name'], cd['comments']
			)
			send_mail(subject, message, 'glebmi69@gmail.com', [cd['to']])
			sent = True
	else:
		form = EmailPostForm()
	return render(
		request,
		'blog/post/share.html',
		{
			'post': post,
			'form': form,
			'sent': sent
		}
	)

def post_search(request):
	form = SearchForm()
	cd = None
	results = None
	total_results = None
	if 'query' in request.GET:
		form = SearchForm(request.GET)
		if form.is_valid():
			cd = form.cleaned_data
			#results = SearchQuerySet().models(Post).filter(content=cd['query']).load_all()
			r = SearchQuerySet().models(Post).filter(content=cd['query'])
			pk_list = [i.pk for i in r]
			results = Post.published.filter(pk__in=pk_list)
			total_results = len(results)
	return render(
		request,
		'blog/post/search.html',
		{
			'form': form,
			'cd': cd,
			'results': results,
			'total_results': total_results
		}
	)
