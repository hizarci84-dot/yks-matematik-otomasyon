import os
import sys
import time
import subprocess
from uuid import uuid4
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired

# UTF-8 console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def custom_two_factor_login(cl, verification_code):
    two_factor_info = cl.last_json.get("two_factor_info", {})
    two_factor_identifier = two_factor_info.get("two_factor_identifier")
    
    # 1: SMS, 2: WhatsApp, 3: TOTP / Authenticator App
    v_method = "1" if two_factor_info.get("sms_two_factor_on") else "3"
    
    data = {
        "verification_code": verification_code,
        "phone_id": cl.phone_id,
        "_csrftoken": cl.token,
        "two_factor_identifier": two_factor_identifier,
        "username": cl.username,
        "trust_this_device": "1",
        "guid": cl.uuid,
        "device_id": cl.android_device_id,
        "waterfall_id": str(uuid4()),
        "verification_method": v_method,
    }
    
    logged = cl.private_request("accounts/two_factor_login/", data, login=True)
    cl.authorization_data = cl.parse_authorization(
        cl.last_response.headers.get("ig-set-authorization")
    )
    if logged:
        cl.login_flow()
        cl.last_login = time.time()
        cl.relogin_attempt = 0
        return True
    return False

def main():
    print("=" * 60)
    print("       MÜFİT HOCA - INSTAGRAM SMS/2FA DOĞRULAYICI")
    print("=" * 60)

    username = "mufithocailematematik"
    password = "844945gmab.2234"

    cl = Client()
    cl.set_locale("tr_TR")
    cl.set_country(90)
    cl.set_timezone_offset(3 * 3600)
    
    cl.set_device({
        "app_version": "315.0.0.38.109",
        "android_version": 33,
        "android_release": "13.0",
        "dpi": "480dpi",
        "resolution": "1080x2400",
        "manufacturer": "Samsung",
        "device": "SM-G998B",
        "model": "galaxy-s21-ultra",
        "cpu": "exynos2100",
        "version_code": "561657871"
    })

    print(f"\n⏳ @{username} hesabına bağlanılıyor ve SMS kodu isteniyor...")
    try:
        logged_in = cl.login(username, password)
        if logged_in:
            os.makedirs("data", exist_ok=True)
            cl.dump_settings("data/ig_session.json")
            print("\n✅ Giriş başarılı! data/ig_session.json güncellendi.")
    except TwoFactorRequired:
        info = cl.last_json.get("two_factor_info", {})
        phone_mask = info.get("obfuscated_phone_number_2", info.get("obfuscated_phone_number", ""))
        print("\n" + "=" * 60)
        print(f"📲 Instagram ({phone_mask}) numaralı telefonunuza SMS kodu gönderdi!")
        print("=" * 60)
        
        code = input("\n📱 Telefonunuza gelen 6 Haneli SMS Kodunu Girin: ").strip()
        
        print("\n⏳ Kod Instagram SMS servisine iletiliyor...")
        success = custom_two_factor_login(cl, code)
        if success:
            os.makedirs("data", exist_ok=True)
            cl.dump_settings("data/ig_session.json")
            print("\n✅ 2FA SMS doğrulaması başarıyla onaylandı! Oturum kaydedildi.")
        else:
            print("\n❌ Kod onaylanamadı.")
            return
    except Exception as e:
        print(f"\n❌ Giriş hatası: {e}")
        return

    # Push to GitHub
    print("\n📤 Güncel 2FA oturumu GitHub'a yükleniyor...")
    try:
        subprocess.run(["git", "add", "data/ig_session.json"], check=True)
        subprocess.run(["git", "commit", "-m", "chore: Add 2FA SMS verified session"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("\n" + "=" * 60)
        print("🎉 TEBRİKLER! 2FA onaylı oturumunuz GitHub'a yüklendi.")
        print("Artık paylaşımlarınız her sabah 09:00'da otomatik devam edecek!")
        print("=" * 60)
    except Exception as e:
        print(f"Git yükleme uyarısı: {e}")

if __name__ == "__main__":
    main()
