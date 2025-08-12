from flask import Flask
import os


app = Flask(__name__)


@app.route("/")
def index():
    version = os.getenv("APP_VERSION", "0.1.0")
    return f"Hello from GitOps Demo v{version}\n"


@app.route("/healthz")
def healthz():
    return "ok\n"


@app.route("/readyz")
def readyz():
    return "ready\n"


if __name__ == "__main__":
    # Listen on port 8080 and on all interfaces. The image runs as a non-root user.
    app.run(host="0.0.0.0", port=8080)




