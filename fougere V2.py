import sys
import os
import random
import colorsys


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

pygame.init()


# Initialisation silencieuse de pygame 
# with open(os.devnull, 'w') as f:
#     old_stdout = sys.stdout
#     sys.stdout = f
#     pygame.init()
#     sys.stdout = old_stdout


class ColorSelector:
    def __init__(self, title="Color Selector", label=None):

        self.title = title

        # Libellé affiché en haut
        if label is not None:
            self.label = label
        elif "background" in title.lower():
            self.label = "Background color"
        elif "point" in title.lower():
            self.label = "Point color"
        else:
            self.label = "Color"

        self.r = random.randint(0, 255)
        self.g = random.randint(0, 255)
        self.b = random.randint(0, 255)

        self.running = True
        self.dragging_slider = None

        # Taille de la fenêtre
        self.WIDTH = 600
        self.HEIGHT = 400

        # Layout sliders et inputs
        self.SLIDER_X = 40
        self.SLIDER_W = 470
        self.SLIDER_H = 20
        self.SLIDER_RADIUS = 8  # coins arrondis du track
        self.INPUT_W = 50
        self.INPUT_X = self.SLIDER_X + self.SLIDER_W + 20  # 530 dans 600

        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(self.title)

        # Police
        try:
            self.font = pygame.font.SysFont("Segoe UI", 18)
        except Exception:
            self.font = pygame.font.SysFont(None, 18)

        # Etat d'édition
        self.input_active = None

        # Valeurs affichées dans les champs
        self.input_boxes = {"R": str(self.r), "G": str(self.g), "B": str(self.b)}

        # Position verticale des contrôles
        self.slider_positions = {"R": 80, "G": 130, "B": 180}

        # Presets rapides
        self.presets = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 255),
            (230, 230, 230),
            (0, 0, 0),
        ]

        # Presse-papiers et curseur
        try:
            pygame.scrap.init()
        except Exception:
            pass  
        self.caret_pos = {
            "R": len(self.input_boxes["R"]),
            "G": len(self.input_boxes["G"]),
            "B": len(self.input_boxes["B"]),
        }
        # selection[name] = None ou (start, end)
        self.selection = {"R": None, "G": None, "B": None}

        self.cursor_timer = 0
        self.cursor_visible = True

    # ---------- Utilitaires d'affichage ----------

    def _readable_text_color(self):
        brightness = 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b
        return (0, 0, 0) if brightness > 140 else (255, 255, 255)

    def _center_x_for_surface(self, surface):
        return (self.WIDTH - surface.get_width()) // 2

    def _preset_centers(self, radius=15, spacing=45):
        n = len(self.presets)
        total_width = (n - 1) * spacing + 2 * radius
        left_edge = (self.WIDTH - total_width) // 2
        first_center = left_edge + radius
        return [first_center + i * spacing for i in range(n)]

    # ---------- Rendu des contrôles ----------

    def draw_gradient_slider(self, x, y, color_index):
    
    
    

    # 1) Gradient du canal (0..255 étiré sur la largeur)
        grad = pygame.Surface((self.SLIDER_W, self.SLIDER_H), pygame.SRCALPHA)
        for i in range(self.SLIDER_W):
            val = int(i * 255 / (self.SLIDER_W - 1))
            c = [0, 0, 0]
            c[color_index] = val
            pygame.draw.line(grad, (*c, 255), (i, 0), (i, self.SLIDER_H - 1))

    # 2) Masque à bords arrondis pour rogner le track
        mask = pygame.Surface((self.SLIDER_W, self.SLIDER_H), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), pygame.Rect(0, 0, self.SLIDER_W, self.SLIDER_H), border_radius=self.SLIDER_RADIUS)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # 3) Afficher le track (aucun fond, aucune bordure)
        self.screen.blit(grad, (x, y))

    # 4) FONDU: léger highlight vertical (alpha 32 -> 0 du haut vers le bas)
        highlight = pygame.Surface((self.SLIDER_W, self.SLIDER_H), pygame.SRCALPHA)
        for j in range(self.SLIDER_H):
            a = int(20 * (1 - j / (self.SLIDER_H - 1)))  # top plus clair, bas nul
            pygame.draw.line(highlight, (255, 255, 255, a), (0, j), (self.SLIDER_W - 1, j))
        highlight.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(highlight, (x, y))

        # 5) Bille: couleur inverse + liseré noir (ça, on garde)
        channel_value = getattr(self, "rgb"[color_index])
        handle_x = x + int(channel_value * self.SLIDER_W / 255)
        inv = (255 - self.r, 255 - self.g, 255 - self.b)
        center = (handle_x, y + self.SLIDER_H // 2)
        pygame.draw.circle(self.screen, inv, center, 10)
        pygame.draw.circle(self.screen, (0, 0, 0), center, 10, 2)


    def draw_input_box(self, x, y, color_name):
        box_rect = pygame.Rect(x, y, self.INPUT_W, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), box_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), box_rect, 2, border_radius=5)

        text_str = self.input_boxes[color_name]
        text_surface = self.font.render(text_str, True, (0, 0, 0))
        self.screen.blit(text_surface, (box_rect.x + 5, box_rect.y + 5))

        # Curseur clignotant si le champ est actif
        if self.input_active == color_name and self.cursor_visible:
            caret = self.caret_pos[color_name]
            caret_x = box_rect.x + 5 + self.font.size(text_str[:caret])[0]
            caret_y1 = box_rect.y + 5
            caret_y2 = caret_y1 + text_surface.get_height()
            pygame.draw.line(self.screen, (0, 0, 0), (caret_x, caret_y1), (caret_x, caret_y2), 1)

    # ---------- Logique ----------

    def update_color_from_input(self, color_name):

        try:
            value = int(self.input_boxes[color_name])
        except ValueError:
            return
        value = max(0, min(value, 255))
        setattr(self, color_name.lower(), value)

    def rgb_to_hex(self):
        return f'# {self.r:02X}{self.g:02X}{self.b:02X}'

    def rgb_to_hsl(self):
        h, l, s = colorsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
        return f"HSL: {int(h * 360)}°, {int(s * 100)}%, {int(l * 100)}%"

    def run(self):
        clock = pygame.time.Clock()

        while self.running:

            dt = clock.tick(60)
            self.cursor_timer += dt
            if self.cursor_timer >= 500:
                self.cursor_timer = 0
                self.cursor_visible = not self.cursor_visible

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()

                    # Début de glisser sur slider si clic dans la zone
                    for idx, name in enumerate("RGB"):
                        sy = self.slider_positions[name]
                        if (self.SLIDER_X <= x <= self.SLIDER_X + self.SLIDER_W) and (sy <= y <= sy + self.SLIDER_H):
                            self.dragging_slider = idx

                    # Activation d'une input box
                    for name in "RGB":
                        box = pygame.Rect(self.INPUT_X, self.slider_positions[name] - 5, self.INPUT_W, 30)
                        if box.collidepoint(x, y):
                            self.input_active = name
                            self.caret_pos[name] = len(self.input_boxes[name])
                            self.selection[name] = None

                    # Clic sur un preset (sélection couleur)
                    centers_x = self._preset_centers()
                    radius = 15
                    for i, color in enumerate(self.presets):
                        cx, cy = centers_x[i], 330
                        if pygame.Rect(cx - radius, cy - radius, 2 * radius, 2 * radius).collidepoint(x, y):
                            self.r, self.g, self.b = color
                            self.input_boxes = {"R": str(self.r), "G": str(self.g), "B": str(self.b)}
                            for n in "RGB":
                                self.caret_pos[n] = len(self.input_boxes[n])
                                self.selection[n] = None

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging_slider = None

                elif event.type == pygame.MOUSEMOTION and self.dragging_slider is not None:
                    # Met à jour la valeur du canal en cours de glisser, mappée sur 0..255
                    mx = pygame.mouse.get_pos()[0]
                    rel = max(0, min(mx - self.SLIDER_X, self.SLIDER_W))
                    value = int(rel * 255 / self.SLIDER_W)
                    setattr(self, "rgb"[self.dragging_slider], value)
                    self.input_boxes["RGB"[self.dragging_slider]] = str(value)

                    self.cursor_visible = True
                    self.cursor_timer = 0

                elif event.type == pygame.KEYDOWN and self.input_active:

                    name = self.input_active
                    s = self.input_boxes[name]
                    caret = self.caret_pos[name]
                    sel = self.selection[name]

                    mods = pygame.key.get_mods()
                    ctrl = bool(mods & pygame.KMOD_CTRL)

                    def delete_selection():
                        nonlocal s, caret, sel
                        if sel:
                            a, b = sorted(sel)
                            s = s[:a] + s[b:]
                            caret = a
                            sel = None

                    if event.key == pygame.K_RETURN:
                        self.update_color_from_input(name)
                        self.input_active = None
                        self.selection[name] = None

                    elif ctrl and event.key == pygame.K_a:
                        self.selection[name] = (0, len(s))
                        self.caret_pos[name] = len(s)

                    elif ctrl and event.key == pygame.K_c:
                        try:
                            a, b = (0, len(s)) if not sel else sorted(sel)
                            pygame.scrap.put(pygame.SCRAP_TEXT, s[a:b].encode('utf-8'))
                        except Exception:
                            pass

                    elif ctrl and event.key == pygame.K_v:
                        try:
                            clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                        except Exception:
                            clip = None
                        if clip:
                            try:
                                clip_text = clip.decode('utf-8', errors='ignore').replace('\x00', '')
                            except Exception:
                                clip_text = ''
                            clip_text = ''.join(ch for ch in clip_text if ch.isdigit())
                            if clip_text:
                                delete_selection()
                                s = s[:caret] + clip_text + s[caret:]
                                caret += len(clip_text)

                    elif event.key == pygame.K_BACKSPACE:
                        if sel:
                            delete_selection()
                        elif caret > 0:
                            s = s[:caret - 1] + s[caret:]
                            caret -= 1

                    elif event.key == pygame.K_DELETE:
                        if sel:
                            delete_selection()
                        elif caret < len(s):
                            s = s[:caret] + s[caret + 1:]

                    elif event.key == pygame.K_LEFT:
                        if sel:
                            a, _ = sorted(sel)
                            caret = a
                            sel = None
                        elif caret > 0:
                            caret -= 1

                    elif event.key == pygame.K_RIGHT:
                        if sel:
                            _, b = sorted(sel)
                            caret = b
                            sel = None
                        elif caret < len(s):
                            caret += 1

                    elif event.key == pygame.K_HOME:
                        caret, sel = 0, None

                    elif event.key == pygame.K_END:
                        caret, sel = len(s), None

                    elif event.key == pygame.K_TAB:
                        order = ["R", "G", "B"]
                        i = order.index(name)
                        name2 = order[(i - 1) % 3] if (mods & pygame.KMOD_SHIFT) else order[(i + 1) % 3]
                        self.input_active = name2
                        self.caret_pos[name2] = len(self.input_boxes[name2])
                        self.selection[name2] = None

                    else:
                        if event.unicode.isdigit():
                            delete_selection()
                            s = s[:caret] + event.unicode + s[caret:]
                            caret += 1

                    # Commit des modifications
                    self.input_boxes[name] = s
                    self.caret_pos[name] = caret
                    self.selection[name] = sel
                    self.cursor_visible = True
                    self.cursor_timer = 0

            # Fond = couleur sélectionnée
            self.screen.fill((self.r, self.g, self.b))

            # Sliders + inputs (input box déportée à INPUT_X)
            for idx, name in enumerate("RGB"):
                y = self.slider_positions[name]
                self.draw_gradient_slider(self.SLIDER_X, y, idx)
                self.draw_input_box(self.INPUT_X, y - 5, name)

            # Texte centrés et à contraste automatique
            text_color = self._readable_text_color()

            # Label de contexte (Background/Point color)
            label_surface = self.font.render(self.label, True, text_color)
            self.screen.blit(label_surface, (self._center_x_for_surface(label_surface), 30))

            # Hex / HSL
            hex_surface = self.font.render(f"Hex: {self.rgb_to_hex()}", True, text_color)
            hsl_surface = self.font.render(self.rgb_to_hsl(), True, text_color)
            self.screen.blit(hex_surface, (self._center_x_for_surface(hex_surface), 240))
            self.screen.blit(hsl_surface, (self._center_x_for_surface(hsl_surface), 270))

            # Presets centrés, bordure noire
            centers_x = self._preset_centers(radius=15, spacing=45)
            for i, color in enumerate(self.presets):
                cx, cy = centers_x[i], 330
                pygame.draw.circle(self.screen, color, (cx, cy), 15)
                pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), 16, 2)

            pygame.display.update()

        return (self.r, self.g, self.b)


# Définir les transformations pour la fractale de Barnsley
TRANSFORMATIONS = [
    (0.0, 0.0, 0.0, 0.16, 0.0, 0.0, 0.01),   # Tige
    (0.85, 0.04, -0.04, 0.85, 0.0, 1.6, 0.85),  # Grande feuille
    (0.2, -0.26, 0.23, 0.22, 0.0, 1.6, 0.07),   # Petite feuille gauche
    (-0.15, 0.28, 0.26, 0.24, 0.0, 0.44, 0.07)  # Petite feuille droite
]


def appliquer_transformation(x, y, transformation):
    a, b, c, d, e, f, _ = transformation
    return a * x + b * y + e, c * x + d * y + f


def dessiner_barnsley(screen, largeur, hauteur, point_color):
    x, y = 0.0, 0.0
    for _ in range(100_000):
        transformation = random.choices(
            TRANSFORMATIONS,
            weights=[t[6] for t in TRANSFORMATIONS]
        )[0]
        x, y = appliquer_transformation(x, y, transformation)
        px = int(largeur / 2 + x * 70)
        py = int(hauteur - y * 70)
        if 0 <= px < largeur and 0 <= py < hauteur:
            screen.set_at((px, py), point_color)


def main():
    # Sélecteur pour la couleur de fond
    bg_selector = ColorSelector("Background Color Selector", label="Background color")
    bg_color = bg_selector.run()

    # Sélecteur pour la couleur des points
    point_selector = ColorSelector("Point Color Selector", label="Point color")
    point_color = point_selector.run()

    # Fenêtre principale pour la fractale
    largeur, hauteur = 500, 500
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode((largeur, hauteur))
    pygame.display.set_caption("Fractale - Feuille de fougère de Barnsley")

    # Dessin
    screen.fill(bg_color)
    dessiner_barnsley(screen, largeur, hauteur, point_color)
    pygame.display.flip()

    # Boucle d'événements
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()


if __name__ == "__main__":
    main()
