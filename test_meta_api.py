import os
import sys
import requests

# UTF-8 encoding for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    from dotenv import load_dotenv
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(dotenv_path=env_path)
except Exception:
    pass

def test_credentials(account_id, access_token):
    print("=" * 60)
    print("      META INSTAGRAM GRAPH API BAĞLANTI TESTİ")
    print("=" * 60)
    print(f"📌 Account ID   : {account_id}")
    print(f"🔑 Access Token  : {access_token[:10]}...{access_token[-5:] if len(access_token) > 15 else ''}")
    print("=" * 60 + "\n")

    # 1. Test Account Info
    print("⏳ 1. Instagram Hesap Bilgileri Sorgulanıyor...")
    url = f"https://graph.facebook.com/v20.0/{account_id}"
    params = {
        "fields": "id,username,name,profile_picture_url,followers_count",
        "access_token": access_token
    }
    
    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
        
        if "error" in data:
            print("\n❌ Meta API Hatası:")
            print(f"Mesaj: {data['error'].get('message')}")
            print(f"Kod: {data['error'].get('code')}")
            print(f"Alt Kod: {data['error'].get('error_subcode')}")
            print(f"Detay: {data['error'].get('error_user_msg', 'Yok')}")
            return False
            
        print("✅ BAĞLANTI BAŞARILI!")
        print(f"   👤 Kullanıcı Adı: @{data.get('username')}")
        print(f"   🏷️ Hesap İsmi: {data.get('name')}")
        print(f"   👥 Takipçi Sayısı: {data.get('followers_count', 'N/A')}")
        print(f"   🆔 Meta Instagram ID: {data.get('id')}")
        print("\n🎉 Tebrikler! Meta Graph API anahtarlarınız %100 çalışıyor.")
        print("Bu anahtarlar ile GitHub Actions üzerinden şifresiz ve güvenli paylaşım yapabilirsiniz.")
        return True

    except Exception as e:
        print(f"\n❌ Bağlantı sırasında bir hata oluştu: {e}")
        return False

if __name__ == "__main__":
    account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()

    if not account_id or not access_token:
        print("Lütfen Meta API bilgilerinizi girin:")
        if not account_id:
            account_id = input("INSTAGRAM_ACCOUNT_ID: ").strip()
        if not access_token:
            access_token = input("INSTAGRAM_ACCESS_TOKEN: ").strip()

    test_credentials(account_id, access_token)
