from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from cockpit import views

urlpatterns = [
    # --- DASHBOARD & NAVIGATION ---
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks_page, name='tasks_page'),
    path('projects/', views.projects_page, name='projects_page'),
    path('contacts/', views.contacts_page, name='contacts_page'),
    
    # --- SCHEDULE ---
    path('schedule/', views.schedule_page, name='schedule_page'),
    path('api/schedule/render/', views.render_agenda, name='render_agenda'),
    path('api/schedule/action/', views.schedule_action, name='schedule_action'),

    # --- RENDER FRAGMENTS ---
    path('api/render_global_view/', views.render_global_view, name='render_global_view'),
    path('api/render_project_stage/<int:project_id>/', views.render_project_stage, name='render_project_stage'),
    path('api/goals/<int:goal_id>/projects/', views.render_goal_projects, name='render_goal_projects'),
    
    # --- CREATION ---
    path('api/render_create_modal/', views.render_create_modal, name='render_create_modal'),
    path('api/process_create_item/', views.process_create_item, name='process_create_item'),
    path('api/projects/create/', views.create_project, name='create_project'),
    path('api/tasks/create/', views.create_task, name='create_task'),
    
    # --- TASKS ---
    path('api/tasks/<int:task_id>/detail/', views.task_detail, name='task_detail'),
    path('api/tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('api/tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('api/tasks/save_details/', views.save_task_details, name='save_task_details'),
    
    # --- PROJECTS & GOALS ---
    path('api/projects/<int:project_id>/settings/', views.render_project_settings, name='render_project_settings'),
    path('api/projects/<int:project_id>/update/', views.update_project, name='update_project'),
    path('api/projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    
    path('api/projects/<int:project_id>/settings/', views.render_project_settings, name='render_project_settings'),
    path('api/projects/<int:project_id>/update/', views.update_project, name='update_project'),
    path('api/projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('api/areas/<int:area_id>/delete/', views.delete_area, name='delete_area'),
    
    path('api/goals/<int:goal_id>/settings/', views.render_goal_settings, name='render_goal_settings'),
    path('api/goals/<int:goal_id>/update/', views.update_goal, name='update_goal'),

    # --- MEMORIES ---
    path('memories/', views.memories_page, name='memories_page'),
    path('api/memories/content/', views.render_memories_content, name='render_memories_content'),
    path('api/memories/modal/', views.render_memory_modal, name='render_memory_modal'),
    path('api/memories/save/', views.save_memory_item, name='save_memory_item'),
    path('api/memories/delete/', views.delete_memory_item, name='delete_memory_item'),
    path('api/memories/quick_journal/', views.process_quick_journal, name='process_quick_journal'),

    # --- HEALTH ---
    path('health/', views.health_page, name='health_page'),
    path('api/health/content/', views.render_health_content, name='render_health_content'),
    path('api/health/modal/', views.render_health_modal, name='render_health_modal'),
    path('api/health/template/<int:template_id>/', views.get_template_details, name='get_template_details'),
    path('api/health/save/', views.save_health_item, name='save_health_item'),
    path('api/health/water/update/', views.update_water, name='update_water'),
    path('api/health/nutrition/estimate/', views.estimate_nutrition, name='estimate_nutrition'),
    path('api/health/meal/<int:meal_id>/duplicate/', views.duplicate_meal, name='duplicate_meal'),

    # --- CHAT AGENT ---
    path('chat/', views.chat_page, name='chat_page'),
    path('api/chat/new/', views.new_chat, name='new_chat'),
    path('api/chat/delete/<int:session_id>/', views.delete_chat, name='delete_chat'),
    path('api/chat/history/search/', views.search_chat_history, name='search_chat_history'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/render_chat_panel/', views.render_chat_panel, name='render_chat_panel'),
    path('api/chat/clear/', views.clear_chat, name='clear_chat'),
    path('api/search/', views.search_api, name='search_api'),

    # --- CONTACTS & INTERACTIONS ---
    path('api/contacts/<int:contact_id>/', views.get_contact_details, name='get_contact_details'),
    path('api/contacts/create/', views.render_create_contact_modal, name='render_create_contact_modal'),
    path('api/contacts/add/', views.add_contact, name='add_contact'),
    path('api/contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
    path('api/contacts/<int:contact_id>/log/', views.log_interaction, name='log_interaction'),
    path('api/interactions/log_modal/', views.render_log_interaction_modal, name='render_log_interaction_modal'),
    path('api/interactions/process/', views.process_standalone_interaction, name='process_standalone_interaction'),
    
    # --- ASSIGNMENTS ---
    path('api/assign/<str:entity_type>/<int:entity_id>/', views.manage_assignment, name='manage_assignment'),
    path('api/assign/<str:entity_type>/<int:entity_id>/remove/<int:contact_id>/', views.remove_assignment, name='remove_assignment'),
    path('api/contacts/<int:contact_id>/assign/', views.assign_to_work, name='assign_to_work'),
    path('api/contacts/<int:contact_id>/unassign/', views.unassign_from_work, name='unassign_from_work'),
    
    # --- PROACTIVE NOTIFICATIONS & PROPOSALS ---
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/proposals/', views.get_proposals, name='get_proposals'),
    path('api/proposals/<int:prop_id>/act/', views.act_on_proposal, name='act_on_proposal'),
    
    # --- BATCH OPS ---
    path('contacts/batch/delete/', views.batch_delete_contacts, name='batch_delete_contacts'),
    path('contacts/batch/interaction_modal/', views.render_batch_interaction_modal, name='render_batch_interaction_modal'),
    path('contacts/batch/log/', views.batch_log_interaction, name='batch_log_interaction'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
