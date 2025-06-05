from flask import Flask, render_template, request, redirect, url_for, render_template_string
import os
import re
import subprocess
import uuid
from werkzeug.utils import safe_join

app = Flask(__name__)
FILES_DIR = './files'

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


# Sanitizing to keep alphanumeric, dots, and hyphens only
def sanitize(ip:str) -> str:
    return re.sub(r'[^a-zA-Z0-9.\-]', '', ip)


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


# File upload and viewing
@app.route('/files', methods=['GET', 'POST'])
def files():
    file_content = ''
    filename = ''

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename:
            ext = os.path.splitext(uploaded_file.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(FILES_DIR, filename)
            uploaded_file.save(save_path)
            # Redirect to GET with filename as query param
            return redirect(url_for('files', file=filename))

    if request.method == 'GET' and 'file' in request.args:
        filename = request.args.get('file')
        print(f"Requested file: {filename}")
        
        # Validate filename to prevent directory traversal attacks
        # Ensure the filename is safe and exists
        safe_path = safe_join(FILES_DIR, filename)
        
        #print(f"Safe path: {safe_path}")
        if not safe_path or not os.path.isfile(safe_path):
            file_content = f"Error reading file."
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            file_content = f"Error reading file"

    return render_template('dashboard.html', show_section='files', filename=filename, file_content=file_content)

# File upload and viewing (unsafe copy)
@app.route('/filesunsafe', methods=['GET', 'POST'])
def filesunsafe():
    file_content = ''
    filename = ''

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        filename = uploaded_file.filename
        if uploaded_file and uploaded_file.filename:
            save_path = os.path.join(FILES_DIR, filename)
            uploaded_file.save(save_path)
            # Redirect to GET with filename as query param
            return redirect(url_for('filesunsafe', file=filename))

    if request.method == 'GET' and 'file' in request.args:
        filename = request.args.get('file')
        print(f"Requested file: {filename}")

        safe_path = FILES_DIR+"/"+filename
        print(f"Safe path: {safe_path}")
        if not safe_path or not os.path.isfile(safe_path):
            file_content = f"Error reading file."
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            file_content = f"Error reading file"

    return render_template('dashboard.html', show_section='filesunsafe', filename=filename, file_content=file_content)


@app.route('/list')
def list_files():
    try:
        files = os.listdir(FILES_DIR)
        files = [f for f in files if os.path.isfile(os.path.join(FILES_DIR, f))]  # Only list files
        print(f"Files in directory: {files}")
        return render_template('dashboard.html', show_section='list', files=files)
    except Exception as e:
        return render_template('dashboard.html', show_section='list', message=f"Error listing files")

if __name__ == '__main__':
    app.run(host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), debug=True)