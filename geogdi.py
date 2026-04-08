import pygame
import sys
import os
import ctypes
import ctypes.wintypes
import struct
import random

# --- 1. INITIALIZE ---
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 400, 300 

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

sw = user32.GetSystemMetrics(0)
sh = user32.GetSystemMetrics(1)

# Position: Moved away from the border
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{sw - WIDTH - 100},{sh - HEIGHT - 100}"
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)

# Stay on top
hwnd = pygame.display.get_wm_info()['window']
user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)

title_font = pygame.font.SysFont("Impact", 28)
title_text = title_font.render("FEED ME OR SUFFER", True, (255, 0, 0))

# --- 2. ASSETS ---
try:
    cube_img = pygame.image.load("cube_458.png").convert_alpha()
    spike_img = pygame.image.load("Spike.png").convert_alpha()
    cube_trail = pygame.transform.scale(cube_img, (100, 100))
    spike_trail = pygame.transform.scale(spike_img, (40, 40))
    
    nums = {str(i): pygame.image.load(f"font1 - {i}.png").convert_alpha() for i in range(10)}
    nums[":"] = pygame.image.load("font1 - message.png").convert_alpha()
    spam_sound = pygame.mixer.Sound("accurate-hitboxes_mMp76Hy.mp3")
except Exception as e:
    print(f"Asset Error: {e}"); sys.exit()

def stamp_png(hdc, surface, x, y):
    w, h = surface.get_size()
    img_str = pygame.image.tostring(surface, "BGRA", False)
    bmi = struct.pack('<IiiHHIIiiII', 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    gdi32.StretchDIBits(hdc, x, y, w, h, 0, 0, w, h, img_str, bmi, 0, 0x00CC0020)

# --- 3. MAIN LOOP ---
hdc_handle = user32.GetDC(0)
time_left = 60.0 
gdi_pos = [sw // 2, sh // 2]
gdi_speed = [25, 25]
clock = pygame.time.Clock()

while True:
    dt = clock.tick(60) / 1000.0
    
    # Get Mouse Pos
    point = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    mx, my = point.x, point.y
    
    # --- ANTI-CLOSE LOGIC ---
    if time_left <= 0:
        # Aggressive jitter
        jx = mx + random.randint(-20, 20)
        jy = my + random.randint(-20, 20)
        
        # If the mouse gets too close to the Pygame window, throw it away!
        # This makes dropping the 'pill' very difficult.
        win_x, win_y = sw - WIDTH - 100, sh - HEIGHT - 100
        if win_x < mx < win_x + WIDTH and win_y < my < win_y + HEIGHT:
            user32.SetCursorPos(mx - 150, my - 150)
        else:
            user32.SetCursorPos(jx, jy)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pass # Totally uncloseable via UI
        
        if event.type == pygame.DROPFILE:
            file_path = event.file.lower()
            file_name = os.path.basename(file_path)
            
            # THE CURE: Dropping 'sleeping.pill' closes the program
            if file_name == "sleeping.pill":
                user32.ReleaseDC(0, hdc_handle)
                pygame.quit()
                sys.exit()
                
            elif file_path.endswith(".pill"):
                time_left = min(time_left + 60, 600)
            elif file_path.endswith(".hitbox"):
                time_left = max(0, time_left - 30)
                gdi32.PatBlt(hdc_handle, 0, 0, sw, sh, 0x5A0049)

    # --- 4. RENDER UI ---
    screen.fill((5, 5, 5))
    
    # Pulsing red background when angry
    if time_left <= 0:
        screen.fill((random.randint(20, 50), 0, 0))
    
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 15))
    screen.blit(pygame.transform.scale(cube_img, (60, 60)), (WIDTH//2 - 30, 60))
    
    display_val = max(0, time_left)
    t_str = f"{int(display_val//60)}:{int(display_val%60):02}"
    curr_x = WIDTH // 2 - 60 
    for c in t_str:
        screen.blit(nums[c], (curr_x, 140))
        curr_x += nums[c].get_width() - 2

    # --- 5. PAYLOAD ---
    if time_left <= 0:
        if not pygame.mixer.get_busy(): 
            spam_sound.play()
        
        stamp_png(hdc_handle, spike_trail, mx - 20, my - 20)
        
        gdi_pos[0] += gdi_speed[0]
        gdi_pos[1] += gdi_speed[1]
        if gdi_pos[0] <= 0 or gdi_pos[0] >= sw - 100: gdi_speed[0] *= -1
        if gdi_pos[1] <= 0 or gdi_pos[1] >= sh - 100: gdi_speed[1] *= -1
        stamp_png(hdc_handle, cube_trail, int(gdi_pos[0]), int(gdi_pos[1]))
    else:
        time_left -= dt

    pygame.display.flip()
