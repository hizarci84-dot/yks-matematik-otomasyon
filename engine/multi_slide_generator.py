import os
import sys
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MultiSlideStoryGenerator:
    def __init__(self, font_dir="assets/fonts", output_dir="dist/stories/multi_slide"):
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

        # Premium Typography Hierarchy (Maximized Legibility & Balance)
        self.font_super_title = get_font("TitleBold.ttf", 50)
        self.font_main_title = get_font("TitleBold.ttf", 40)
        self.font_brand_header = get_font("TitleBold.ttf", 28)
        self.font_brand_sub = get_font("BodyBold.ttf", 20)
        self.font_badge = get_font("TitleBold.ttf", 24)
        self.font_era = get_font("SerifBold.ttf", 28)
        
        # Body and Card text
        self.font_hero_quote = get_font("SerifBold.ttf", 42)
        self.font_node_tag = get_font("TitleBold.ttf", 22)
        self.font_node_title = get_font("TitleBold.ttf", 26)
        self.font_node_body = get_font("Body.ttf", 26)
        self.font_node_bold = get_font("BodyBold.ttf", 26)
        self.font_arrow_lbl = get_font("TitleBold.ttf", 21)
        
        # Quiz fonts (Large, comfortable tap targets)
        self.font_quiz_hero = get_font("TitleBold.ttf", 36)
        self.font_quiz_letter = get_font("TitleBold.ttf", 32)
        self.font_quiz_opt_lg = get_font("BodyBold.ttf", 32)
        
        self.font_swipe = get_font("TitleBold.ttf", 24)
        self.font_small = get_font("Body.ttf", 21)
        self.font_footer = get_font("TitleBold.ttf", 21)
        self.font_footer_sub = get_font("Serif.ttf", 19)

    def clean_special_chars(self, text):
        return (
            text.replace("↔", " - ")
            .replace("→", " > ")
            .replace("←", " < ")
            .replace("•", "*")
            .replace("❓", "")
            .replace("🎯", "")
            .replace("💡", "")
            .replace("🌍", "")
            .replace("📜", "")
            .replace("⚙️", "")
            .replace("✍️", "")
            .replace("👉", ">")
            .replace("👇", "v")
            .strip()
        )

    def wrap_text(self, text, width=36):
        cleaned = self.clean_special_chars(text)
        lines = []
        for p in cleaned.split("\n"):
            if p.strip():
                lines.extend(textwrap.wrap(p.strip(), width=width))
        return lines

    def draw_bullet_diamond(self, draw, x, y, size=6, color="#8C682D"):
        draw.polygon([(x, y - size), (x + size, y), (x, y + size), (x - size, y)], fill=color)

    def draw_base_frame(self, draw, W=1080, H=1920):
        draw.rectangle([24, 24, W - 24, H - 24], outline="#C4A66B", width=2)
        draw.rectangle([32, 32, W - 32, H - 32], outline="#E8DEC8", width=1)
        for cx, cy in [(32, 32), (W - 32, 32), (32, H - 32), (W - 32, H - 32)]:
            self.draw_bullet_diamond(draw, cx, cy, size=7, color="#8C6A2E")

    def draw_top_branding(self, draw, W, curr_y, slide_num, total_slides=3):
        # 1. Müfit Hoca Title
        h_brand = "MÜFİT HOCA İLE MATEMATİK"
        bbox = draw.textbbox((0, 0), h_brand, font=self.font_brand_header)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, curr_y), h_brand, fill="#2A2114", font=self.font_brand_header)
        curr_y += 36

        # 2. Source Attribution Pill
        h_attr = "Kaynak: @riyazihane  •  @mufithocailematematik"
        bbox = draw.textbbox((0, 0), h_attr, font=self.font_brand_sub)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 34) / 2, curr_y, (W + tw + 34) / 2, curr_y + 34], radius=17, fill="#EFE5D0")
        draw.text(((W - tw) / 2, curr_y + 5), h_attr, fill="#5C482C", font=self.font_brand_sub)
        curr_y += 46

        # 3. Slide Counter Indicator
        slide_pill = f"BÖLÜM {slide_num} / {total_slides}"
        bbox = draw.textbbox((0, 0), slide_pill, font=self.font_small)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 28) / 2, curr_y, (W + tw + 28) / 2, curr_y + 30], radius=6, fill="#D9C7A7")
        draw.text(((W - tw) / 2, curr_y + 4), slide_pill, fill="#3A2C18", font=self.font_small)
        curr_y += 46

        return curr_y

    def draw_footer_swipe(self, draw, W, H, text="Zihin Haritası & Mantık"):
        footer_y = 1590
        draw.line([100, footer_y, W - 100, footer_y], fill="#DAC9A6", width=1)
        
        lbl = f"{text}  >>"
        bbox = draw.textbbox((0, 0), lbl, font=self.font_swipe)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 52) / 2, footer_y + 16, (W + tw + 52) / 2, footer_y + 68], radius=26, fill="#8C682D")
        draw.text(((W - tw) / 2, footer_y + 26), lbl, fill="#FFFFFF", font=self.font_swipe)

        f_sub = "“Matematik sadece formül değil; insanlığın düşünme tarihidir.”"
        bbox = draw.textbbox((0, 0), f_sub, font=self.font_footer_sub)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, footer_y + 78), f_sub, fill="#7A6849", font=self.font_footer_sub)

    # =========================================================================
    # SLIDE 1: VURUCU KAPAK & KANCA (MAKSİMUM FERAHLIK)
    # =========================================================================
    def generate_slide_1_cover(self, day_data, filename=None):
        day_num = day_data["day"]
        title = self.clean_special_chars(day_data["title"].upper())
        era_figure = self.clean_special_chars(day_data.get("era_figure", ""))
        hook = self.clean_special_chars(day_data.get("hook", ""))

        W, H = 1080, 1920
        img = Image.new("RGB", (W, H), color="#FBF8F1")
        draw = ImageDraw.Draw(img)
        self.draw_base_frame(draw, W, H)

        curr_y = self.draw_top_branding(draw, W, 210, slide_num=1)

        # 1. Main Campaign Badge
        badge_str = f"YKS / TYT-AYT ZİHİN HARİTASI • GÜN {day_num} / 97"
        bbox = draw.textbbox((0, 0), badge_str, font=self.font_badge)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 52) / 2, curr_y, (W + tw + 52) / 2, curr_y + 46], radius=8, fill="#8C682D")
        draw.text(((W - tw) / 2, curr_y + 9), badge_str, fill="#FFFFFF", font=self.font_badge)
        curr_y += 76

        # 2. Hero Title
        title_lines = self.wrap_text(title, width=22)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=self.font_super_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), line, fill="#1B1710", font=self.font_super_title)
            curr_y += 60

        if era_figure:
            sub_str = f"~ {era_figure} ~"
            bbox = draw.textbbox((0, 0), sub_str, font=self.font_era)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), sub_str, fill="#7A5A29", font=self.font_era)
            curr_y += 54
        else:
            curr_y += 30

        draw.line([140, curr_y, W - 140, curr_y], fill="#DAC9A6", width=2)
        self.draw_bullet_diamond(draw, W/2, curr_y, size=7, color="#8C682D")
        curr_y += 70

        # 3. Big Prominent Hook Box
        hook_lines = self.wrap_text(f"“{hook}”", width=22)
        hook_h = len(hook_lines) * 66 + 110
        card_w = W - 140
        card_x = 70

        draw.rounded_rectangle([card_x, curr_y, card_x + card_w, curr_y + hook_h], radius=18, fill="#FFFDF7", outline="#D9C398", width=3)
        draw.rounded_rectangle([card_x, curr_y, card_x + 14, curr_y + hook_h], radius=4, fill="#C49A45")

        tag_txt = "GÜNÜN KANCASI"
        bbox = draw.textbbox((0, 0), tag_txt, font=self.font_node_tag)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([card_x + 30, curr_y + 22, card_x + 30 + tw + 32, curr_y + 58], radius=6, fill="#8C682D")
        draw.text((card_x + 46, curr_y + 27), tag_txt, fill="#FFFFFF", font=self.font_node_tag)

        hy = curr_y + 84
        for line in hook_lines:
            draw.text((card_x + 36, hy), line, fill="#2C1D07", font=self.font_hero_quote)
            hy += 66

        curr_y += hook_h + 76

        # 4. Highlight Summary Capsule
        capsule_lines = [
            "Bu kavramın nereden doğduğunu ve TYT-AYT sınavında",
            "hangi soruları çözdürdüğünü keşfetmek için yana kaydırın!"
        ]
        for line in capsule_lines:
            bbox = draw.textbbox((0, 0), line, font=self.font_node_bold)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), line, fill="#5B4527", font=self.font_node_bold)
            curr_y += 42

        self.draw_footer_swipe(draw, W, H, text="Kaydırın: Zihin Haritası")

        if filename is None:
            filename = f"slide_1_cover_day_{day_num:03d}.jpg"
        out_path = os.path.join(self.output_dir, filename)
        img.save(out_path, quality=95)
        print(f"Rendered Slide 1 (Cover): {out_path}")
        return out_path

    # =========================================================================
    # SLIDE 2: KAVRAMSAL ZİHİN HARİTASI (MAKSİMUM AÇIK OK ARALIKLARI: 100px)
    # =========================================================================
    def generate_slide_2_mindmap(self, day_data, filename=None):
        day_num = day_data["day"]
        title = self.clean_special_chars(day_data["title"].upper())
        history = self.clean_special_chars(day_data.get("history", ""))
        tyt_links = day_data.get("tyt_ayt_links", [])
        daily_life = self.clean_special_chars(day_data.get("daily_life", ""))
        conn_note = self.clean_special_chars(day_data.get("connection_note", ""))
        surprising_fact = self.clean_special_chars(day_data.get("surprising_fact", ""))

        W, H = 1080, 1920
        img = Image.new("RGB", (W, H), color="#FBF8F1")
        draw = ImageDraw.Draw(img)
        self.draw_base_frame(draw, W, H)

        curr_y = self.draw_top_branding(draw, W, 210, slide_num=2)

        # Header Title
        h_title = f"ZİHİN HARİTASI: {title}"
        title_lines = self.wrap_text(h_title, width=28)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=self.font_main_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), line, fill="#1B1710", font=self.font_main_title)
            curr_y += 48
        
        draw.line([140, curr_y, W - 140, curr_y], fill="#DAC9A6", width=1)
        curr_y += 36

        card_w = W - 120
        card_x = 60
        mid_x = W / 2

        # ---------------------------------------------------------
        # NODE 1: DOĞUŞ SEBEBİ (MANTIK)
        # ---------------------------------------------------------
        hist_lines = self.wrap_text(history, width=38)
        n1_h = len(hist_lines) * 36 + 76
        draw.rounded_rectangle([card_x, curr_y, card_x + card_w, curr_y + n1_h], radius=14, fill="#FFFDF7", outline="#D5C099", width=2)
        
        tag1 = "1. NEDEN DOĞDU? (MANTIK)"
        bbox = draw.textbbox((0, 0), tag1, font=self.font_node_tag)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([card_x + 22, curr_y + 16, card_x + 22 + tw + 30, curr_y + 50], radius=6, fill="#8C682D")
        draw.text((card_x + 37, curr_y + 20), tag1, fill="#FFFFFF", font=self.font_node_tag)

        ny = curr_y + 64
        for line in hist_lines:
            draw.text((card_x + 28, ny), line, fill="#2C261D", font=self.font_node_body)
            ny += 36
        curr_y += n1_h

        # FLOW ARROW 1 -> 2 (Maksimum Genişlik: 95px)
        arrow_h = 95
        draw.line([mid_x, curr_y, mid_x, curr_y + arrow_h], fill="#8C682D", width=4)
        draw.polygon([(mid_x, curr_y + arrow_h), (mid_x - 9, curr_y + arrow_h - 14), (mid_x + 9, curr_y + arrow_h - 14)], fill="#8C682D")
        
        lbl = "TYT - AYT Sınav Yansıması"
        bbox = draw.textbbox((0, 0), lbl, font=self.font_arrow_lbl)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(mid_x - tw/2 - 22), curr_y + 28, (mid_x + tw/2 + 22), curr_y + 66], radius=8, fill="#EFE4D0", outline="#CDBB9B", width=2)
        draw.text((mid_x - tw/2, curr_y + 34), lbl, fill="#5B4527", font=self.font_arrow_lbl)
        curr_y += arrow_h

        # ---------------------------------------------------------
        # NODE 2: TYT - AYT SINAV KÖPRÜSÜ
        # ---------------------------------------------------------
        conn_str = conn_note if conn_note else "Temel Kavramlar > Modelleme > Analiz"
        conn_lines = self.wrap_text(f"Kavram Zinciri: {conn_str}", width=38)
        n2_h = 116 + (len(conn_lines) * 34)
        draw.rounded_rectangle([card_x, curr_y, card_x + card_w, curr_y + n2_h], radius=14, fill="#F5ECE0", outline="#C6AE85", width=2)

        tag2 = "2. SINAVDA NEREDE ÇIKAR?"
        bbox = draw.textbbox((0, 0), tag2, font=self.font_node_tag)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([card_x + 22, curr_y + 16, card_x + 22 + tw + 30, curr_y + 50], radius=6, fill="#685028")
        draw.text((card_x + 37, curr_y + 20), tag2, fill="#FFFFFF", font=self.font_node_tag)

        tag_x = card_x + 28
        tag_y = curr_y + 64
        for topic in tyt_links:
            clean_topic = self.clean_special_chars(topic)
            tag_str = f"• {clean_topic}"
            bbox = draw.textbbox((0, 0), tag_str, font=self.font_node_bold)
            t_w = bbox[2] - bbox[0] + 28
            if tag_x + t_w > W - 80:
                tag_x = card_x + 28
                tag_y += 46
            draw.rounded_rectangle([tag_x, tag_y, tag_x + t_w, tag_y + 38], radius=6, fill="#E3D1AE", outline="#BFA87E")
            draw.text((tag_x + 14, tag_y + 4), tag_str, fill="#2A2214", font=self.font_node_bold)
            tag_x += t_w + 14

        cy = tag_y + 50
        for line in conn_lines:
            draw.text((card_x + 28, cy), line, fill="#4A3B22", font=self.font_node_bold)
            cy += 34
        curr_y += n2_h

        # FLOW ARROW 2 -> 3 (Maksimum Genişlik: 95px)
        arrow_h = 95
        draw.line([mid_x, curr_y, mid_x, curr_y + arrow_h], fill="#8C682D", width=4)
        draw.polygon([(mid_x, curr_y + arrow_h), (mid_x - 9, curr_y + arrow_h - 14), (mid_x + 9, curr_y + arrow_h - 14)], fill="#8C682D")
        
        lbl = "Gerçek Dünya Bağlantısı"
        bbox = draw.textbbox((0, 0), lbl, font=self.font_arrow_lbl)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(mid_x - tw/2 - 22), curr_y + 28, (mid_x + tw/2 + 22), curr_y + 66], radius=8, fill="#EFE4D0", outline="#CDBB9B", width=2)
        draw.text((mid_x - tw/2, curr_y + 34), lbl, fill="#5B4527", font=self.font_arrow_lbl)
        curr_y += arrow_h

        # ---------------------------------------------------------
        # NODE 3: ŞAŞIRTICI BİLGİ & GÜNLÜK HAYAT
        # ---------------------------------------------------------
        fact_lines = self.wrap_text(f"Şaşırtıcı Bilgi: {surprising_fact}", width=38)
        if daily_life:
            fact_lines.append("")
            fact_lines.extend(self.wrap_text(f"Günlük Hayat: {daily_life}", width=38))
        n3_h = len(fact_lines) * 34 + 76
        draw.rounded_rectangle([card_x, curr_y, card_x + card_w, curr_y + n3_h], radius=14, fill="#FFFFFF", outline="#D8C8A8", width=2)

        tag3 = "3. BİLİYOR MUYDUNUZ?"
        bbox = draw.textbbox((0, 0), tag3, font=self.font_node_tag)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([card_x + 22, curr_y + 16, card_x + 22 + tw + 30, curr_y + 50], radius=6, fill="#7B6133")
        draw.text((card_x + 37, curr_y + 20), tag3, fill="#FFFFFF", font=self.font_node_tag)

        fy = curr_y + 64
        for line in fact_lines:
            if line.startswith("Şaşırtıcı Bilgi:") or line.startswith("Günlük Hayat:"):
                draw.text((card_x + 28, fy), line, fill="#3E3018", font=self.font_node_bold)
            else:
                draw.text((card_x + 28, fy), line, fill="#3E3018", font=self.font_node_body)
            fy += 34

        self.draw_footer_swipe(draw, W, H, text="Kaydırın: Günün Sorusu")

        if filename is None:
            filename = f"slide_2_mindmap_day_{day_num:03d}.jpg"
        out_path = os.path.join(self.output_dir, filename)
        img.save(out_path, quality=95)
        print(f"Rendered Slide 2 (Mind Map): {out_path}")
        return out_path

    # =========================================================================
    # SLIDE 3: GÜNÜN SORUSU & İNTERAKTİF TEST (MAKSİMUM BOŞLUKLAR & GÜVENLİ BÖLGE)
    # =========================================================================
    def generate_slide_3_quiz(self, day_data, filename=None):
        day_num = day_data["day"]
        title = self.clean_special_chars(day_data["title"].upper())
        quiz = day_data.get("quiz", {})
        quiz_q = self.clean_special_chars(quiz.get("question", ""))
        quiz_opts = [self.clean_special_chars(o) for o in quiz.get("options", [])]

        W, H = 1080, 1920
        img = Image.new("RGB", (W, H), color="#FBF8F1")
        draw = ImageDraw.Draw(img)
        self.draw_base_frame(draw, W, H)

        curr_y = self.draw_top_branding(draw, W, 210, slide_num=3)

        # Header Badge
        badge_str = f"GÜNÜN YKS MATEMATİK SORUSU • GÜN {day_num}"
        bbox = draw.textbbox((0, 0), badge_str, font=self.font_badge)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 52) / 2, curr_y, (W + tw + 52) / 2, curr_y + 46], radius=8, fill="#D4AF37")
        draw.text(((W - tw) / 2, curr_y + 9), badge_str, fill="#1E1911", font=self.font_badge)
        curr_y += 68

        # Subtitle
        sub_str = f"Konu: {title}"
        bbox = draw.textbbox((0, 0), sub_str, font=self.font_era)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, curr_y), sub_str, fill="#7A5A29", font=self.font_era)
        curr_y += 52

        draw.line([140, curr_y, W - 140, curr_y], fill="#DAC9A6", width=2)
        curr_y += 50

        card_w = W - 140
        card_x = 70

        # Giant Question Card (Fills generously)
        q_lines = self.wrap_text(quiz_q, width=28)
        q_card_h = len(q_lines) * 54 + 104
        draw.rounded_rectangle([card_x, curr_y, card_x + card_w, curr_y + q_card_h], radius=16, fill="#FFFDF7", outline="#8C682D", width=3)
        
        tag_q = "GÜNÜN SORUSU"
        bbox = draw.textbbox((0, 0), tag_q, font=self.font_node_tag)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([card_x + 26, curr_y + 18, card_x + 26 + tw + 30, curr_y + 52], radius=6, fill="#8C682D")
        draw.text((card_x + 41, curr_y + 22), tag_q, fill="#FFFFFF", font=self.font_node_tag)

        qy = curr_y + 72
        for line in q_lines:
            draw.text((card_x + 32, qy), line, fill="#1E1911", font=self.font_quiz_hero)
            qy += 54

        # Expanded Gap before Choice Buttons (64px)
        curr_y += q_card_h + 64

        # 4 Large Interactive Choice Buttons (Height: 96px, Gap: 32px)
        opt_labels = ["A", "B", "C", "D"]
        for i, opt in enumerate(quiz_opts):
            opt_h = 96
            draw.rounded_rectangle([card_x, curr_y, card_x + card_w, curr_y + opt_h], radius=16, fill="#241E15", outline="#8C682D", width=2)
            
            # Letter Badge Circle (Larger diameter: 56px)
            draw.ellipse([card_x + 22, curr_y + 20, card_x + 78, curr_y + 76], fill="#D4AF37")
            draw.text((card_x + 37, curr_y + 26), opt_labels[i], fill="#1E1911", font=self.font_quiz_letter)
            
            # Option Text
            draw.text((card_x + 100, curr_y + 28), opt, fill="#F7EAC7", font=self.font_quiz_opt_lg)
            curr_y += opt_h + 32

        curr_y += 36

        # Call to Action Banner (Centered and balanced)
        cta_text = "Doğru cevabınızı yoruma yazın veya hikayeye yanıt verin!"
        bbox = draw.textbbox((0, 0), cta_text, font=self.font_node_bold)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, curr_y), cta_text, fill="#5B4527", font=self.font_node_bold)
        curr_y += 44

        f_sol = "Detaylı çözüm yarın sabahki hikayede açıklanacak!"
        bbox = draw.textbbox((0, 0), f_sol, font=self.font_small)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, curr_y), f_sol, fill="#8C682D", font=self.font_small)

        # Footer branding (inside Safe Zone at y = 1620)
        footer_y = 1620
        draw.line([100, footer_y, W - 100, footer_y], fill="#DAC9A6", width=1)
        f1 = "Hazırlayan: @mufithocailematematik  |  Kaynak: @riyazihane"
        bbox = draw.textbbox((0, 0), f1, font=self.font_footer)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, footer_y + 14), f1, fill="#3A2D16", font=self.font_footer)

        if filename is None:
            filename = f"slide_3_quiz_day_{day_num:03d}.jpg"
        out_path = os.path.join(self.output_dir, filename)
        img.save(out_path, quality=95)
        print(f"Rendered Slide 3 (Quiz): {out_path}")
        return out_path

    def generate_day_suite(self, day_data):
        day_num = day_data["day"]
        s1 = self.generate_slide_1_cover(day_data, filename=f"day_{day_num:03d}_slide_1_cover.jpg")
        s2 = self.generate_slide_2_mindmap(day_data, filename=f"day_{day_num:03d}_slide_2_mindmap.jpg")
        s3 = self.generate_slide_3_quiz(day_data, filename=f"day_{day_num:03d}_slide_3_quiz.jpg")
        return [s1, s2, s3]

if __name__ == "__main__":
    with open("data/campaign_97_days.json", "r", encoding="utf-8") as f:
        days = json.load(f)

    gen = MultiSlideStoryGenerator()
    d9 = next(x for x in days if x["day"] == 9)
    gen.generate_day_suite(d9)
