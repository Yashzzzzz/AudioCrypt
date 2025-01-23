import os
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pymongo import MongoClient
import bcrypt
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Flask app setup
app = Flask(__name__)
app.secret_key ='SECRET_KEY'
s = URLSafeTimedSerializer(app.secret_key)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['audio_encryptor']
users_collection = db['users']

# Directories
UPLOAD_FOLDER = 'uploads'
DECRYPTED_FOLDER = 'decrypted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Utility functions
def generate_symmetric_key():
    """Generate a symmetric key using ECDH."""
    private_key_a = ec.generate_private_key(ec.SECP256R1())
    private_key_b = ec.generate_private_key(ec.SECP256R1())
    shared_secret = private_key_a.exchange(ec.ECDH(), private_key_b.public_key())
    symmetric_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"encryption-key"
    ).derive(shared_secret)
    return symmetric_key

def derive_chaotic_key(symmetric_key):
    """Derive a chaotic key for additional encryption."""
    chaotic_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"chaotic-key"
    ).derive(symmetric_key)
    return chaotic_key

def generate_rsa_key_pair():
    """Generate an RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt_data(data, aes_key, chacha_key, rsa_public_key):
    """Encrypt data using AES, RSA, and ChaCha20."""
    try:
        aes_iv = os.urandom(16)
        aes_cipher = Cipher(algorithms.AES(aes_key), modes.CFB(aes_iv))
        aes_encryptor = aes_cipher.encryptor()
        aes_encrypted = aes_iv + aes_encryptor.update(data) + aes_encryptor.finalize()

        rsa_encrypted_aes_key = rsa_public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        chacha_nonce = os.urandom(16)
        chacha_cipher = Cipher(algorithms.ChaCha20(chacha_key, chacha_nonce), mode=None)
        chacha_encryptor = chacha_cipher.encryptor()
        final_encrypted = chacha_nonce + chacha_encryptor.update(rsa_encrypted_aes_key + aes_encrypted)

        return final_encrypted
    except Exception as e:
        print(f"Encryption failed: {e}")
        return None

def decrypt_data(encrypted_data, rsa_private_key, chacha_key):
    """Decrypt data using ChaCha20, RSA, and AES."""
    try:
        chacha_nonce = encrypted_data[:16]
        chacha_encrypted = encrypted_data[16:]

        chacha_cipher = Cipher(algorithms.ChaCha20(chacha_key, chacha_nonce), mode=None)
        chacha_decryptor = chacha_cipher.decryptor()
        rsa_encrypted_aes_key_and_aes_encrypted = chacha_decryptor.update(chacha_encrypted)

        rsa_encrypted_aes_key = rsa_encrypted_aes_key_and_aes_encrypted[:256]
        aes_encrypted = rsa_encrypted_aes_key_and_aes_encrypted[256:]

        aes_key = rsa_private_key.decrypt(
            rsa_encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        aes_iv = aes_encrypted[:16]
        aes_ciphertext = aes_encrypted[16:]

        aes_cipher = Cipher(algorithms.AES(aes_key), modes.CFB(aes_iv))
        aes_decryptor = aes_cipher.decryptor()
        decrypted_data = aes_decryptor.update(aes_ciphertext) + aes_decryptor.finalize()

        return decrypted_data
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None

def read_file(file_path):
    with open(file_path, "rb") as f:
        return f.read()

def write_file(file_path, data):
    with open(file_path, "wb") as f:
        f.write(data)

# Routes
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Generate a password reset token
        token = s.dumps(email, salt='password-reset-salt')
        
        # Create the email content
        msg = MIMEMultipart()
        msg['From'] = 'raiyashas05@gmail.com'
        msg['To'] = email
        msg['Subject'] = 'Password Reset Request'
        link = url_for('reset_password', token=token, _external=True)
        msg.attach(MIMEText(f'Click the link to reset your password: {link}', 'plain'))
        
        # Send the email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('raiyashas05@gmail.com', '1810sspr')
                server.sendmail(msg['From'], msg['To'], msg.as_string())
            flash('If an account with that email exists, a password reset link has been sent.')
            time.sleep(2)
        except Exception as e:
            flash('An error occurred while sending the email. Please try again later.')
        
    
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception as e:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password', token=token))
        
        # Hash the new password using bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update the user's password in the database
        users_collection.update_one({'email': email}, {'$set': {'password': hashed_password}})
        
        flash('Your password has been reset successfully.')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email=request.form['email']
        # Check if the username already exists in the database
        if users_collection.find_one({'username': username}):
            return render_template('signup.html', alert_message='Username already exists!')
        
        if users_collection.find_one({'email': email}):
            return render_template('signup.html', alert_message='Email already exists!')
        
        # Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Generate a unique symmetric key for the user
        symmetric_key = generate_symmetric_key()
        
        # Generate RSA key pair for the user
        rsa_private_key, rsa_public_key = generate_rsa_key_pair()
        
        # Store the username, hashed password, symmetric key, and RSA keys in the database
        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'symmetric_key': symmetric_key.hex(),
            'rsa_private_key': rsa_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8'),
            'rsa_public_key': rsa_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
        })
        
        alert_message = 'Account created successfully! Please login.'
        time.sleep(2)
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Load the user from the database
        user = users_collection.find_one({'username': username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            session['symmetric_key'] = user['symmetric_key']
            session['rsa_private_key'] = user['rsa_private_key']
            session['rsa_public_key'] = user['rsa_public_key']
            alert_message = 'Login successful!'
            return redirect(url_for('audio_options'))
        else:
            return render_template('login.html', alert_message='Invalid username or password!')
    return render_template('login.html')

@app.route('/options')
def audio_options():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('options.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/audio_encryption', methods=['GET', 'POST'])
def audio_encryption():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        files = request.files.getlist('audio_files')
        encrypted_files = []
        for file in files:
            if file and file.filename.endswith('.mp3'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                original_data = read_file(file_path)
                
                # Retrieve the symmetric key and RSA public key from session
                symmetric_key = bytes.fromhex(session.get('symmetric_key'))
                rsa_public_key = serialization.load_pem_public_key(session.get('rsa_public_key').encode('utf-8'))
                chaotic_key = derive_chaotic_key(symmetric_key)

                encrypted_data = encrypt_data(original_data, symmetric_key, chaotic_key, rsa_public_key)
                if encrypted_data:
                    encrypted_file = os.path.splitext(filename)[0] + ".enc"
                    encrypted_file_path = os.path.join(UPLOAD_FOLDER, encrypted_file)
                    write_file(encrypted_file_path, encrypted_data)
                    encrypted_files.append(encrypted_file)
                else:
                    return render_template('audio_encryption.html', message="Encryption failed for file: " + filename)
            else:
                return render_template('audio_encryption.html', message="Please upload valid MP3 files!")
        return render_template('audio_encryption.html', message="Files encrypted successfully!", encrypted_files=encrypted_files)
    return render_template('audio_encryption.html')

@app.route('/audio_decryption', methods=['GET', 'POST'])
def audio_decryption():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        files = request.files.getlist('encrypted_files')
        decrypted_files = []
        for file in files:
            if file and file.filename.endswith('.enc'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                encrypted_data = read_file(file_path)

                # Retrieve the symmetric key and RSA private key from session
                symmetric_key = bytes.fromhex(session.get('symmetric_key'))
                rsa_private_key = serialization.load_pem_private_key(
                    session.get('rsa_private_key').encode('utf-8'),
                    password=None
                )
                chaotic_key = derive_chaotic_key(symmetric_key)

                decrypted_data = decrypt_data(encrypted_data, rsa_private_key, chaotic_key)
                if decrypted_data:
                    decrypted_file = filename.replace('.enc', '.mp3')
                    decrypted_path = os.path.join(DECRYPTED_FOLDER, decrypted_file)
                    write_file(decrypted_path, decrypted_data)
                    decrypted_files.append(decrypted_file)
                else: 
                    return render_template('audio_decryption.html', message="Decryption failed for file: " + filename)
            else:
                return render_template('audio_decryption.html', message="Please upload valid encrypted files!")
        return render_template('audio_decryption.html', message="Files decrypted successfully!", decrypted_files=decrypted_files)
    return render_template('audio_decryption.html')

@app.route('/download/uploads/<filename>')
def download_upload_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return "File not found!", 404
    return send_file(file_path, as_attachment=True, mimetype='audio/mp3')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(DECRYPTED_FOLDER, filename)
    if not os.path.exists(file_path):
        return "File not found!", 404
    return send_file(file_path, as_attachment=True, mimetype='audio/mp3')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)