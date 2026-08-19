import os
import sys
import time
import subprocess
from uuid import uuid4
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, UnknownError

# UTF-8 console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def attempt_two_factor_verification(cl, code):
    """Try both Bloks 2FA and legacy SMS 2FA endpoints."""
    # 1. Try Bloks 2FA
    try:
        print("  -> Bloks 2FA yöntemi deneniyor...")
        if cl._login_with_bloks_two_factor(code, cl.last_json, TwoFactorRequired()):
            return True
    except Exception as e1:
        print(f"     Bloks denemesi: {e1}")

    # 2. Try legacy 2FA endpoint with method 1 (SMS)
    try:
        print("  -> Standart SMS 2FA yöntemi deneniyor...")
        two_factor_info = cl.last_json.get("two_factor_info", {})
        two_factor_identifier = two_factor_info.get("two_factor_identifier")
        data = {
            "verification_code": code,
            "phone_id": cl.phone_id,
            "_csrftoken": cl.token,
            "two_factor_identifier": two_factor_identifier,
            "username": cl.username,
            "trust_this_device": "1",
            "guid": cl.uuid,
            "device_id": cl.android_device_id,
            "waterfall_id": str(uuid4()),
            "verification_method": "1",
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
    except Exception as e2:
        print(f"     Standart SMS denemesi: {e2}")

    # 3. Try legacy 2FA endpoint with method 2 (WhatsApp)
    try:
        print("  -> WhatsApp 2FA yöntemi deneniyor...")
        data["verification_method"] = "2"
        logged = cl.private_request("accounts/two_factor_login/", data, login=True)
        if logged:
            cl.login_flow()
            return True
    except Exception as e3:
        print(f"     WhatsApp denemesi: {e3}")

    return False

def login_with_sessionid(cl, sessionid):
    """Direct 100% foolproof login using browser sessionid cookie."""
    cl.login_by_sessionid(sessionid)
    user_info = cl.account_info()
    print(f"\n✅ Cookie ile Giriş Başarılı! Kullanıcı: @{user_info.username}")
    return True

def main():
    print("=" * 60)
    print("       MÜFİT HOCA - INSTAGRAM OTURUM YENİLEYİCİ")
    print("=" * 60)
    print("Yöntem 1: Otomatik SMS Kodu İle Giriş")
    print("Yöntem 2: Tarayıcı 'sessionid' Çerezi İle Doğrudan Giriş")
    print("=" * 60 + "\n")

    choice = input("Hangi yöntemi kullanmak istersiniz? [1: SMS Kodu, 2: Tarayıcı Cookie (Varsayılan 1)]: ").strip()
    if choice == "2":
        sessionid = input("\nTarayıcınızdan kopyaladığınız 'sessionid' çerez değerini yapıştırın: ").strip()
        cl = Client()
        cl.set_locale("tr_TR")
        try:
            login_with_sessionid(cl, sessionid)
            os.makedirs("data", exist_ok=True)
            cl.dump_settings("data/ig_session.json")
        except Exception as e:
            print(f"\n❌ Cookie giriş hatası: {e}")
            return
    else:
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
            
            print("\n⏳ Kod Instagram'a iletiliyor...")
            success = attempt_two_factor_verification(cl, code)
            if success:
                os.makedirs("data", exist_ok=True)
                cl.dump_settings("data/ig_session.json")
                print("\n✅ 2FA doğrulaması başarıyla onaylandı! Oturum kaydedildi.")
            else:
                print("\n❌ Kod onaylanamadı.")
                return
        except Exception as e:
            print(f"\n❌ Giriş hatası: {e}")
            return

    # Push to GitHub
    print("\n📤 Güncel oturum dosyası GitHub'a yükleniyor...")
    try:
        subprocess.run(["git", "add", "data/ig_session.json"], check=True)
        subprocess.run(["git", "commit", "-m", "chore: Update authentic Instagram session"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("\n" + "=" * 60)
        print("🎉 TEBRİKLER! Oturumunuz GitHub'a başarıyla yüklendi.")
        print("Artık paylaşımlarınız her sabah 09:00'da otomatik devam edecek!")
        print("=" * 60)
    except Exception as e:
        print(f"Git yükleme uyarısı: {e}")

if __name__ == "__main__":
    main()
