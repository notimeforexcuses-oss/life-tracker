# Second Brain: AI System Manual & Architecture Map

This document outlines the architecture and file structure of the Second Brain project.

## 1. High-Level Overview

The "Second Brain" is a personal management system designed to be a comprehensive tool for organizing various aspects of life. It features a web-based interface and a powerful AI agent to manage tasks, contacts, notes, goals, and more.

## 2. Core Components

The application is divided into two main parts:

1.  **AI Backend (`brain_agent.py`)**: A powerful AI agent that can perform a wide range of tasks, from managing a calendar to tracking finances.
2.  **Web Interface (`second_brain_web/`)**: A Django-based web application that provides a user-friendly interface for interacting with the Second Brain.

## 3. File Breakdown

### 3.1. AI Backend

*   `brain_agent.py`: The core of the AI agent. It uses the Google Generative AI API to understand and respond to user requests. It can also use a variety of tools to perform tasks.
*   `modules/`: This directory contains all the tools that the AI agent can use. Each file in this directory corresponds to a specific tool, such as `tools_calendar.py`, `tools_tasks.py`, etc.

### 3.2. Web Interface

*   `second_brain_web/`: The root directory of the Django project.
*   `second_brain_web/cockpit/`: The main Django app that contains the models, views, and templates for the web interface.
*   `second_brain_web/cockpit/views.py`: This file contains the main logic for the web interface. It handles all the requests from the user and returns the appropriate responses.
*   `second_brain_web/cockpit/templates/`: This directory contains all the templates for the web interface.
    *   `cockpit/`: This subdirectory contains the main templates for the web interface.
        *   `base.html`: The base template that all other templates extend.
        *   `dashboard.html`: The template for the main dashboard.
        *   `tasks.html`: The template for the tasks page.
        *   `chat.html`: The template for the chat page.
    *   `partials/`: This subdirectory contains all the partial templates that are included in other templates. This allows for code reuse and makes the templates easier to maintain.
        *   `chat_message.html`: A partial template that displays a single chat message.
        *   `chat_panel.html`: A partial template that displays the chat panel.
        *   `create_item_modal.html`: A partial template that displays a modal for creating a new item.
        *   `goal_overview.html`: A partial template that displays an overview of a goal.
        *   `goal_settings_modal.html`: A partial template that displays a modal for editing goal settings.
        *   `project_overview.html`: A partial template that displays an overview of a project.
        *   `project_settings_modal.html`: A partial template that displays a modal for editing project settings.
        *   `task_item.html`: A partial template that displays a single task item.
        *   `task_list.html`: A partial template that displays a list of tasks.
        *   `task_modal.html`: A partial template that displays a modal for editing a task.

### 3.3. Data Management

*   `brain.db`: A SQLite database that stores all the data for the Second Brain.
*   `modules/database_utils.py`: A utility file that provides a connection to the `brain.db` database. This ensures that all tools can access the database in a consistent manner.
*   `modules/tools_*.py`: A collection of tools that the AI agent can use to interact with the database. These tools provide a high-level interface for creating, reading, updating, and deleting data. For example, the `tools_tasks.py` file contains functions for adding, completing, and deleting tasks.

### 3.4. Other Key Files

To ensure code quality and maintainabil ity, please follow these guidelines.

## 4. Interactions

The AI backend and the web interface are designed to work together seamlessly. The web interface provides a user-friendly way to interact with the AI agent, while the AI agent provides the intelligence and power to perform a wide range of tasks.

The user can interact with the AI agent through the web interface. The web interface sends requests to the AI agent, which then uses its tools to perform the requested task. The AI agent then returns the results to the web interface, which displays them to the user.
