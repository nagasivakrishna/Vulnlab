from flask import Flask, render_template, request, redirect, url_for
import os
import re
import subprocess

app = Flask(__name__)


# Sanitizing to keep alphanumeric, dots, and hyphens only
def sanitize(ip:str) -> str:
    return re.sub(r'[^a-zA-Z0-9.\-]', '', ip)


# Routes
@app.route('/', methods=['GET', 'PUT', 'POST'])
def home():        
    return redirect(url_for('landing'))

@app.route('/landing', methods=['GET','POST'])
def landing():
    return render_template('dashboard.html',show_section='landing')

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    return render_template('dashboard.html',show_section='pingunsafe')


# The first argument is a list so python does NOT run the command through a shell (like /bin/sh).
# Instead, it calls the program directly with the given arguments.
# Because there is no shell involved, shell metacharacters like ;, &&, |, backticks, $(), etc. have no special meaning.
# The arguments are passed to the executable ping only. Hence this is safe app.
@app.route('/pingsafe', methods=['GET', 'POST'])
def pingsafe():
    ip = request.form['ip']

    # sanitizing the ip only allowing alpha-numeric values, '.' and '-'
    # stripping away ;&|` 
    sanitized_ip = sanitize(ip)

    # uncomment below to see what is the sanitized_ip parameter being passed to the subprocess
    print(sanitized_ip)
    result = None
    if result is None:
        try:
            result = subprocess.check_output(["ping", "-c", "4", sanitized_ip], universal_newlines=True, stderr=subprocess.STDOUT)
        except:
            result = "error try again."
    return render_template('dashboard.html', show_section='pingsafe', result=result)


# Unsafe because it passes user input directly to os.system() without sanitization.
# This allows shell injection via special characters like ;, &, |, ` etc.
@app.route('/pingunsafe', methods=['GET', 'POST'])
def pingunsafe():
    try:
        ip = request.form['ip']
    except:
        ip = '127.0.0.1'
    result = None
    if result is None:
        try:
            os.system(f"{{ ping -c 4 {ip}; }} >> ./tmp.txt 2>&1")
            with open("./tmp.txt", "r+") as file:
                result = file.read()
                file.seek(0)
                file.truncate()
        except Exception as e:
            result = e.output
    return render_template('dashboard.html', show_section='pingunsafe', result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), debug=True)