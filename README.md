# Audio Encryption and Decryption System

A Flask-based web application that allows users to encrypt and decrypt audio files using advanced cryptographic algorithms like AES and ChaCha20. The application also implements ECDH (Elliptic Curve Diffie-Hellman) for key exchange and chaotic maps for enhanced security.

---

## Features

- **User Authentication**: Secure login system to access encryption and decryption functionalities.
- **Audio File Encryption**: Upload an `.mp3` file, and the system encrypts it using AES and ChaCha20.
- **Audio File Decryption**: Decrypt previously encrypted files back into `.mp3` format.
- **Elliptic Curve Cryptography**: Uses ECDH for secure symmetric key generation.
- **Chaotic Key Derivation**: Adds an extra layer of security by deriving chaotic keys.
- **Secure File Handling**: Files are securely saved in specific folders, ensuring privacy.
- **Downloadable Output**: Users can download encrypted or decrypted files directly.

---

## Technologies Used

- **Backend**: Flask
- **Cryptography**: Python's `cryptography` library for AES, ChaCha20, and ECDH implementations
- **Frontend**: HTML and Flask templates
- **File Management**: `werkzeug` for secure file uploads
- **Session Management**: Flask's built-in session handling

---
