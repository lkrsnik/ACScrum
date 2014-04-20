from django.template import RequestContext
from django.shortcuts import render_to_response
from scrumko.forms import UserForm, UserProfileForm, SprintCreateForm, ProjectCreateForm, StoryForm

from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction


from scrumko.models import User
from scrumko.models import UserProfile
from scrumko.models import Sprint, Project
#from scrumko.forms import UserForm, UserProfileForm

@login_required
def home(request):
	
	# get current user
	current_user = request.user.id
	
	# Request the context of the request.
   	context = RequestContext(request)
        	
	# Project choose
	project_info = Project.objects.all()
	context_dict = {"project_detail" : project_info}
	
	# if user choose project, save this project id and name	
	if int(request.GET.get('project_id', '0'))>0:
		request.session['selected_project'] = int(request.GET.get('project_id', '0'))
		request.session['project_name'] = request.GET.get('name', '')
	# if project not choose
	else:
		if not request.session.get('selected_project'):
			request.session['selected_project'] = 0	
			request.session['project_name'] = ''
	
	# get information what roles user has on curent project
	selected_project_id = request.session['selected_project']
	is_owner = len (Project.objects.filter(project_owner__id = current_user, id = selected_project_id)) > 0
	is_scrum_master = len (Project.objects.filter(scrum_master__id = current_user, id = selected_project_id)) > 0
	
	# Construct a dictionary to pass to the template engine as its context.
	context_dict.update( {'is_owner':is_owner, 'is_scrum_master': is_scrum_master});	
				
	return render_to_response('scrumko/home.html', context_dict, context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def register(request):
    
	context = RequestContext(request)
	registered = False
	if request.method == 'POST':
  		user_form = UserForm(data=request.POST)
  		profile_form = UserProfileForm(data=request.POST)
		
		if user_form.is_valid() and profile_form.is_valid():	    
			user = user_form.save()	    
			user.set_password(user.password)
			user.save()
			profile = profile_form.save(commit=False)
			profile.user = user

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			profile.save()
			registered = True
		else:
			print user_form.errors, profile_form.errors
			return render_to_response('scrumko/register.html',{'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
	return render_to_response('scrumko/register.html',{'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)

def index(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)
    success=True;
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user is not None:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/scrumko/home/')
            else:
                # An inactive account was used - no logging in!
                success=False;
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            success=False;
            return render_to_response('scrumko/index.html', {'success': success}, context)
            #return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('scrumko/index.html', {'success': success}, context)


# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/scrumko/')


@login_required
def sprintcreate(request):

	# check permision to form and
	# project permision check
	current_user = request.user.id
	user_project =  Project.objects.filter(scrum_master__id = current_user, id = request.session['selected_project'])
	if len(user_project) == 0:
		return HttpResponseRedirect("/scrumko/home/")
	
	# set id of project to hidden input field
	r = user_project[0]

	# get context
	context = RequestContext(request)    
	
	# variable to check if sprint created
	registered = False
   
	if request.method == 'POST':
  		# get form inputs
  		sprint_form = SprintCreateForm(data=request.POST)
  		  		 		
        # If the forms is valid...
		if sprint_form.is_valid():
			
            # Save the user's form data to the database.
			sprint = sprint_form.save()
			sprint.save()
			           
            # Update our variable to tell the template registration was successful.
			registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
		else:
			print sprint_form.errors
			return render_to_response('scrumko/sprintcreate.html',{'sprint_form': sprint_form, 'registered': registered}, context)
	
	sprint_form = SprintCreateForm(initial={'project_name': r.id})		
		
    # Render the template depending on the context.
	return render_to_response('scrumko/sprintcreate.html',{'sprint_form': sprint_form, 'registered': registered}, context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
#@transaction.atomic
def projectcreate(request):
    # Like before, get the request's context.
	context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
	registered = False

    # If it's a HTTP POST, we're interested in processing form data.
	if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
  		project_form = ProjectCreateForm(data=request.POST)
  		
        # If the two forms are valid...
		if project_form.is_valid():
		
            # Save the user's form data to the database.
			scrum_master=User.objects.filter(id = int(request.POST.get('scrum_master')))
			scrum_master.update(is_staff = True)

			for member in scrum_master:
				member.save()
				print member

			project = project_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            			
			project.save()
			
			# check if is scrum master or team member
           
            # Update our variable to tell the template registration was successful.
			registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
		else:
			print project_form.errors
			return render_to_response('scrumko/projectcreate.html',{'project_form': project_form, 'registered': registered}, context)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
	
	project_form = ProjectCreateForm()
		
		
    # Render the template depending on the context.
	return render_to_response('scrumko/projectcreate.html',{'project_form': project_form, 'registered': registered}, context)

def maintainuser(request):
	context = RequestContext(request)
	user_info = User.objects.all()
	user_data = {"user_detail" : user_info}

	
    # Render the template depending on the context.
	return render_to_response('scrumko/maintainuser.html',user_data, context)
	
def maintainsprint(request):
	context = RequestContext(request)
	sprint_info = Sprint.objects.all()
	sprint_data = {"sprint_detail" : sprint_info}

	
    # Render the template depending on the context.
	return render_to_response('scrumko/maintainsprint.html',sprint_data, context)

def maintainproject(request):
	context = RequestContext(request)
	project_info = Project.objects.all()
	project_data = {"project_detail" : project_info}	
    # Render the template depending on the context.
	return render_to_response('scrumko/maintainproject.html', project_data, context)




@login_required

def storycreate(request):
    
    # get current user
	current_user = request.user.id
	
	# check on which project is this user owner or scrum master
	user_project_master =  Project.objects.filter(scrum_master__id = current_user, id = request.session['selected_project'])
	user_project_owner =  Project.objects.filter(project_owner__id = current_user, id = request.session['selected_project'])
    
    # check if user is scrum master or owner 
    # if not redirect (he has no permision to this site)
	if len (user_project_master) == 0 and len (user_project_owner) == 0:
		return HttpResponseRedirect("/scrumko/home")
	       
	context = RequestContext(request)
	registered = False
	if request.method == 'POST':
		story_form = StoryForm(data=request.POST)
  		
  				
		if story_form.is_valid():	    
			story = story_form.save()	    
									
				
			registered = True
		else:
			print story_form.errors
			return render_to_response('scrumko/storycreate.html',{'story_form': story_form, 'registered': registered}, context)
		
	# take project where user is scrum master or owner
	if len (user_project_master) > 0:
		r = user_project_master[0]
	elif len (user_project_owner) > 0:
		r = user_project_owner[0]
	
	# fill hidden with id of project
	story_form = StoryForm(initial={'project_name': r.id})
	
	return render_to_response('scrumko/storycreate.html',{'story_form': story_form, 'registered': registered}, context)

def edit(request):
	#manjka: preko seje pridobi uporabnika!
	context = RequestContext(request)
	registered = False
	if request.method == 'POST':
  		user_form = UserForm(data=request.POST)
  		profile_form = UserProfileForm(data=request.POST)
		
		if user_form.is_valid() and profile_form.is_valid():	    
			user = user_form.save()	    
			user.set_password(user.password)
			user.save()
			profile = profile_form.save(commit=False)
			profile.user = user

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			profile.save()
			registered = True
		else:
			print user_form.errors, profile_form.errors
			return render_to_response('scrumko/edit.html',{'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
	return render_to_response('scrumko/edit.html',{'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)
	
def poker(reques):
	context = RequestContext(request)
	
	
