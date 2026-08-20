# EventFlow Simple

This is the beginner version of EventFlow. The Python code is kept in only three files:

- `app.py` contains the website pages and main logic.
- `models.py` contains the classes.
- `helpers.py` contains files, recursion, weather and reminders.

Organizers can choose a basic event category or select `Other` and type their own category.

## Run on Windows

Extract the ZIP and open the extracted folder. Click the File Explorer address bar, type `cmd` and press Enter.

Run these commands one at a time:

```text
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000`.

## Test

```text
venv\Scripts\python.exe -m pytest -q
```

The result should say `2 passed`.

## Test Reminders and Weather

1. Create an organizer account.
2. Create an event about two hours ahead.
3. Use `Accra, Ghana` as the location.
4. Log out and create a participant account.
5. Register for the event.
6. Open Dashboard to see the reminder and notification pop-up.

The organizer chooses the reminder time while creating the event.

## Requirements Covered

- OOP: User, Organizer, Participant, Event, Ticket and Registration classes
- Files: JSON files
- Collections: lists, dictionaries and sets
- Loops: events, tickets, attendance and reminders
- Conditionals: if/elif/else, match/case and ternary
- Functions: routes and helper functions
- Libraries: Flask and requests
- API: Open-Meteo weather and location
- Recursion: copy_categories
- GUI: HTML and CSS

## Make It Live

### Upload to GitHub

1. Create a new empty GitHub repository called `eventflow-simple`.
2. Open the extracted project folder and select everything inside it.
3. On GitHub, choose `Add file`, then `Upload files`.
4. Drag the selected files and folders onto the page.
5. Enter `Upload EventFlow` as the message and commit the files.

Make sure `app.py`, `models.py`, `helpers.py`, `templates` and `static` appear on the first repository page.

### Use GitHub Codespaces

1. Open the repository and click `Code`.
2. Open `Codespaces` and create a codespace on `main`.
3. Run these commands in its terminal:

```text
python -m pip install -r requirements.txt
python app.py
```

4. Open the port 5000 link that appears.

For a temporary shareable link, open the `Ports` panel, right-click port 5000, change its visibility to `Public` and copy its address. The codespace and Python program must remain running.

Save changes with:

```text
git add .
git commit -m "Update EventFlow"
git push
```

### Deploy with Render

1. Sign in to Render using GitHub.
2. Create a new Web Service and select the repository.
3. Choose Python and the Free instance.
4. Use `pip install -r requirements.txt` as the build command.
5. Use `gunicorn app:app` as the start command.
6. Deploy and open the generated website link.

The free Render service can reset JSON data when it restarts. It is suitable for a class demonstration, but not permanent data storage.
