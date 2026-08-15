import os
import sys
import subprocess
from instagrapi import Client

def main():
    print("=" * 55)
    print("   INSTAGRAM GÜVENLİ YEREL OTURUM OLUŞTURUCU")
    print("=" * 55)
    print("Bu araç, ev internetinizden Instagram'a güvenle giriş yaparak")
    print("oturum dosyasını (data/ig_session.json) oluşturur ve GitHub'a yükler.\n")

    username = input("Instagram Kullanıcı Adınız: ").strip()
    password = input("Instagram Şifreniz: ").strip()

    if not username or not password:
        print("[HATA] Kullanıcı adı veya şifre boş bırakılamaz.")
        return

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

    print(f"\n⏳ @{username} hesabına giriş yapılıyor...")
    try:
        cl.login(username, password)
        os.makedirs("data", exist_ok=True)
        cl.dump_settings("data/ig_session.json")
        print("✅ Giriş başarılı! data/ig_session.json oluşturuldu.")
    except Exception as e:
        print(f"\n❌ Giriş başarısız oldu: {e}")
        return

    # Automatically commit and push session to GitHub
    print("\n📤 Oturum dosyası GitHub reponuza yükleniyor...")
    try:
        subprocess.run(["git", "add", "data/ig_session.json"], check=True)
        subprocess.run(["git", "commit", "-m", "chore: Add authentic Instagram session file"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("\n" + "=" * 55)
        print("🎉 TEBRİKLER! Oturum dosyanız GitHub'a başarıyla yüklendi.")
        print("Artık GitHub Actions hiçbir 429 engeline takılmadan çalışacaktır!")
        print("=" * 55)
    except Exception as e:
        print(f"Git yükleme uyarısı: {e}")

if __name__ == "__main__":
    main()
