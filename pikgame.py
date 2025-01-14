from datetime import timedelta

from flask import Flask, render_template, request, session, redirect
from flask_session import Session
import mysql.connector


app = Flask(__name__)
app.secret_key = "sdBahD$oJIDbs#d4nmvd*s7anN(54"
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=5)
Session(app)

SQL_SERVER = "127.0.0.1"


@app.route("/")
def home_view():
	""" Strona główna """
	return render_template("index.html")


@app.route("/zakup")
def zakupy_view(valid=True, warning=""):
	""" Strona kupowania gry """
	if valid:
		return render_template("buy.html")
	else:
		return render_template("buy.html", message=warning)

@app.route("/platnosc", methods=["POST", "GET"])
def platnosc_view():
	""" Strona oplacania zakupu """
	pik_wybrany = request.form.get("pik_wybrany")
	username = request.form["username"]
	password = request.form["passwd"]
	password_again = request.form["passwd_check"]
	email = request.form["email"]

	registry_items = {"usrname":username, "passwd":password, "email":email}

	if password != password_again or not password or not password_again:
		return zakupy_view(valid=False, warning="Wprowadzone hasło jest nieprawidłowe.")
	elif not email:
		return zakupy_view(valid=False, warning="Nie podano adresu email.")
	elif not username:
		return zakupy_view(valid=False, warning="Nie podano nazwy użytkownika.")
	elif len(password) < 8:
		return zakupy_view(valid=False, warning="Hasło powinno mnieć minimum 8 znaków.")
	elif not pik_wybrany:
		return zakupy_view(valid=False, warning="Nie wybrano produktu.")

	return zakup_dokonany_view(**registry_items)

@app.route("/zakup-dokonany")
def zakup_dokonany_view(usrname: str  = "", passwd: str  = "", email: str  = ""):
	""" Strona z podziękowaniami za kupienie gry """

	# Sprawdzanie poprawności danych
	if not usrname:
		return home_view()

	# Dodawanie usera od bazy danych
	try:
		db = mysql.connector.connect(
			host=SQL_SERVER,
			user="root",
			passwd="new_password",
			database="pikaccounts",
			auth_plugin='mysql_native_password'
		)

		kursor = db.cursor()
		kursor.execute(f"INSERT INTO accounts (username, email, passwd) VALUES ('{usrname}', '{email}', '{passwd}');")
		db.commit()
		db.disconnect()
		print(f"Added new user: {usrname}")

	except Exception as e:
		print(e)

	return render_template("finish.html")


@app.route("/zaloguj")
def zaloguj_view(valid=True, warning="Nie znaleziono użytkownika."):
	""" Strona z widokiem zarządzania konta """
	if valid:
		return render_template("login.html", message="")
	else:
		return render_template("login.html", message=warning)

@app.route("/moje-konto", methods=["POST", "GET"])
def moje_konto_view():
	""" Strona z widokiem zarządzania konta """

	# Walidacja formularza
	try:
		username_input = request.form["username"]
		password_input = request.form["passwd"]
		
		db = mysql.connector.connect(
			host=SQL_SERVER,
			user="root",
			passwd="new_password",
			database="pikaccounts",
			auth_plugin='mysql_native_password'
		)
		kursor = db.cursor()
		kursor.execute(r"SELECT username, passwd FROM accounts;")
		dane_uzytkownikow = kursor.fetchall()
		db.disconnect()

		for uzytkownik in dane_uzytkownikow:
			zgadza_sie_nazwa = (username_input == uzytkownik[0])
			zgadza_sie_haslo = (password_input == uzytkownik[1])

			if zgadza_sie_nazwa and zgadza_sie_haslo:
				session["zalogowano"] = True
				session["logged_user"] = uzytkownik[0]
				print("[Server] Znaleziono uzytkownika", uzytkownik[0])
				break
		else:
			return zaloguj_view(valid=False)

	except Exception as e:
		pass

	# Protekcja przed niezalogowanym dostępem
	if session.get("zalogowano"):
		pass
	else:
		return redirect("/zaloguj")

	return render_template("account.html",)


if __name__ == '__main__':
	app.run()

#  /home/dog/.local/lib/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so