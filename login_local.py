import os
import sys
import subprocess
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired

# UTF-8 console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def main():
    print("=" * 60)
    print("       MÜFİT HOCA - INSTAGRAM 2FA OTURUM DOĞRULAYICI")
    print("=" * 60)
    print("Bu araç, 2FA kodunuzu Instagram'a güvenle ileterek oturumu")
    print("otomatik olarak oluşturur ve GitHub'a yükler.\n")

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

    print(f"⏳ @{username} hesabına bağlanılıyor...")
    try:
        logged_in = cl.login(username, password)
        if logged_in:
            os.makedirs("data", exist_ok=True)
            cl.dump_settings("data/ig_session.json")
            print("\n✅ Giriş başarılı! data/ig_session.json güncellendi.")
    except TwoFactorRequired:
        print("\n" + "=" * 60)
        print("🔔 İki Adımlı Doğrulama (2FA) Devrede!")
        print("Telefonunuza az önce gelen 6 haneli kodu aşağıya yazın.")
        print("=" * 60)
        code = input("\n📱 6 Haneli 2FA Onay Kodunu Girin: ").strip()
        
        print("\n⏳ Kod Instagram'a iletiliyor...")
        cl.login(username, password, verification_code=code)
        os.makedirs("data", exist_ok=True)
        cl.dump_settings("data/ig_session.json")
        print("\n✅ 2FA doğrulaması başarılı! Oturum kaydedildi.")
    except Exception as e:
        print(f"\n❌ Giriş başarısız oldu: {e}")
        return

    # Automatically commit and push session to GitHub
    print("\n📤 Güncel oturum dosyası GitHub reponuza yükleniyor...")
    try:
        subprocess.run(["git", "add", "data/ig_session.json"], check=True)
        subprocess.run(["git", "commit", "-m", "chore: Update 2FA authentic Instagram session file"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("\n" + "=" * 60)
        print("🎉 TEBRİKLER! 2FA onaylı oturumunuz GitHub'a yüklendi.")
        print("Artık paylaşımlarınız her sabah 09:00'da otomatik devam edecek!")
        print("=" * 60)
    except Exception as e:
        print(f"Git yükleme uyarısı: {e}")

if __name__ == "__main__":
    main()
