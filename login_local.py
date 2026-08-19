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

def challenge_code_handler(username, choice):
    code = input(f"\n📩 Instagram doğrulama kodu gönderdi ({choice}). Lütfen gelen kodu buraya yazın: ").strip()
    return code

def main():
    print("=" * 60)
    print("      INSTAGRAM GÜNCEL OTURUM YENİLEYİCİ")
    print("=" * 60)
    print("Instagram hesabınızda e-posta/şifre değişikliği yapıldığında")
    print("bu araç yeni oturum anahtarını (data/ig_session.json) üretir")
    print("ve otomatik olarak GitHub'a yükler.\n")

    username = input("Instagram Kullanıcı Adınız [Varsayılan: mufithocailematematik]: ").strip()
    if not username:
        username = "mufithocailematematik"

    password = input("Instagram Güncel Şifreniz: ").strip()

    if not password:
        print("[HATA] Şifre boş bırakılamaz.")
        return

    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
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

    print(f"\n⏳ @{username} hesabına giriş yapılıyor...")
    try:
        logged_in = cl.login(username, password)
        if logged_in:
            os.makedirs("data", exist_ok=True)
            cl.dump_settings("data/ig_session.json")
            print("✅ Giriş başarılı! data/ig_session.json güncellendi.")
    except TwoFactorRequired:
        code = input("\n📱 İki Adımlı Doğrulama (2FA) Kodu: ").strip()
        cl.login_by_2fa(code)
        os.makedirs("data", exist_ok=True)
        cl.dump_settings("data/ig_session.json")
        print("✅ 2FA ile giriş başarılı! data/ig_session.json güncellendi.")
    except Exception as e:
        print(f"\n❌ Giriş başarısız oldu: {e}")
        print("\nİpucu: Instagram uygulamanızı telefonunuzdan açıp 'Giriş yapan bendim' onayını verin ve tekrar deneyin.")
        return

    # Automatically commit and push session to GitHub
    print("\n📤 Güncel oturum dosyası GitHub reponuza yükleniyor...")
    try:
        subprocess.run(["git", "add", "data/ig_session.json"], check=True)
        subprocess.run(["git", "commit", "-m", "chore: Update authentic Instagram session file"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("\n" + "=" * 60)
        print("🎉 TEBRİKLER! Yeni oturumunuz GitHub'a başarıyla yüklendi.")
        print("Artık her sabahki otomatik paylaşımlar sorunsuz devam edecektir!")
        print("=" * 60)
    except Exception as e:
        print(f"Git yükleme uyarısı: {e}")

if __name__ == "__main__":
    main()
