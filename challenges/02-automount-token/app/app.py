import subprocess
from flask import Flask, request, render_template

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    country = request.form.get("country", "")
    # INTENTIONALLY VULNERABLE: unsanitised input passed to shell
    cmd = f"tail -n +2 /app/countries.csv | grep -i '^[^,]*{country}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    rows = [line.split(",") for line in result.stdout.splitlines() if line]
    error = result.stderr or ("(no results)" if not rows else None)
    return render_template("index.html", rows=rows, error=error, query=country)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
