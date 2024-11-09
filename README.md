# Academic Assistant

## Overview
Academic Assistant is a Django-based web application designed to streamline academic tasks through features such as interactive chat with AI, file management, quizzes, and summaries generation. The application enables users to upload documents and engage with AI for instant insights and structured study plans.

## Features
- **Interactive Chat**: Engage in discussions, ask questions, and get summaries from uploaded files.
- **Context Files Management**: Upload and reference documents (PDFs and TXT files) within your chats.
- **Quizzes Creation**: Automatically generate quizzes based on content files with customizable parameters.
- **Summaries Generation**: Create markdown-formatted summaries from uploaded documents.
- **Study Plans**: Develop and monitor structured study plans based on user-defined goals.

## Technologies Used
- **Backend**: Django 5.x
- **Database**: PostgreSQL (or SQLite for development)
- **Frontend**: Bootstrap 5 for responsive design
- **Other Libraries**: Django REST Framework, Crispy Forms, OpenAI API, Django Tables2

## Installation

### Prerequisites
- Python 3.11 or higher
- PostgreSQL or SQLite for database
- Docker (optional, for containerized setup)

### Clone the Repository
```bash
git clone https://github.com/HadsyC/Academic-Assistant.git
cd Academic-Assistant
```

### Create and Activate Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Database Setup

Make sure to take a look into `example.env`, for the reset command to work you need to define the variables correctly.

1. **Run Migrations**: 
    Use the custom management command to reset the database, delete migration files, create a new migration, and create a superuser.

    ```bash
    python manage.py reset
    ```

2. **Create Superuser**: 
    The reset command already creates a superuser, but if you need to create one manually, you can run:
    ```bash
    python manage.py createsuperuser
    ```

### Running the Application
```bash
python manage.py runserver
```

### Building with Docker (Optional)
Then, run the container using:
```bash
docker-compose up
```

## Usage
1. Access the application at `http://localhost:8000/`.
2. Sign up or log in using your credentials.
3. Use the chat interface to engage with AI by uploading documents, creating quizzes, or generating summaries.

## Running Tests
To run the tests included in the application:
```bash
python manage.py test
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions welcomed!

## Acknowledgements
- OpenAI for providing the AI functionalities.
- Django community for their amazing framework.