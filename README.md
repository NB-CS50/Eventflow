# EventFlow

EventFlow is a Flask website for creating and joining events.

Organizers create events and manage attendees. Participants find events, register and receive digital tickets.

## Main features

- Event creation and registration
- Organizer and participant accounts
- Digital ticket codes and attendance checking
- Event reminders
- Live weather information
- Ticket sales and attendee records

## Run on Windows

Open Command Prompt inside the project folder. Run each command separately:

```text
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

If `python` does not work, use `py` instead.

## Test the project

```text
python -m pytest -q
```

The result should say `4 passed`.

## Put it online

1. Upload the project files to GitHub.
2. Create a Web Service on Render.
3. Connect the GitHub repository.
4. Use `pip install -r requirements.txt` as the build command.
5. Use `gunicorn app:app` as the start command.
6. Deploy the website.

## Course requirements

The project includes OOP, files, collections, loops, conditionals, functions, imported libraries, APIs, recursion and an HTML GUI.
