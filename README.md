# FireTools

FireTools is a collection of small utilities built with Flask. The application exposes a set of tools such as PDF splitting, URL shortening, image and video conversion, and several YouTube helpers. The tools are loaded dynamically as Flask blueprints from the `tools/` directory.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

The `video_converter` tool requires the `moviepy` library. It is listed in
`requirements.txt`, so ensure all dependencies are installed before running the
application.

## Environment Variables

- `SECRET_KEY` – secret key used by Flask for sessions and CSRF protection. If not provided the application generates a random key on startup.
- `PORT` – port for `python app.py` to listen on. Defaults to `4666`.

Set these in your environment before running the application as needed.

## Running

After installing the dependencies and setting optional variables, start the application with:

```bash
python app.py
```
