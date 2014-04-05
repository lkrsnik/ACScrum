from django.conf.urls import patterns, url
from scrumko import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
	url(r'^register/$', views.register, name='register'),
	url(r'^home/$', views.home, name='home'),
	url(r'^logout/$', views.user_logout, name='logout'),
	url(r'^sprintcreate/$', views.sprintcreate, name='spcreate'),
	url(r'^projectcreate/$', views.projectcreate, name='prcreate'),
	url(r'^maintainuser/$', views.maintainuser, name='maintainuser'),
	url(r'^maintainsprint/$', views.maintainsprint, name='maintainsprint'),
	url(r'^storycreate/$', views.storycreate, name='storycreate'),
	url(r'^maintainproject/$', views.maintainproject, name='maintainproject'),
	)
