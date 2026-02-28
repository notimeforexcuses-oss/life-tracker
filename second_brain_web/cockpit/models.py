from django.db import models
from datetime import datetime, date

class Areas(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'areas'


class Memories(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'memories'


class Goals(models.Model):
    id = models.AutoField(primary_key=True)
    # New Relationship: Link to Area
    area = models.ForeignKey(
        Areas,
        on_delete=models.SET_NULL,
        null=True,
        db_column='area_id',
        related_name='goals'
    )
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    motivation = models.TextField(blank=True, null=True)
    target_date = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    @property
    def date_status_class(self):
        """Returns CSS classes based on deadline proximity."""
        if not self.target_date:
            return "bg-white text-blue-700 border-blue-100"
        
        try:
            target = datetime.strptime(self.target_date, "%Y-%m-%d").date()
            today = date.today()
            delta = (target - today).days
            
            if delta < 0:
                return "bg-red-50 text-red-700 border-red-200 font-bold" # Overdue
            elif delta <= 7:
                return "bg-orange-50 text-orange-800 border-orange-200 font-semibold" # Urgent
            else:
                return "bg-white text-blue-700 border-blue-100" # Normal
        except:
            return "bg-gray-50 text-gray-600 border-gray-200"

    class Meta:
        managed = False
        db_table = 'goals'


class Projects(models.Model):
    id = models.AutoField(primary_key=True)
    goal = models.ForeignKey(
        Goals,
        on_delete=models.SET_NULL,
        null=True,
        db_column='goal_id',
        related_name='projects'
    )
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    priority = models.TextField(blank=True, null=True)
    percent_complete = models.IntegerField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    @property
    def progress_color(self):
        """Returns a Tailwind color class based on completion percentage."""
        pc = self.percent_complete or 0
        if pc >= 100: return "bg-green-500"
        if pc >= 75: return "bg-green-400"
        if pc >= 40: return "bg-blue-500"
        if pc >= 20: return "bg-yellow-400"
        return "bg-red-400"

    @property
    def priority_border(self):
        """Returns a Tailwind border class based on priority."""
        if self.priority == 'High': return "border-l-4 border-l-red-500"
        if self.priority == 'Medium': return "border-l-4 border-l-blue-400"
        return "border-l-4 border-l-gray-300"

    class Meta:
        managed = False
        db_table = 'projects'


class Contacts(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    relationship = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    organization = models.TextField(blank=True, null=True)
    last_contact_date = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    # New fields found in DB
    address = models.TextField(blank=True, null=True)
    address_street = models.TextField(blank=True, null=True)
    address_city = models.TextField(blank=True, null=True)
    address_state = models.TextField(blank=True, null=True)
    address_zip = models.TextField(blank=True, null=True)
    tier = models.TextField(blank=True, null=True)
    job_title = models.TextField(blank=True, null=True)
    next_contact_date = models.TextField(blank=True, null=True)
    linkedin_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contacts'


class ContactDetails(models.Model):
    id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contacts, on_delete=models.CASCADE, db_column='contact_id')
    type = models.TextField(blank=True, null=True)
    value = models.TextField(blank=True, null=True)
    label = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contact_details'


class Tasks(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    due_date = models.TextField(blank=True, null=True)
    is_recurring = models.IntegerField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(
        Projects,
        on_delete=models.SET_NULL,
        null=True,
        db_column='linked_project_id',
        related_name='tasks'
    )
    linked_goal = models.ForeignKey(
        Goals,
        on_delete=models.SET_NULL,
        null=True,
        db_column='linked_goal_id',
        related_name='tasks_by_goal'
    )
    linked_contact = models.ForeignKey(
        Contacts,
        on_delete=models.SET_NULL,
        null=True,
        db_column='linked_contact_id',
        related_name='tasks_by_contact'
    )
    priority = models.TextField(blank=True, null=True)

    @property
    def is_overdue(self):
        if not self.due_date: return False
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
            return due < date.today()
        except:
            return False

    class Meta:
        managed = False
        db_table = 'tasks'


class Notes(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    updated_at = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    linked_goal = models.ForeignKey(Goals, on_delete=models.SET_NULL, null=True, db_column='linked_goal_id')
    linked_contact = models.ForeignKey(Contacts, on_delete=models.SET_NULL, null=True, db_column='linked_contact_id', related_name='notes_by_contact')

    class Meta:
        managed = False
        db_table = 'notes'


class JournalEntries(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    time = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    linked_goal = models.ForeignKey(Goals, on_delete=models.SET_NULL, null=True, db_column='linked_goal_id')
    linked_contact = models.ForeignKey(Contacts, on_delete=models.SET_NULL, null=True, db_column='linked_contact_id')
    linked_task = models.ForeignKey(Tasks, on_delete=models.SET_NULL, null=True, db_column='linked_task_id')

    class Meta:
        managed = False
        db_table = 'journal_entries'


class Interactions(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    contact = models.ForeignKey(Contacts, on_delete=models.SET_NULL, null=True, db_column='contact_id')
    type = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    linked_goal = models.ForeignKey(Goals, on_delete=models.SET_NULL, null=True, db_column='linked_goal_id')

    class Meta:
        managed = False
        db_table = 'interactions'


class DailyMetrics(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    sleep_hours = models.FloatField(blank=True, null=True)
    sleep_quality = models.IntegerField(blank=True, null=True)
    morning_mood = models.IntegerField(blank=True, null=True)
    readiness_score = models.IntegerField(blank=True, null=True)
    stress_level = models.IntegerField(blank=True, null=True)
    productivity_score = models.IntegerField(blank=True, null=True)
    evening_mood = models.IntegerField(blank=True, null=True)
    diet_quality = models.IntegerField(blank=True, null=True)
    water_intake = models.IntegerField(default=0) # New Field
    win_of_the_day = models.TextField(blank=True, null=True)
    primary_obstacle = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    linked_goal = models.ForeignKey(Goals, on_delete=models.SET_NULL, null=True, db_column='linked_goal_id')
    hrv = models.IntegerField(blank=True, null=True)
    resting_hr = models.IntegerField(blank=True, null=True)
    sleep_deep_min = models.IntegerField(default=0)
    sleep_rem_min = models.IntegerField(default=0)
    sleep_light_min = models.IntegerField(default=0)
    sleep_awake_min = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'daily_metrics'


class Workouts(models.Model):
    id = models.AutoField(primary_key=True)
    start_datetime = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    duration_min = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'workouts'


class WorkoutTemplates(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    last_used = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'workout_templates'


class Exercises(models.Model):
    id = models.AutoField(primary_key=True)
    workout = models.ForeignKey(Workouts, on_delete=models.CASCADE, db_column='workout_id', related_name='exercises_set')
    template = models.ForeignKey(WorkoutTemplates, on_delete=models.CASCADE, db_column='template_id', blank=True, null=True, related_name='exercises')
    name = models.TextField(blank=True, null=True)
    sets = models.IntegerField(blank=True, null=True)
    reps = models.TextField(blank=True, null=True)
    weight = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, db_column='exercise_order')

    class Meta:
        managed = False
        db_table = 'exercises'


class WorkoutSets(models.Model):
    id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercises, on_delete=models.CASCADE, db_column='exercise_id', related_name='workout_sets')
    set_number = models.IntegerField(blank=True, null=True)
    reps = models.IntegerField(default=0)
    weight = models.FloatField(default=0.0)
    is_completed = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'workout_sets'


class NutritionLogs(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    food_item = models.TextField(blank=True, null=True)
    calories = models.IntegerField(blank=True, null=True)
    protein_g = models.IntegerField(blank=True, null=True)
    carbs_g = models.IntegerField(blank=True, null=True)
    fat_g = models.IntegerField(blank=True, null=True)
    meal_type = models.TextField(blank=True, null=True)
    # Micros
    fiber_g = models.IntegerField(default=0)
    sugar_g = models.IntegerField(default=0)
    sodium_mg = models.IntegerField(default=0)
    cholesterol_mg = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'nutrition_logs'


class MealLibrary(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    default_calories = models.IntegerField(blank=True, null=True)
    default_protein = models.IntegerField(blank=True, null=True)
    default_carbs = models.IntegerField(blank=True, null=True)
    default_fat = models.IntegerField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    # Micros
    default_fiber = models.IntegerField(default=0)
    default_sugar = models.IntegerField(default=0)
    default_sodium = models.IntegerField(default=0)
    default_cholesterol = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'meal_library'


class TimelineBlocks(models.Model):
    id = models.AutoField(primary_key=True)
    activity = models.TextField(blank=True, null=True)
    start_datetime = models.TextField(blank=True, null=True)
    end_datetime = models.TextField(blank=True, null=True)
    workout = models.ForeignKey(Workouts, on_delete=models.SET_NULL, null=True, db_column='workout_id')
    project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='project_id')
    task = models.ForeignKey(Tasks, on_delete=models.SET_NULL, null=True, db_column='task_id')
    interaction = models.ForeignKey(Interactions, on_delete=models.SET_NULL, null=True, db_column='interaction_id')

    class Meta:
        managed = False
        db_table = 'timeline_blocks'


class ProposedAutomations(models.Model):
    id = models.AutoField(primary_key=True)
    trigger_condition = models.TextField(blank=True, null=True)
    proposed_action = models.TextField(blank=True, null=True)
    recurrence = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proposed_automations'


class FlexibleTracker(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    metric = models.TextField(blank=True, null=True)
    value = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    linked_contact = models.ForeignKey(Contacts, on_delete=models.SET_NULL, null=True, db_column='linked_contact_id')

    class Meta:
        managed = False
        db_table = 'flexible_tracker'


class Transactions(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    linked_timeline = models.ForeignKey(TimelineBlocks, on_delete=models.SET_NULL, null=True, db_column='linked_timeline_id')
    linked_nutrition = models.ForeignKey(NutritionLogs, on_delete=models.SET_NULL, null=True, db_column='linked_nutrition_id')

    class Meta:
        managed = False
        db_table = 'transactions'


class Resources(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'resources'


class TaskUpdates(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, db_column='task_id')
    date = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    confidence_level = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'task_updates'


class Budgets(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.TextField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    period = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')
    last_updated = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'budgets'


class FocusLogs(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.TextField(blank=True, null=True)
    time = models.TextField(blank=True, null=True)
    focus_level = models.IntegerField(blank=True, null=True)
    energy_level = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    linked_project = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, db_column='linked_project_id')

    class Meta:
        managed = False
        db_table = 'focus_logs'

class InteractionParticipants(models.Model):
    id = models.AutoField(primary_key=True)
    interaction = models.ForeignKey(Interactions, on_delete=models.CASCADE, db_column='interaction_id')
    contact = models.ForeignKey(Contacts, on_delete=models.CASCADE, db_column='contact_id')

    class Meta:
        managed = False
        db_table = 'interaction_participants'

class ProjectStakeholders(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project_id')
    contact = models.ForeignKey(Contacts, on_delete=models.CASCADE, db_column='contact_id')
    role = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'project_stakeholders'


class TaskAssignees(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, db_column='task_id')
    contact = models.ForeignKey(Contacts, on_delete=models.CASCADE, db_column='contact_id')
    role = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'task_assignees'


class GoalParticipants(models.Model):
    id = models.AutoField(primary_key=True)
    goal = models.ForeignKey(Goals, on_delete=models.CASCADE, db_column='goal_id')
    contact = models.ForeignKey(Contacts, on_delete=models.CASCADE, db_column='contact_id')
    role = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'goal_participants'


class MemoryLinks(models.Model):
    id = models.AutoField(primary_key=True)
    source_id = models.IntegerField()
    source_type = models.CharField(max_length=20) # 'note' or 'journal'
    target_id = models.IntegerField()
    target_type = models.CharField(max_length=20) # 'note' or 'journal'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'memory_links'


class NoteAttachments(models.Model):


    id = models.AutoField(primary_key=True)


    note = models.ForeignKey(Notes, on_delete=models.CASCADE, db_column='note_id', related_name='attachments')


    file_name = models.TextField()


    file_path = models.TextField()


    file_type = models.TextField()


    uploaded_at = models.TextField()





    class Meta:


        managed = False


        db_table = 'note_attachments'





class ChatSessions(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    is_archived = models.IntegerField(default=0)
    tags = models.TextField(blank=True, null=True)
    linked_goal_id = models.IntegerField(blank=True, null=True)
    linked_project_id = models.IntegerField(blank=True, null=True)
    linked_contact_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chat_sessions'


class ChatMessages(models.Model):
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(ChatSessions, on_delete=models.CASCADE, db_column='session_id', related_name='messages')
    role = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tool_usage = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chat_messages'

class SystemNotifications(models.Model):


    id = models.AutoField(primary_key=True)


    type = models.TextField()


    content = models.TextField()


    severity = models.TextField()


    created_at = models.TextField()


    is_read = models.IntegerField(default=0)





    class Meta:


        managed = False


        db_table = 'system_notifications'

