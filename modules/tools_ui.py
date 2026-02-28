# modules/tools_ui.py

def direct_browser(action: str, target_id: str = None, announcement: str = None, url: str = None):
    """
    Directly orchestrates the User Interface (Browser).
    action: 'focus', 'announce', 'navigate', 'close_chat'
    target_id: The HTML element ID to focus.
    announcement: The text for the screen reader to speak (aria-live).
    url: The destination path for navigation (e.g., '/memories').
    """
    # Intercepted by views.py
    return f"UI Command Queued: {action}"

def render_ui_component(component_type: str, data: dict):
    """
    Renders a pre-defined UI component into the chat window.
    component_type: 'summary_card', 'data_table'
    data: The JSON data required for the template.
    Example: render_ui_component('summary_card', {'title': 'Savings', 'value': '$1,200'})
    """
    # Intercepted by views.py
    return f"UI Component Queued: {component_type}"
