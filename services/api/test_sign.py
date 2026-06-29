import base64, hashlib, hmac, json
from urllib.parse import quote

client_secret = "88e40499b2af98eaa8e81046353954a3"
method = "POST"
path = "/jdyconnector/app_management/push_app_authorize"
ts = "1741234567890"
nonce = "1234567"
instance_id = "509132114453729280"

ek = quote(quote("outerInstanceId", safe=""), safe="")
ev = quote(quote(instance_id, safe=""), safe="")
encoded_params = f"{ek}={ev}"

sign_data = (
    f"{method}\n"
    f"{quote(path, safe='')}\n"
    f"{encoded_params}\n"
    f"x-api-nonce:{nonce}\n"
    f"x-api-timestamp:{ts}\n"
)

print("=== Python signing test ===")
print("path encoded:", quote(path, safe=""))
print("encoded_params:", encoded_params)
print("sign_data repr:", repr(sign_data))

hex_digest = hmac.new(client_secret.encode(), sign_data.encode(), hashlib.sha256).hexdigest()
print("hex_digest:", hex_digest)

signature = base64.b64encode(hex_digest.encode()).decode()
print("signature:", signature)

# Also output JS-equivalent test code
print("\n=== Copy this to Postman Console to compare ===")
js_code = f"""
var clientSecret = "{client_secret}";
var signData = {json.dumps(sign_data)};
console.log("JS sign_data repr:", JSON.stringify(signData));
var hexDigest = CryptoJS.HmacSHA256(signData, clientSecret).toString(CryptoJS.enc.Hex);
console.log("JS hex_digest:", hexDigest);
var signature = CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(hexDigest));
console.log("JS signature:", signature);
console.log("Python signature was: {{}}" );
""".strip()
print(js_code)
