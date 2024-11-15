import pygame
import pandas as pd
import random
import math
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set screen dimensions and initialize Pygame
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Constant Speed Data-Driven Graphical Representation")
FPS = 60

# Parameters
MAX_DIAMETER = 200  # Diameter in pixels for the largest amount
MIN_DIAMETER = 10   # Diameter in pixels for the smallest amount
MAX_AMOUNT = 5000000  # Maximum amount corresponding to MAX_DIAMETER
MIN_AMOUNT = 1000     # Minimum amount corresponding to MIN_DIAMETER
DATE_RANGE = 7        # Number of days to consider for including a ball
SPEED_FACTORS = [5, 4.25, 3.5, 2.75, 2, 1.25, 0.5, 0.25]  # Fixed speed factors by date

# Initialize Pygame font for collision display
pygame.font.init()
font = pygame.font.SysFont(None, 24)

# Ball class to handle physics, color fading, and bouncing
class Ball:
    def __init__(self, x, y, diameter, speed_factor):
        self.x = x
        self.y = y
        self.diameter = diameter
        self.radius = diameter / 2
        self.color = [random.randint(50, 255) for _ in range(3)]
        self.color_speed = [random.randint(-1, 1) for _ in range(3)]
        
        # Set a fixed speed directly based on the date-driven speed factor
        self.speed = speed_factor
        angle = random.uniform(0, 2 * math.pi)
        self.velocity_x = self.speed * math.cos(angle)
        self.velocity_y = self.speed * math.sin(angle)

    def update(self):
        # Update position based on velocity
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Boundary collision - reflect direction without altering speed
        if self.x - self.radius < 0:
            self.velocity_x = abs(self.velocity_x)
            self.x = self.radius
        elif self.x + self.radius > WIDTH:
            self.velocity_x = -abs(self.velocity_x)
            self.x = WIDTH - self.radius

        if self.y - self.radius < 0:
            self.velocity_y = abs(self.velocity_y)
            self.y = self.radius
        elif self.y + self.radius > HEIGHT:
            self.velocity_y = -abs(self.velocity_y)
            self.y = HEIGHT - self.radius

        # Color fade
        for i in range(3):
            self.color[i] += self.color_speed[i]
            if self.color[i] < 50 or self.color[i] > 255:
                self.color_speed[i] = -self.color_speed[i]
            self.color[i] = max(50, min(self.color[i], 255))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))

# Function to handle collisions without altering the date-driven speed
def handle_collision(ball1, ball2):
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.hypot(dx, dy)
    if distance < ball1.radius + ball2.radius:
        # Reflect the directions of each ball post-collision while maintaining their speed
        angle = math.atan2(dy, dx)
        ball1.velocity_x = -ball1.speed * math.cos(angle)
        ball1.velocity_y = -ball1.speed * math.sin(angle)
        ball2.velocity_x = ball2.speed * math.cos(angle)
        ball2.velocity_y = ball2.speed * math.sin(angle)

# Function to load balls from CSV file based on date and amount
def load_balls_from_csv(filepath):
    today = datetime.today()
    balls = []
    try:
        # Read the CSV file and strip whitespace from headers
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()  # Strip any whitespace from column names
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Parse the date and calculate days old
                date = pd.to_datetime(row['Date']).date()
                days_old = (today.date() - date).days
                
                if days_old > DATE_RANGE:
                    continue
                
                # Clean up the Amount value by removing '$', ',', and spaces
                amount = float(str(row['Amount']).replace('$', '').replace(',', '').strip())
                
                # Calculate the ball's diameter based on the amount
                diameter = max(MIN_DIAMETER, min(MAX_DIAMETER, (amount - MIN_AMOUNT) / (MAX_AMOUNT - MIN_AMOUNT) * (MAX_DIAMETER - MIN_DIAMETER) + MIN_DIAMETER))
                
                # Assign the fixed speed factor based on days_old
                speed_factor = SPEED_FACTORS[min(days_old, DATE_RANGE)]
                
                # Initialize the ball with random position and date-driven speed factor
                x, y = random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)
                balls.append(Ball(x, y, diameter, speed_factor))
                
            except Exception as row_error:
                print(f"Error processing row: {row}, Error: {row_error}")
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
    
    return balls

# Watchdog event handler to reload balls on CSV change
class CSVChangeHandler(FileSystemEventHandler):
    def __init__(self, filepath, on_change_callback):
        self.filepath = filepath
        self.on_change_callback = on_change_callback

    def on_modified(self, event):
        if event.src_path == self.filepath:
            self.on_change_callback()

# Main function
def main():
    csv_filepath = r'C:\balls\balls_data.csv'  # Update this path to the actual CSV location
    balls = load_balls_from_csv(csv_filepath)

    # Modify the event handler to reload without duplicating balls
    def reload_balls():
        nonlocal balls
        balls = load_balls_from_csv(csv_filepath)

    # Set up the watchdog observer
    event_handler = CSVChangeHandler(csv_filepath, reload_balls)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(csv_filepath), recursive=False)
    observer.start()

    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill((0, 0, 0))  # Black background
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update each ball's position and handle ball-to-ball collisions
        for i, ball in enumerate(balls):
            ball.update()
            for j in range(i + 1, len(balls)):
                handle_collision(ball, balls[j])
            ball.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    observer.stop()
    observer.join()
    pygame.quit()

if __name__ == "__main__":
    main()
