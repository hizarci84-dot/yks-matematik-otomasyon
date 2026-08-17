import os
import sys
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class DiagramStoryGenerator:
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

        self.font_brand = get_font("TitleBold.ttf", 25)
        self.font_brand_sub = get_font("BodyBold.ttf", 18)
        self.font_badge = get_font("TitleBold.ttf", 20)
        self.font_title = get_font("TitleBold.ttf", 34)
        self.font_era = get_font("SerifBold.ttf", 22)
        
        # Diagram Node Fonts
        self.font_node_tag = get_font("TitleBold.ttf", 17)
        self.font_node_title = get_font("TitleBold.ttf", 21)
        self.font_node_body = get_font("Body.ttf", 21)
        self.font_node_bold = get_font("BodyBold.ttf", 21)
        self.font_arrow_lbl = get_font("TitleBold.ttf", 16)
        self.font_quiz_opt = get_font("BodyBold.ttf", 20)
        self.font_small = get_font("Body.ttf", 16)
        self.font_footer = get_font("TitleBold.ttf", 19)
        self.font_footer_sub = get_font("Serif.ttf", 17)

    def clean_special_chars(self, text):
        # Sanitize text so standard TrueType fonts render without glyph missing boxes
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
            .strip()
        )

    def wrap_text(self, text, width=48):
        cleaned = self.clean_special_chars(text)
        lines = []
        for p in cleaned.split("\n"):
            if p.strip():
                lines.extend(textwrap.wrap(p.strip(), width=width))
        return lines

    def draw_bullet_diamond(self, draw, x, y, size=5, color="#8C682D"):
        draw.polygon([(x, y - size), (x + size, y), (x, y + size), (x - size, y)], fill=color)

    def draw_node_box(self, draw, x, y, w, h, bg_color="#FFFFFF", border_color="#CDBB9B", radius=12):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg_color, outline=border_color, width=2)

    def draw_flow_arrow(self, draw, x1, y1, x2, y2, label="", color="#A08048"):
        draw.line([x1, y1, x2, y2], fill=color, width=3)
        ah = 8
        draw.polygon([(x2, y2), (x2 - 5, y2 - ah), (x2 + 5, y2 - ah)], fill=color)
        
        if label:
            bbox = draw.textbbox((0, 0), label, font=self.font_arrow_lbl)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            my = (y1 + y2) / 2
            pill_w = tw + 18
            pill_h = 24
            draw.rounded_rectangle([(x1 - pill_w / 2), my - pill_h / 2, (x1 + pill_w / 2), my + pill_h / 2], radius=6, fill="#EFE4D0", outline="#CDBB9B")
            draw.text((x1 - tw / 2, my - th / 2 - 2), label, fill="#5B4527", font=self.font_arrow_lbl)

    def generate_diagram_story(self, day_data, filename=None):
        day_num = day_data["day"]
        raw_title = day_data["title"].upper()
        title = self.clean_special_chars(raw_title)
        era_figure = self.clean_special_chars(day_data.get("era_figure", ""))
        hook = self.clean_special_chars(day_data.get("hook", ""))
        history = self.clean_special_chars(day_data.get("history", ""))
        tyt_links = day_data.get("tyt_ayt_links", [])
        daily_life = self.clean_special_chars(day_data.get("daily_life", ""))
        conn_note = self.clean_special_chars(day_data.get("connection_note", ""))
        surprising_fact = self.clean_special_chars(day_data.get("surprising_fact", ""))
        quiz = day_data.get("quiz", {})

        W, H = 1080, 1920
        img = Image.new("RGB", (W, H), color="#FBF8F1")
        draw = ImageDraw.Draw(img)

        # 1. Classical Diagram Grid / Frame
        draw.rectangle([24, 24, W - 24, H - 24], outline="#C4A66B", width=2)
        draw.rectangle([32, 32, W - 32, H - 32], outline="#E8DEC8", width=1)
        for cx, cy in [(32, 32), (W - 32, 32), (32, H - 32), (W - 32, H - 32)]:
            self.draw_bullet_diamond(draw, cx, cy, size=6, color="#8C6A2E")

        # ==========================================
        # TOP SAFE ZONE (Start content below y = 210)
        # ==========================================
        curr_y = 210

        # Header Branding
        h_brand = "MÜFİT HOCA İLE MATEMATİK"
        bbox = draw.textbbox((0, 0), h_brand, font=self.font_brand)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, curr_y), h_brand, fill="#2A2114", font=self.font_brand)
        curr_y += 32

        # Attribution Pill
        h_attr = "Kaynak: @riyazihane  •  @mufithocailematematik"
        bbox = draw.textbbox((0, 0), h_attr, font=self.font_brand_sub)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 28) / 2, curr_y, (W + tw + 28) / 2, curr_y + 28], radius=14, fill="#EFE5D0")
        draw.text(((W - tw) / 2, curr_y + 4), h_attr, fill="#5C482C", font=self.font_brand_sub)
        curr_y += 38

        # Badge: KAVRAM DİYAGRAMI & ZİHİN HARİTASI
        badge_str = f"KAVRAM DİYAGRAMI • GÜN {day_num} / 97"
        bbox = draw.textbbox((0, 0), badge_str, font=self.font_badge)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([(W - tw - 32) / 2, curr_y, (W + tw + 32) / 2, curr_y + 32], radius=8, fill="#8C682D")
        draw.text(((W - tw) / 2, curr_y + 5), badge_str, fill="#FFFFFF", font=self.font_badge)
        curr_y += 40

        # Main Title
        title_lines = self.wrap_text(title, width=32)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=self.font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), line, fill="#1B1710", font=self.font_title)
            curr_y += 40

        if era_figure:
            sub_str = f"~ {era_figure} ~"
            bbox = draw.textbbox((0, 0), sub_str, font=self.font_era)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, curr_y), sub_str, fill="#7A5A29", font=self.font_era)
            curr_y += 30
        else:
            curr_y += 6

        draw.line([140, curr_y, W - 140, curr_y], fill="#DAC9A6", width=1)
        curr_y += 18

        card_w = W - 120
        card_x = 60
        mid_x = W / 2

        # =========================================================================
        # NODE 1: TARİHSEL PROBLEM & İHTİYAÇ
        # =========================================================================
        n1_hook_lines = self.wrap_text(f"“{hook}”", width=44)
        n1_hist_lines = self.wrap_text(f"Mantık: {history}", width=48)
        n1_lines = n1_hook_lines + n1_hist_lines
        n1_h = len(n1_lines) * 27 + 52

        self.draw_node_box(draw, card_x, curr_y, card_w, n1_h, bg_color="#FFFDF7", border_color="#D5C099", radius=12)
        
        # Pill Tag inside box
        draw.rounded_rectangle([card_x + 18, curr_y + 10, card_x + 230, curr_y + 34], radius=6, fill="#8C682D")
        draw.text((card_x + 28, curr_y + 13), "1. TARİHSEL İHTİYAÇ", fill="#FFFFFF", font=self.font_node_tag)
        
        ny = curr_y + 42
        for line in n1_hook_lines:
            draw.text((card_x + 24, ny), line, fill="#38260B", font=self.font_node_bold)
            ny += 27
        ny += 2
        for line in n1_hist_lines:
            draw.text((card_x + 24, ny), line, fill="#2C261D", font=self.font_node_body)
            ny += 27

        curr_y += n1_h

        # FLOW ARROW 1 -> 2
        arrow_h = 42
        self.draw_flow_arrow(draw, mid_x, curr_y, mid_x, curr_y + arrow_h, label="Matematiksel Modelleme")
        curr_y += arrow_h

        # =========================================================================
        # NODE 2: TYT - AYT SINAV KÖPRÜSÜ
        # =========================================================================
        conn_str = conn_note if conn_note else "Temel Kavramlar > Modelleme > Analiz"
        n2_conn_lines = self.wrap_text(f"Kavram Zinciri: {conn_str}", width=46)
        n2_h = 76 + (len(n2_conn_lines) * 25)

        self.draw_node_box(draw, card_x, curr_y, card_w, n2_h, bg_color="#F5ECE0", border_color="#C6AE85", radius=12)
        
        draw.rounded_rectangle([card_x + 18, curr_y + 10, card_x + 260, curr_y + 34], radius=6, fill="#685028")
        draw.text((card_x + 28, curr_y + 13), "2. TYT - AYT SINAV KÖPRÜSÜ", fill="#FFFFFF", font=self.font_node_tag)

        # Subject Badges
        tag_x = card_x + 24
        tag_y = curr_y + 42
        for topic in tyt_links:
            clean_topic = self.clean_special_chars(topic)
            tag_str = f"• {clean_topic}"
            bbox = draw.textbbox((0, 0), tag_str, font=self.font_node_bold)
            t_w = bbox[2] - bbox[0] + 18
            if tag_x + t_w > W - 80:
                tag_x = card_x + 24
                tag_y += 32
            draw.rounded_rectangle([tag_x, tag_y, tag_x + t_w, tag_y + 24], radius=6, fill="#E3D1AE", outline="#BFA87E")
            draw.text((tag_x + 8, tag_y + 2), tag_str, fill="#2A2214", font=self.font_node_bold)
            tag_x += t_w + 10

        cy = tag_y + 32
        for line in n2_conn_lines:
            draw.text((card_x + 24, cy), line, fill="#4A3B22", font=self.font_node_bold)
            cy += 25

        curr_y += n2_h

        # FLOW ARROW 2 -> 3
        arrow_h = 40
        self.draw_flow_arrow(draw, mid_x, curr_y, mid_x, curr_y + arrow_h, label="Günlük Hayat & Uygulama")
        curr_y += arrow_h

        # =========================================================================
        # NODE 3: GERÇEK DÜNYA ETKİSİ
        # =========================================================================
        n3_fact_lines = self.wrap_text(f"Şaşırtıcı Bilgi: {surprising_fact}", width=48)
        if daily_life:
            n3_fact_lines.append("")
            n3_fact_lines.extend(self.wrap_text(f"Günlük Hayat: {daily_life}", width=48))
        n3_h = len(n3_fact_lines) * 25 + 46

        self.draw_node_box(draw, card_x, curr_y, card_w, n3_h, bg_color="#FFFFFF", border_color="#D8C8A8", radius=12)
        
        draw.rounded_rectangle([card_x + 18, curr_y + 10, card_x + 230, curr_y + 34], radius=6, fill="#7B6133")
        draw.text((card_x + 28, curr_y + 13), "3. GERÇEK DÜNYA ETKİSİ", fill="#FFFFFF", font=self.font_node_tag)

        fy = curr_y + 42
        for line in n3_fact_lines:
            if line.startswith("Şaşırtıcı Bilgi:") or line.startswith("Günlük Hayat:"):
                draw.text((card_x + 24, fy), line, fill="#3E3018", font=self.font_node_bold)
            else:
                draw.text((card_x + 24, fy), line, fill="#3E3018", font=self.font_node_body)
            fy += 25

        curr_y += n3_h

        # FLOW ARROW 3 -> 4
        arrow_h = 36
        self.draw_flow_arrow(draw, mid_x, curr_y, mid_x, curr_y + arrow_h, label="Zihin Testi")
        curr_y += arrow_h

        # =========================================================================
        # NODE 4: GÜNÜN SORUSU (Quiz Node)
        # =========================================================================
        quiz_q = self.clean_special_chars(quiz.get("question", ""))
        quiz_opts = [self.clean_special_chars(o) for o in quiz.get("options", [])]
        quiz_lines = self.wrap_text(f"GÜNÜN SORUSU: {quiz_q}", width=44)
        
        grid_rows = 2 if len(quiz_opts) == 4 else len(quiz_opts)
        quiz_h = len(quiz_lines) * 27 + 54 + (grid_rows * 38)

        self.draw_node_box(draw, card_x, curr_y, card_w, quiz_h, bg_color="#1E1911", border_color="#8C682D", radius=12)
        
        draw.rounded_rectangle([card_x + 18, curr_y + 10, card_x + 190, curr_y + 34], radius=6, fill="#D4AF37")
        draw.text((card_x + 28, curr_y + 13), "4. GÜNÜN SORUSU", fill="#1E1911", font=self.font_node_tag)

        qy = curr_y + 44
        for line in quiz_lines:
            draw.text((card_x + 24, qy), line, fill="#F7EAC7", font=self.font_node_bold)
            qy += 27
        
        if len(quiz_opts) == 4:
            opt_labels = ["A", "B", "C", "D"]
            opt_w = (card_w - 60) / 2
            opt_h = 30
            qy += 4
            for i, opt in enumerate(quiz_opts):
                col = i % 2
                row = i // 2
                ox = card_x + 20 + col * (opt_w + 16)
                oy = qy + row * (opt_h + 8)
                draw.rounded_rectangle([ox, oy, ox + opt_w, oy + opt_h], radius=6, fill="#2F271B", outline="#6A573B")
                lbl_text = f"[{opt_labels[i]}] {opt}"
                draw.text((ox + 10, oy + 4), lbl_text, fill="#F5E8C7", font=self.font_quiz_opt)
            qy += 2 * (opt_h + 8) + 2
        
        draw.text((card_x + 24, qy + 2), "Cevabınızı yoruma yazın veya ankete katılın!", fill="#D8B772", font=self.font_small)
        curr_y += quiz_h + 14

        # ==========================================
        # BOTTOM SAFE ZONE FOOTER (y ~ 1650)
        # ==========================================
        footer_y = curr_y + 6
        draw.line([100, footer_y, W - 100, footer_y], fill="#DAC9A6", width=1)
        
        f1 = "Hazırlayan: @mufithocailematematik  |  Kaynak: @riyazihane"
        bbox = draw.textbbox((0, 0), f1, font=self.font_footer)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, footer_y + 8), f1, fill="#3A2D16", font=self.font_footer)
        
        f2 = "“Matematik sadece formül değil; insanlığın düşünme tarihidir.”"
        bbox = draw.textbbox((0, 0), f2, font=self.font_footer_sub)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, footer_y + 32), f2, fill="#7A6849", font=self.font_footer_sub)

        # Save Image
        if filename is None:
            filename = f"diagram_day_{day_num:03d}.jpg"
        out_path = os.path.join(self.output_dir, filename)
        img.save(out_path, quality=95)
        print(f"Rendered polished diagram story: {out_path}")
        return out_path

if __name__ == "__main__":
    with open("data/campaign_97_days.json", "r", encoding="utf-8") as f:
        days = json.load(f)

    gen = DiagramStoryGenerator()
    
    # Test Day 9
    d9 = next(x for x in days if x["day"] == 9)
    gen.generate_diagram_story(d9, filename="test_diagram_day_009.jpg")
    
    # Test Day 1
    d1 = next(x for x in days if x["day"] == 1)
    gen.generate_diagram_story(d1, filename="test_diagram_day_001.jpg")
