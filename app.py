from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import os
import bcrypt
import subprocess

app = Flask(__name__)
app.secret_key = "AK-Nde*7dhnBkx-e21kdsK(dsk1nudJDJmcsiIJxs"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

PASSWORD_HASH_FILE = "password.hash"
VPN_SCRIPT = "openvpn-install.sh"  # CHANGE THIS to your script path

@app.before_first_request
def check_password():
    if not os.path.exists(PASSWORD_HASH_FILE):
        print("[*] No admin password found. Please set one:")
        pw = input("Set admin password: ").encode("utf-8")
        hashed = bcrypt.hashpw(pw, bcrypt.gensalt())
        with open(PASSWORD_HASH_FILE, "wb") as f:
            f.write(hashed)
        print("[*] Password saved.")

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")
        if username != "admin":
            error = "Invalid username"
        else:
            with open(PASSWORD_HASH_FILE, "rb") as f:
                hashed = f.read()
                if bcrypt.checkpw(password, hashed):
                    session["logged_in"] = True
                    return redirect("/dashboard")
                else:
                    error = "Invalid password"
    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/clients")
def clients():
    if not session.get("logged_in"):
        return redirect("/login")
    clients = []
    try:
        with open("/etc/openvpn/server/openvpn-status.log") as f:
            for line in f:
                if line.startswith("CLIENT_LIST"):
                    parts = line.strip().split(",")
                    clients.append(parts[1])
    except:
        pass
    return render_template("clients.html", clients=clients)

@app.route("/add-client", methods=["GET", "POST"])
def add_client():
    if not session.get("logged_in"):
        return redirect("/login")
    message = None
    if request.method == "POST":
        client_name = request.form["client_name"]
        # Run the angristan script non-interactively
        try:
            subprocess.run(
                ["sudo", VPN_SCRIPT],
                input=f"1\n{client_name}\n\n",
                text=True,
                check=True
            )
            message = f"Client {client_name} added successfully."
        except Exception as e:
            message = f"Error: {e}"
    return render_template("add_client.html", message=message)

@app.route("/remove-client", methods=["GET", "POST"])
def remove_client():
    if not session.get("logged_in"):
        return redirect("/login")
    message = None
    if request.method == "POST":
        client_name = request.form["client_name"]
        try:
            subprocess.run(
                ["sudo", VPN_SCRIPT],
                input=f"2\n{client_name}\n",
                text=True,
                check=True
            )
            message = f"Client {client_name} removed successfully."
        except Exception as e:
            message = f"Error: {e}"
    return render_template("remove_client.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1227)
