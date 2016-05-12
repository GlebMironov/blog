from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords
from django.core.urlresolvers import reverse

from .models import Post


class LatestPostsFeed(Feed):
	title = 'glebmironov.com'
	link = '/blog/'
	description = 'New posts of my blog'

	def items(self):
		return Post.published.all()[:5]

	def item_title(self, item):
		return item.title

	def item_description(self, item):
		return truncatewords(item.body, 30)

