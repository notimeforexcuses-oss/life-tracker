
# ==========================================
# SCHEDULE & TIME BLOCKING
# ==========================================

def schedule_page(request):
    """
    Renders the main Schedule Interface.
    """
    from modules.tools_schedule import get_day_schedule, get_unscheduled_tasks
    
    date_str = request.GET.get('date', datetime.date.today().strftime("%Y-%m-%d"))
    
    # Calculate Nav
    current_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    prev_date = (current_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (current_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    date_display = current_date.strftime("%A, %B %d")
    
    # Fetch Data
    agenda_items = get_day_schedule(date_str)
    unscheduled_tasks = get_unscheduled_tasks()
    
    context = {
        'date_str': date_str,
        'date_display': date_display,
        'prev_date': prev_date,
        'next_date': next_date,
        'agenda_items': agenda_items,
        'unscheduled_tasks': unscheduled_tasks
    }
    return render(request, 'cockpit/schedule.html', context)

def render_agenda(request):
    """
    HTMX partial to refresh just the agenda list.
    """
    from modules.tools_schedule import get_day_schedule
    date_str = request.GET.get('date', datetime.date.today().strftime("%Y-%m-%d"))
    agenda_items = get_day_schedule(date_str)
    return render(request, 'cockpit/partials/schedule_agenda.html', {'agenda_items': agenda_items})

@csrf_exempt
@require_POST
def schedule_action(request):
    """
    Handles scheduling tasks or creating events via the modal.
    """
    from modules.tools_schedule import schedule_task_block, add_calendar_event
    
    action_type = request.POST.get('type') # 'task' or 'event'
    date_str = request.POST.get('date')
    start_time = request.POST.get('start_time')
    duration = int(request.POST.get('duration', 30))
    
    if action_type == 'task':
        task_id = request.POST.get('task_id')
        schedule_task_block(task_id, date_str, start_time, duration)
        
    elif action_type == 'event':
        title = request.POST.get('title')
        full_start_time = f"{date_str} {start_time}"
        add_calendar_event(title, full_start_time, duration)
    
    # Refresh Agenda
    return render_agenda(request)
