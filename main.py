# ============================================================================
# Nombre del estudiante: Jaime Antonio Alvarez Crisóstomo
# Materia: Lenguajes de Interfaz
# Título del proyecto: Animación mejorada de clima en pantalla OLED con Raspberry Pi Pico W
# Fecha: 15/05/2025
#
# Descripción:
# Este programa en Python utiliza una Raspberry Pi Pico W y una pantalla OLED controlada
# por el protocolo I2C para representar de forma animada cinco estados climáticos distintos:
# Soleado, Lluvioso, Nublado, Tormenta y Nevado. Cada fase climática incluye efectos
# visuales personalizados como rayos solares pulsantes, gotas de lluvia, nubes dinámicas,
# relámpagos intermitentes y copos de nieve que caen.
# ============================================================================

# Animación mejorada de clima en OLED con Raspberry Pi Pico W
from machine import Pin, I2C, Timer
import ssd1306
import math
import random
import time

# --- Configuración I2C y OLED ---
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# --- Variables de estado ---
WEATHER_PHASES = ["Soleado", "Lluvioso", "Nublado", "Tormenta", "Nevado"]
current_phase = 0
phase_time = 0

# --- Efectos visuales ---
sun_radius = 15
rain_drops = []
lightning_frame = 0
clouds = []
snow_flakes = []

# --- Utilidades ---
def fill_circle(x, y, r, color):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r*r - dy*dy))
        oled.hline(x - dx, y + dy, 2 * dx + 1, color)

def create_snow_flake():
    return {
        'x': random.randint(0, 127),
        'y': random.randint(-10, 0),
        'speed': random.uniform(0.5, 2),
        'size': random.randint(1, 3),
        'drift': random.uniform(-0.3, 0.3)
    }

# --- Fases del clima ---
def draw_sunny():
    angle = phase_time * 0.1
    pulse = 1 + 0.1 * math.sin(phase_time * 0.2)
    current_radius = int(sun_radius * pulse)
    fill_circle(64, 32, current_radius, 1)

    for i in range(12):
        ray_angle = angle + (i * math.pi / 6)
        length = current_radius + 10 + 3 * math.sin(phase_time * 0.5 + i)
        end_x = 64 + int(length * math.cos(ray_angle))
        end_y = 32 + int(length * math.sin(ray_angle))
        oled.line(64, 32, end_x, end_y, 1)

def draw_rainy():
    if phase_time % 2 == 0:
        rain_drops.append([random.randint(0, 127), -5, random.randint(3, 8)])

    for drop in rain_drops[:]:
        oled.vline(drop[0], drop[1], drop[2], 1)
        drop[1] += 7
        if drop[1] > 60:
            oled.hline(drop[0]-1, 63, 3, 1)
            rain_drops.remove(drop)

    oled.fill_rect(30, 10, 70, 15, 1)
    fill_circle(40, 20, 10, 1)
    fill_circle(70, 15, 12, 1)
    fill_circle(90, 20, 10, 1)

def draw_cloudy():
    if phase_time % 15 == 0:
        clouds.append([128, random.randint(5, 25), random.randint(30, 50), random.uniform(0.5, 1.5)])

    for cloud in clouds[:]:
        oled.fill_rect(int(cloud[0]), cloud[1], cloud[2], 12, 1)
        fill_circle(int(cloud[0]) + 10, cloud[1] + 6, 8, 1)
        fill_circle(int(cloud[0]) + 25, cloud[1] + 2, 10, 1)
        fill_circle(int(cloud[0]) + cloud[2] - 10, cloud[1] + 6, 7, 1)

        cloud[0] -= cloud[3]
        if cloud[0] < -cloud[2]:
            clouds.remove(cloud)

def draw_storm():
    global lightning_frame

    if lightning_frame > 0:
        oled.fill_rect(0, 0, 128, 64, 1)
        lightning_frame -= 1
    elif random.random() < 0.05:
        lightning_frame = 3

    oled.fill_rect(20, 15, 90, 20, 0)
    fill_circle(30, 25, 15, 0)
    fill_circle(60, 20, 18, 0)
    fill_circle(90, 25, 15, 0)
    fill_circle(45, 35, 12, 0)

    if phase_time % 2 == 0:
        rain_drops.append([random.randint(0, 127), -2, random.randint(5, 10)])

    for drop in rain_drops[:]:
        oled.vline(drop[0], drop[1], drop[2], 1)
        drop[1] += 12
        if drop[1] > 64:
            rain_drops.remove(drop)

def draw_snowy():
    oled.fill_rect(10, 10, 110, 20, 1)
    fill_circle(20, 20, 15, 1)
    fill_circle(50, 15, 18, 1)
    fill_circle(90, 20, 15, 1)
    fill_circle(110, 15, 12, 1)

    if random.random() < 0.4:
        snow_flakes.append(create_snow_flake())

    for flake in snow_flakes[:]:
        fill_circle(int(flake['x']), int(flake['y']), flake['size'], 1)
        flake['y'] += flake['speed']
        flake['x'] += flake['drift'] + math.sin(flake['y'] * 0.1) * 0.5

        if flake['y'] > 60 and random.random() < 0.1:
            oled.pixel(int(flake['x']), 63, 1)
        if flake['y'] > 64:
            snow_flakes.remove(flake)

# --- Render principal ---
def draw_weather_icon():
    oled.fill(0)
    phase_name = WEATHER_PHASES[current_phase]

    if phase_name == "Soleado":
        draw_sunny()
    elif phase_name == "Lluvioso":
        draw_rainy()
    elif phase_name == "Nublado":
        draw_cloudy()
    elif phase_name == "Tormenta":
        draw_storm()
    elif phase_name == "Nevado":
        draw_snowy()

    oled.text(phase_name, 6, 6, 0)
    oled.text(phase_name, 5, 5, 1)
    oled.show()

# --- Timer de actualización ---
def update_weather(timer):
    global current_phase, phase_time, rain_drops, clouds, snow_flakes, lightning_frame

    phase_time += 1
    draw_weather_icon()

    if phase_time >= 150:
        current_phase = (current_phase + 1) % len(WEATHER_PHASES)
        phase_time = 0
        rain_drops = []
        clouds = []
        snow_flakes = []
        lightning_frame = 0

# --- Iniciar animación ---
timer = Timer()
timer.init(period=33, mode=Timer.PERIODIC, callback=update_weather)
draw_weather_icon()