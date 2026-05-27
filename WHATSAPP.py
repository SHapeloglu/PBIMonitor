import requests

phone_number_id = "1221514654368217"
access_token = "EAAZBuZAPURlf0BRp66A4ZCjV2j31WTZCD5tzauIlni7IqeUQLGX2GBLFhAfyqNCDoQEkrhSwdMai4pE7WFeWAM5QP2fIZBM3jLCEc6blgo3Bu6eYobTHNcXi6pLy3ZCp7HOinzrQOOtJOedcOXTdhOxkM28ZBxpIfyO3i8yATh5JdrXv4PZBLy3moWL74VCdBdRElZB8jytmYYfdhKJoRaDKWPbGpQnMWJMtrVPEGMEIyAG6l9e41tZBDptTIR4NiTxdMR1WOlB4K31olpPrNJ4WPfPYHpHwZDZD"
alici_numara = "905397835500"  # başına 90 ekle, 0 olmadan

url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "messaging_product": "whatsapp",
    "to": alici_numara,
    "type": "text",
    "text": {
        "body": "✅ PBI Monitor test mesajı. Sistem çalışıyor."
    }
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())