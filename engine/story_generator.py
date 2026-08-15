import os
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

class StoryGenerator:
    def __init__(self, font_dir="assets/fonts", output_dir="dist/stories"):
        self.font_dir = font_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.load_fonts()

    def load_fonts(self):
        def get_font(name, size):
            path = os.path.join(self.font_dir, name)
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
            return ImageFont.load_default()

        # Calibrated typography for Instagram Safe Zone (1080x1920)
        self.font_brand_title = get_font("TitleBold.ttf", 26)
        self.font_brand_sub = get_font("BodyBold.ttf", 19)
        self.font_badge = get_font("TitleBold.ttf", 21)
        self.font_title = get_font("TitleBold.ttf", 36)
        self.font_era = get_font("SerifBold.ttf", 23)
        self.font_card_header = get_font("TitleBold.ttf", 22)
        self.font_quote = get_font("SerifBold.ttf", 27)
        self.font_body = get_font("Body.ttf", 23)
        self.font_body_bold = get_font("BodyBold.ttf", 23)
        self.font_quiz_opt = get_font("BodyBold.ttf", 21)
        self.font_small = get_font("Body.ttf", 18)
        self.font_footer_main = get_font("TitleBold.ttf", 20)
        self.font_footer_sub = get_font("Serif.ttf", 18)

    def clean_special_chars(self, text):
        return text.replace("↔", " - ").replace("→", " > ").replace("←", " < ").replace("•", "*")

    def wrap_text(self, text, width=44):
        cleaned = self.clean_special_chars(text)
        lines = []
        for p in cleaned.split("\n"):
            if p.strip():
                lines.extend(textwrap.wrap(p.strip(), width=width))
        return lines

    def draw_card(self, draw, x, y, w, h, bg_color="#FFFFFF", border_color="#DDCFB4", radius=14):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg_color, outline=border_color, width=2)

    def draw_bullet_diamond(self, draw, x, y, size=5, color="#8C682D"):
        draw.polygon([(x, y - size), (x + size, y), (x, y + size), (x - size, y)], fill=color)

    def generate_story(self, day_data, filename=None):
        day_num = day_data["day"]
        raw_title = day_data["title"].upper()
        title = self.clean_special_chars(raw_title)
        era_figure = self.clean_special_chars(day_data.get("era_figure", ""))
        hook = day_data.get("hook", "")
        history = day_data.get("history", "")
        tyt_links = day_data.get("tyt_ayt_links", [])
        daily_life = day_data.get("daily_life", "")
        conn_note = day_data.get("connection_note", "")
        surprising_fact = day_data.get("surprising_fact", "")
        quiz = day_data.get("quiz", {})

        # Standard Instagram Story resolution (1080 x 1920)
        W, H = 1080, 1920
        img = Image.new("RGB", (W, H), color="#FBF8F1")
        draw = ImageDraw.Draw(img)

        # 1. Classical Borders & Ornaments (Fit within canvas)
        draw.rectangle([24, 24, W - 24, H - 24], outline="#C4A66B", width=2)
        draw.rectangle([32, 32, W - 32, H - 32], outline="#E8DEC8", width=1)
        
        # Corner diamonds
        for cx, cy in [(32, 32), (W - 32, 32), (32, H - 32), (W - 32, H - 32)]:
            self.draw_bullet_diamond(draw, cx, cy, size=7, color="#8C6A2E")

        # ==========================================
        # TOP SAFE ZONE: Start content below y = 210
        # ==========================================
        curr_y = 210

        # 2. Header Brand Section
        h_brand = "MÜFİT HOCA İLE MATEMATİK"
        bbox = draw.textbbox((0, 0), h_brand, font=self.font_brand_title)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, curr_y), h_brand, fill="#2A2114", font=self.font_brand_title)
        curr_y += 34

        # Attribution Pill
        h_attr = "Kaynak: @riyazihane  •  @mufithocailematematik"
        bbox = draw.textbbox((0, 0), h_attr, font=self.font_brand_sub)
        tw = bbox[2] - bbox[0]
        pill_w = tw + 32
        pill_h = 30
        draw.rounded_rectangle([(W - pill_w) / 2, curr_y, (W + pill_w) / 2, curr_y + pill_h], radius=15, fill="#EFE5D0")
        draw.text(((W - tw) / 2, curr_y + 5), h_attr, fill="#5C482C", font=self.font_brand_sub)
        curr_y += 42

        # 3. Campaign Badge (Gün X / 97)
        badge_str = f"YKS / TYT-AYT ZİHİN HARİTASI  •  GÜN {day_num} / 97"
        bbox = draw.textbbox((0, 0), badge_str, font=self.font_badge)
        tw = bbox[2] - bbox[0]
        bw = tw + 38
        bh = 34
        draw.rounded_rectangle([(W - bw) / 2, curr_y, (W + bw) / 2, curr_y + bh], radius=8, fill="#8C682D")
        draw.text(((W - tw) / 2, curr_y + 6), badge_str, fill="#FFFFFF", font=self.font_badge)
        curr_y += 44

        # 4. Main Title
        title_lines = self.wrap_text(title, width=32)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=self.font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), line, fill="#1B1710", font=self.font_title)
            curr_y += 42

        # Era / Figure Tag
        if era_figure:
            sub_str = f"~ {era_figure} ~"
            bbox = draw.textbbox((0, 0), sub_str, font=self.font_era)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), sub_str, fill="#7A5A29", font=self.font_era)
            curr_y += 32
        else:
            curr_y += 8

        # Decorative Divider
        draw.line([120, curr_y, W - 120, curr_y], fill="#DAC9A6", width=1)
        self.draw_bullet_diamond(draw, W/2, curr_y, size=5, color="#8C682D")
        curr_y += 18

        card_w = W - 120
        card_x = 60

        # 5. Card 1: Hook Question (Kanca Soru)
        hook_lines = self.wrap_text(f"“{hook}”", width=38)
        hook_h = len(hook_lines) * 34 + 24
        self.draw_card(draw, card_x, curr_y, card_w, hook_h, bg_color="#FFFDF7", border_color="#D9C398", radius=12)
        draw.rounded_rectangle([card_x, curr_y, card_x + 8, curr_y + hook_h], radius=4, fill="#C49A45")
        
        hy = curr_y + 12
        for line in hook_lines:
            draw.text((card_x + 26, hy), line, fill="#3A280B", font=self.font_quote)
            hy += 34
        curr_y += hook_h + 14

        # 6. Card 2: Tarihsel Mantık & Doğuş Sebebi
        hist_lines = self.wrap_text(history, width=50)
        hist_h = len(hist_lines) * 30 + 54
        self.draw_card(draw, card_x, curr_y, card_w, hist_h, bg_color="#FFFFFF", border_color="#E4D7BF", radius=12)
        
        self.draw_bullet_diamond(draw, card_x + 28, curr_y + 22, size=4, color="#8C682D")
        draw.text((card_x + 40, curr_y + 12), "NEDEN DOĞDU? (TARİHSEL MANTIK)", fill="#8C682D", font=self.font_card_header)
        hy = curr_y + 44
        for line in hist_lines:
            draw.text((card_x + 26, hy), line, fill="#2C271E", font=self.font_body)
            hy += 30
        curr_y += hist_h + 14

        # 7. Card 3: TYT - AYT Sınav Haritası & Bağlantı Notu
        conn_lines = self.wrap_text(f"Bağlantı Köprüsü: {conn_note}", width=50) if conn_note else []
        card3_h = 76 + (len(conn_lines) * 28) + 24
        self.draw_card(draw, card_x, curr_y, card_w, card3_h, bg_color="#F6F0E2", border_color="#D5C19A", radius=12)
        
        self.draw_bullet_diamond(draw, card_x + 28, curr_y + 20, size=4, color="#8C682D")
        draw.text((card_x + 40, curr_y + 10), "TYT - AYT SINAV YANSIMASI", fill="#8C682D", font=self.font_card_header)
        
        # Topic Tags
        tag_x = card_x + 26
        tag_y = curr_y + 40
        for topic in tyt_links:
            clean_topic = self.clean_special_chars(topic)
            tag_str = f"• {clean_topic}"
            bbox = draw.textbbox((0, 0), tag_str, font=self.font_body_bold)
            t_w = bbox[2] - bbox[0] + 20
            if tag_x + t_w > W - 80:
                tag_x = card_x + 26
                tag_y += 36
            draw.rounded_rectangle([tag_x, tag_y, tag_x + t_w, tag_y + 28], radius=6, fill="#E5D6B6")
            draw.text((tag_x + 8, tag_y + 3), tag_str, fill="#2C2416", font=self.font_body_bold)
            tag_x += t_w + 10
        
        # Wrapped connection chain
        cy = tag_y + 38
        for line in conn_lines:
            draw.text((card_x + 26, cy), line, fill="#5A472A", font=self.font_body_bold)
            cy += 28
        curr_y += card3_h + 14

        # 8. Card 4: Şaşırtıcı Bilgi & Günlük Hayat
        fact_lines = self.wrap_text(f"Şaşırtıcı Bilgi: {surprising_fact}", width=50)
        if daily_life:
            fact_lines.append("")
            fact_lines.extend(self.wrap_text(f"Günlük Hayat: {daily_life}", width=50))
        fact_h = len(fact_lines) * 28 + 52
        self.draw_card(draw, card_x, curr_y, card_w, fact_h, bg_color="#FFFDF2", border_color="#DAC79A", radius=12)
        
        self.draw_bullet_diamond(draw, card_x + 28, curr_y + 20, size=4, color="#8C682D")
        draw.text((card_x + 40, curr_y + 10), "ŞAŞIRTICI BİLGİ & GÜNLÜK HAYAT", fill="#8C682D", font=self.font_card_header)
        
        fy = curr_y + 42
        for line in fact_lines:
            if line.startswith("Şaşırtıcı Bilgi:") or line.startswith("Günlük Hayat:"):
                draw.text((card_x + 26, fy), line, fill="#4A3B18", font=self.font_body_bold)
            else:
                draw.text((card_x + 26, fy), line, fill="#4A3B18", font=self.font_body)
            fy += 28
        curr_y += fact_h + 14

        # 9. Card 5: Günün İnteraktif Soru Çıkartması (Quiz Box)
        quiz_q = quiz.get("question", "")
        quiz_opts = quiz.get("options", [])
        quiz_lines = self.wrap_text(f"GÜNÜN SORUSU: {quiz_q}", width=44)
        
        grid_rows = 2 if len(quiz_opts) == 4 else len(quiz_opts)
        quiz_h = len(quiz_lines) * 30 + 54 + (grid_rows * 44)
        self.draw_card(draw, card_x, curr_y, card_w, quiz_h, bg_color="#241E15", border_color="#8C682D", radius=12)
        
        qy = curr_y + 14
        for line in quiz_lines:
            draw.text((card_x + 24, qy), line, fill="#F7EAC7", font=self.font_body_bold)
            qy += 30
        
        if len(quiz_opts) == 4:
            opt_labels = ["A", "B", "C", "D"]
            opt_w = (card_w - 60) / 2
            opt_h = 36
            qy += 6
            for i, opt in enumerate(quiz_opts):
                col = i % 2
                row = i // 2
                ox = card_x + 20 + col * (opt_w + 16)
                oy = qy + row * (opt_h + 8)
                draw.rounded_rectangle([ox, oy, ox + opt_w, oy + opt_h], radius=6, fill="#3A3223", outline="#7A6849")
                lbl_text = f"[{opt_labels[i]}] {opt}"
                draw.text((ox + 10, oy + 6), lbl_text, fill="#F5E8C7", font=self.font_quiz_opt)
            qy += 2 * (opt_h + 8) + 4
        
        draw.text((card_x + 24, qy + 2), "Cevabını hikayeye yanıt olarak yaz veya ankete katıl!", fill="#D8B772", font=self.font_small)
        curr_y += quiz_h + 14

        # =============================================
        # BOTTOM SAFE ZONE: Placed safely at y ~ 1640
        # (Well above Instagram bottom action bar at 1730)
        # =============================================
        footer_y = curr_y + 8
        draw.line([100, footer_y, W - 100, footer_y], fill="#DAC9A6", width=1)
        
        f1 = "Hazırlayan: @mufithocailematematik  |  Kaynak: @riyazihane"
        bbox = draw.textbbox((0, 0), f1, font=self.font_footer_main)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, footer_y + 10), f1, fill="#3A2D16", font=self.font_footer_main)
        
        f2 = "“Matematik sadece formül değil; insanlığın düşünme tarihidir.”"
        bbox = draw.textbbox((0, 0), f2, font=self.font_footer_sub)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, footer_y + 36), f2, fill="#7A6849", font=self.font_footer_sub)

        # Save image
        if filename is None:
            filename = f"day_{day_num:03d}.jpg"
        out_path = os.path.join(self.output_dir, filename)
        img.save(out_path, quality=95)
        print(f"Rendered polished story: {out_path}")
        return out_path

if __name__ == "__main__":
    with open("data/campaign_97_days.json", "r", encoding="utf-8") as f:
        days = json.load(f)

    gen = StoryGenerator()
    test_days = [1, 9, 42, 80]
    for d_num in test_days:
        d_data = next(x for x in days if x["day"] == d_num)
        gen.generate_story(d_data)
