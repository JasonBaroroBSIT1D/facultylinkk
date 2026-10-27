"""Flask entrypoint for local development and `flask --app app run`."""

from factory import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
