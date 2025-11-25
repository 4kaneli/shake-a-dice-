import pygame
import random
import cv2
import mediapipe as mp
import math
import sys

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Dado Gesto Interattivo")
clock = pygame.time.Clock()

# Carica immagini dado e ridimensiona
try:
    dice_images = []
    for i in range(1, 7):
        img = pygame.image.load(f'dado{i}.png')
        img = pygame.transform.scale(img, (150, 150))
        dice_images.append(img)
except Exception as e:
    print("Errore caricamento immagini:", e)
    pygame.quit()
    sys.exit()

# Carica suoni
try:
    sound_shake = pygame.mixer.Sound("scuotere.wav")
    sound_roll = pygame.mixer.Sound("rolling.wav")
except Exception as e:
    print("Errore caricamento suoni:", e)
    pygame.quit()
    sys.exit()

# Webcam + Mediapipe
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Errore webcam.")
    pygame.quit()
    sys.exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

def mano_chiusa(landmarks):
    dita_piegate = 0
    dita = [8, 12, 16, 20]      # punta dita
    articolazioni = [6, 10, 14, 18]  # articolazioni PIP
    
    for punta, pip in zip(dita, articolazioni):
        if landmarks[punta].y > landmarks[pip].y:
            dita_piegate += 1
    
    return dita_piegate >= 3

def rileva_mano(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    risultati = hands.process(frame_rgb)
    if risultati.multi_hand_landmarks:
        mano = risultati.multi_hand_landmarks[0]
        return mano_chiusa(mano.landmark)
    else:
        return False

# Stato variabili
dado_pos = (245, 160)
mano_chiusa_flag = False
mano_chiusa_prec = False
dado_visibile = True
dado_corrente = random.randint(0, 5)
suono_scuotere_in_corso = False

# Variabili per rotazione e tremolio
angolo_rotazione = 0
tremolio_frames = 0
TREMOLIO_DURATA = 15  # durata tremolio in frame
TREMOLIO_INTENSITA = 5  # pixels massimo spostamento tremolio

print("Avviato: mano aperta → dado visibile fermo, mano chiusa → dado sparisce, riapre mano → dado cambia immagine, ruotato e tremolio")

running = True
while running:
    ret, frame = cap.read()
    if not ret:
        print("Errore lettura webcam.")
        break

    mano_chiusa_flag = rileva_mano(frame)
    cv2.imshow("Webcam", frame)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Gestione transizioni mano
    if mano_chiusa_flag and not mano_chiusa_prec:
        # Mano chiusa → dado scompare + loop suono scuotere
        dado_visibile = False
        if not suono_scuotere_in_corso:
            sound_shake.play(-1)
            suono_scuotere_in_corso = True

    if not mano_chiusa_flag and mano_chiusa_prec:
        # Mano riaperta → dado appare con immagine nuova casuale + suono rolling + rotazione + tremolio
        dado_visibile = True
        sound_shake.stop()
        suono_scuotere_in_corso = False
        sound_roll.play()

        # Cambia immagine dado casuale diversa dalla precedente
        nuovo_dado = dado_corrente
        while nuovo_dado == dado_corrente:
            nuovo_dado = random.randint(0, 5)
        dado_corrente = nuovo_dado

        # Angolo rotazione casuale
        angolo_rotazione = random.randint(0, 359)
        # Inizia tremolio
        tremolio_frames = TREMOLIO_DURATA

    mano_chiusa_prec = mano_chiusa_flag

    screen.fill((0, 0, 0))

    if dado_visibile:
        # Tremolio: offset casuale limitato, alternato ogni frame
        offset_x, offset_y = 0, 0
        if tremolio_frames > 0:
            offset_x = random.randint(-TREMOLIO_INTENSITA, TREMOLIO_INTENSITA)
            offset_y = random.randint(-TREMOLIO_INTENSITA, TREMOLIO_INTENSITA)
            tremolio_frames -= 1

        dado_img = dice_images[dado_corrente]
        # Ruota immagine centrata
        dado_rotato = pygame.transform.rotate(dado_img, angolo_rotazione)
        rect = dado_rotato.get_rect(center=(dado_pos[0] + dado_img.get_width()//2 + offset_x,
                                            dado_pos[1] + dado_img.get_height()//2 + offset_y))

        screen.blit(dado_rotato, rect.topleft)

    pygame.display.flip()
    clock.tick(30)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

sound_shake.stop()
cap.release()
cv2.destroyAllWindows()
pygame.quit()

