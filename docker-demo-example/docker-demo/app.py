from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello from inside a Docker !!! container!"


if __name__ == "__main__":
    # host 0.0.0.0 lets the port mapping reach the app from your laptop
    app.run(host="0.0.0.0", port=8000, debug=True)
