import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

numbers = public_key.public_numbers()
public_bytes = (
    b"\x04"
    + numbers.x.to_bytes(32, "big")
    + numbers.y.to_bytes(32, "big")
)
public_urlsafe = base64.urlsafe_b64encode(
    public_bytes
).decode("ascii").rstrip("=")

Path("vapid_private.pem").write_bytes(private_pem)

print("\nClé publique VAPID (à mettre dans WEBPUSH_VAPID_PUBLIC_KEY) :")
print(public_urlsafe)
print("\nClé privée enregistrée dans vapid_private.pem.")
print("Garde ce fichier secret et ne le téléverse pas dans static/.")