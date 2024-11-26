from django.shortcuts import render, redirect
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from django.http import HttpResponseRedirect
from .models import Event, MyClubUser, Venue
# Import User Model From Django
from django.contrib.auth.models import User
from .forms import VenueForm, EventForm, EventFormAdmin
from django.http import HttpResponse
import csv
from django.contrib import messages

# Import PDF Stuff
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# Import Pagination Stuff
from django.core.paginator import Paginator


# Show Event
def show_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	return render(request, 'events/show_event.html', {
			"event":event
			})

# Show Events In A Venue
def venue_events(request, venue_id):
	# Grab the venue
	venue = Venue.objects.get(id=venue_id)	
	# Grab the events from that venue
	events = venue.event_set.all()
	if events:
		return render(request, 'events/venue_events.html', {
			"events":events
			})
	else:
		messages.success(request, ("That Venue Has No Events At This Time..."))
		return redirect('admin_approval')


# Create Admin Event Approval Page
def admin_approval(request):
	# Get The Venues
	venue_list = Venue.objects.all()
	# Get Counts
	event_count = Event.objects.all().count()
	venue_count = Venue.objects.all().count()
	user_count = User.objects.all().count()

	event_list = Event.objects.all().order_by('-event_date')
	if request.user.is_superuser:
		if request.method == "POST":
			# Get list of checked box id's
			id_list = request.POST.getlist('boxes')

			# Uncheck all events
			event_list.update(approved=False)

			# Update the database
			for x in id_list:
				Event.objects.filter(pk=int(x)).update(approved=True)
			
			# Show Success Message and Redirect
			messages.success(request, ("Event List Approval Has Been Updated!"))
			return redirect('list-events')



		else:
			return render(request, 'events/admin_approval.html',
				{"event_list": event_list,
				"event_count":event_count,
				"venue_count":venue_count,
				"user_count":user_count,
				"venue_list":venue_list})
	else:
		messages.success(request, ("You aren't authorized to view this page!"))
		return redirect('home')


	return render(request, 'events/admin_approval.html')

# Create My Events Page
def my_events(request):
	if request.user.is_authenticated:
		me = request.user.id
		events = Event.objects.filter(attendees=me)
		return render(request, 
			'events/my_events.html', {
				"events":events
			})

	else:
		messages.success(request, ("You Aren't Authorized To View This Page"))
		return redirect('home')

# Generate a PDF File Venue List
def venue_pdf(request):
	# Create Bytestream buffer
	buf = io.BytesIO()
	# Create a canvas
	c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
	# Create a text object
	textob = c.beginText()
	textob.setTextOrigin(inch, inch)
	textob.setFont("Helvetica", 14)

	# Add some lines of text
	#lines = [
	#	"This is line 1",
	#	"This is line 2",
	#	"This is line 3",
	#]
	
	# Designate The Model
	venues = Venue.objects.all()

	# Create blank list
	lines = []

	for venue in venues:
		lines.append(venue.name)
		lines.append(venue.address)
		lines.append(venue.zip_code)
		lines.append(venue.phone)
		lines.append(venue.web)
		lines.append(venue.email_address)
		lines.append(" ")

	# Loop
	for line in lines:
		textob.textLine(line)

	# Finish Up
	c.drawText(textob)
	c.showPage()
	c.save()
	buf.seek(0)

	# Return something
	return FileResponse(buf, as_attachment=True, filename='venue.pdf')

# Generate CSV File Venue List
def venue_csv(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename=venues.csv'
	
	# Create a csv writer
	writer = csv.writer(response)

	# Designate The Model
	venues = Venue.objects.all()

	# Add column headings to the csv file
	writer.writerow(['Venue Name', 'Address', 'Zip Code', 'Phone', 'Web Address', 'Email'])

	# Loop Thu and output
	for venue in venues:
		writer.writerow([venue.name, venue.address, venue.zip_code, venue.phone, venue.web, venue.email_address])

	return response



# Generate Text File Venue List
def venue_text(request):
	response = HttpResponse(content_type='text/plain')
	response['Content-Disposition'] = 'attachment; filename=venues.txt'
	# Designate The Model
	venues = Venue.objects.all()

	# Create blank list
	lines = []
	# Loop Thu and output
	for venue in venues:
		lines.append(f'{venue.name}\n{venue.address}\n{venue.zip_code}\n{venue.phone}\n{venue.web}\n{venue.email_address}\n\n\n')

	#lines = ["This is line 1\n", 
	#"This is line 2\n",
	#"This is line 3\n\n",
	#"John Elder Is Awesome!\n"]

	# Write To TextFile
	response.writelines(lines)
	return response

# Delete a Venue
def delete_venue(request, venue_id):
	venue = Venue.objects.get(pk=venue_id)
	venue.delete()
	return redirect('list-venues')		


# Delete an Event
def delete_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	if request.user == event.manager:
		event.delete()
		messages.success(request, ("Event Deleted!!"))
		return redirect('list-events')		
	else:
		messages.success(request, ("You Aren't Authorized To Delete This Event!"))
		return redirect('list-events')		

def add_event(request):
	submitted = False
	if request.method == "POST":
		if request.user.is_superuser:
			form = EventFormAdmin(request.POST)
			if form.is_valid():
					form.save()
					return 	HttpResponseRedirect('/add_event?submitted=True')	
		else:
			form = EventForm(request.POST)
			if form.is_valid():
				#form.save()
				event = form.save(commit=False)
				event.manager = request.user # logged in user
				event.save()
				return 	HttpResponseRedirect('/add_event?submitted=True')	
	else:
		# Just Going To The Page, Not Submitting 
		if request.user.is_superuser:
			form = EventFormAdmin
		else:
			form = EventForm

		if 'submitted' in request.GET:
			submitted = True

	return render(request, 'events/add_event.html', {'form':form, 'submitted':submitted})


def update_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	if request.user.is_superuser:
		form = EventFormAdmin(request.POST or None, instance=event)	
	else:
		form = EventForm(request.POST or None, instance=event)
	
	if form.is_valid():
		form.save()
		return redirect('list-events')

	return render(request, 'events/update_event.html', 
		{'event': event,
		'form':form})


def update_venue(request, venue_id):
	venue = Venue.objects.get(pk=venue_id)
	form = VenueForm(request.POST or None, request.FILES or None, instance=venue)
	if form.is_valid():
		form.save()
		return redirect('list-venues')

	return render(request, 'events/update_venue.html', 
		{'venue': venue,
		'form':form})

def search_venues(request):
	if request.method == "POST":
		searched = request.POST['searched']
		venues = Venue.objects.filter(name__contains=searched)
	
		return render(request, 
		'events/search_venues.html', 
		{'searched':searched,
		'venues':venues})
	else:
		return render(request, 
		'events/search_venues.html', 
		{})


def search_events(request):
	if request.method == "POST":
		searched = request.POST['searched']
		events = Event.objects.filter(description__contains=searched)
	
		return render(request, 
		'events/search_events.html', 
		{'searched':searched,
		'events':events})
	else:
		return render(request, 
		'events/search_events.html', 
		{})


def show_venue(request, venue_id):
	venue = Venue.objects.get(pk=venue_id)
	venue_owner = User.objects.get(pk=venue.owner)

	# Grab the events from that venue
	events = venue.event_set.all()

	return render(request, 'events/show_venue.html', 
		{'venue': venue,
		'venue_owner':venue_owner,
		'events':events})

def list_venues(request):
	#venue_list = Venue.objects.all().order_by('?')
	venue_list = Venue.objects.all()

	# Set up Pagination
	p = Paginator(Venue.objects.all(), 3)
	page = request.GET.get('page')
	venues = p.get_page(page)
	nums = "a" * venues.paginator.num_pages
	return render(request, 'events/venue.html', 
		{'venue_list': venue_list,
		'venues': venues,
		'nums':nums}
		)

def add_venue(request):
	submitted = False
	if request.method == "POST":
		form = VenueForm(request.POST, request.FILES)
		if form.is_valid():
			venue = form.save(commit=False)
			venue.owner = request.user.id # logged in user
			venue.save()
			#form.save()
			return 	HttpResponseRedirect('/add_venue?submitted=True')	
	else:
		form = VenueForm
		if 'submitted' in request.GET:
			submitted = True

	return render(request, 'events/add_venue.html', {'form':form, 'submitted':submitted})

def all_events(request):
	event_list = Event.objects.all().order_by('-event_date')
	return render(request, 'events/event_list.html', 
		{'event_list': event_list})


def home(request):
    # Get the current date
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime('%B')

    # Get year and month from GET parameters or use current values
    year = int(request.GET.get('year', current_year))  # Convert to int
    month = request.GET.get('month', current_month)  # Get month as string

    # If month is a number (string), convert it to month name
    if month.isdigit():
        month_number = int(month)
        month_name = calendar.month_name[month_number]
    else:
        month_name = month.capitalize()
        month_number = list(calendar.month_name).index(month_name)

    # Create a calendar
    cal = HTMLCalendar().formatmonth(year, month_number)

    # Query the Events Model For Dates
    event_list = Event.objects.filter(
        event_date__year=year,
        event_date__month=month_number
    )

    # Get current time
    time = now.strftime('%I:%M %p')

    # Prepare the context for rendering
    context = {
        "name": "John",
        "year": year,
        "month": month_name,
        "month_number": month_number,
        "cal": cal,
        "current_year": current_year,
        "time": time,
        "event_list": event_list,
        "months": dict(enumerate(calendar.month_name[1:], start=1)),  # For month selection dropdown
        "years": range(current_year - 5, current_year + 6),  # Example range of years
        "selected_month": month_number,
        "selected_year": year,
        "month_name": month_name,
        "no_events_message": "No events scheduled for this period." if not event_list else ""
    }

    return render(request, 'events/home.html', context)



from django.db.models import Count
from .models import Event, Venue, User

import matplotlib.pyplot as plt
import io
import base64

def analytics_view(request):
    # Query events and count attendees
    events = Event.objects.annotate(attendee_count=Count('attendees')).order_by('-attendee_count')[:10]
    
    # Extract data for the graph
    event_names = [event.name for event in events]
    attendee_counts = [event.attendee_count for event in events]

    # Generate the graph
    plt.figure(figsize=(10, 6))
    plt.bar(event_names, attendee_counts, color='skyblue')
    plt.title('Top 10 Events by Attendee Count', fontsize=14)
    plt.xlabel('Event Name', fontsize=12)
    plt.ylabel('Attendee Count', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the graph to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_url = base64.b64encode(buf.getvalue()).decode('utf8')
    buf.close()

    # Pass the data and graph URL to the template
    context = {
        'events': events,
        'graph_url': f"data:image/png;base64,{graph_url}"
    }
    return render(request, 'events/analytics_dashboard.html', context)



from django.db.models import Count

def top_users_view(request):
    # Query for top creators
    top_creators = (
        User.objects.annotate(event_count=Count('event'))
        .order_by('-event_count')[:5]
    )

    # Query for top attendees
    top_attendees = (
        MyClubUser.objects.annotate(event_count=Count('event'))
        .order_by('-event_count')[:5]
    )

    context = {
        'top_creators': top_creators,
        'top_attendees': top_attendees,
    }
    return render(request, 'events/top_users.html', context)

