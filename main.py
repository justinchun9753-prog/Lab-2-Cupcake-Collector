import math
import pygame
import random
import asyncio

pygame.init()

WIDTH, HEIGHT = 600, 500
FPS = 60
GRAVITY = 0.5
JUMP_SPEED = -10
MOVE_SPEED = 5
Damping = 0.9
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 15
PLATFORM_GAP = 70
GUN_LENGTH = 34
GUN_WIDTH = 10
KNOCKBACK_STRENGTH = 14
MAX_AMMO = 10

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cupcake Collector")
clock = pygame.time.Clock()


def load_image(filename, size):
    image = pygame.image.load(filename).convert_alpha()
    return pygame.transform.scale(image, size)


player_image = load_image("player.png", (50, 50))
cupcake_image = load_image("cupcake.png", (30, 30))
gun_image = load_image("gun.png", (GUN_LENGTH, GUN_WIDTH))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        self.dy = 0
        self.vx = 0
        self.on_ground = True
        self.ammo = 2
        self.best_y = y
        self.aim_angle = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update_aim(self, mouse_pos, camera_offset):
        cx = self.x + self.width / 2
        cy = self.y - camera_offset + self.height / 2
        self.aim_angle = math.degrees(
            math.atan2(cy - mouse_pos[1], mouse_pos[0] - cx)
        )

    def shoot(self, mouse_pos, camera_offset):
        if self.ammo <= 0:
            return

        cx = self.x + self.width / 2
        cy = self.y - camera_offset + self.height / 2

        dx = mouse_pos[0] - cx
        dy = mouse_pos[1] - cy

        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        self.vx -= dx / dist * KNOCKBACK_STRENGTH
        self.dy -= dy / dist * KNOCKBACK_STRENGTH

        self.on_ground = False
        self.ammo -= 1

    def apply_physics(self, platforms):
        self.dy += GRAVITY
        self.y += self.dy
        self.x += self.vx

        self.vx *= Damping

        if abs(self.vx) < 0.05:
            self.vx = 0

        self.x = max(0, min(WIDTH - self.width, self.x))

        self.on_ground = False

        rect = self.rect

        if self.dy >= 0:
            for platform in platforms:
                if rect.colliderect(platform):
                    self.y = platform.top - self.height
                    self.dy = 0
                    self.on_ground = True
                    break

        if self.y + self.height >= HEIGHT:
            self.y = HEIGHT - self.height
            self.dy = 0
            self.on_ground = True

        if self.on_ground and self.y < self.best_y - 10:
            self.best_y = self.y
            self.ammo = min(
                self.ammo + random.randint(1, 3),
                MAX_AMMO
            )

    def draw(self, surface, camera_offset):
        surface.blit(
            player_image,
            (self.x, self.y - camera_offset)
        )

        cx = self.x + self.width / 2
        cy = self.y - camera_offset + self.height / 2

        rotated = pygame.transform.rotate(
            gun_image,
            self.aim_angle
        )

        rad = math.radians(self.aim_angle)

        center = (
            cx + math.cos(rad) * 20,
            cy - math.sin(rad) * 20
        )

        surface.blit(
            rotated,
            rotated.get_rect(center=center)
        )


def generate_platforms_up_to(platforms, target_y):
    highest_y = min(
        (p.y for p in platforms),
        default=HEIGHT
    )

    new_cupcakes = []

    y = highest_y - PLATFORM_GAP

    while y > target_y:
        x = random.randint(
            0,
            WIDTH - PLATFORM_WIDTH
        )

        platforms.append(
            pygame.Rect(
                x,
                y,
                PLATFORM_WIDTH,
                PLATFORM_HEIGHT
            )
        )

        if random.random() < 0.5:
            new_cupcakes.append(
                pygame.Rect(
                    x + PLATFORM_WIDTH // 2 - 15,
                    y - 40,
                    30,
                    30
                )
            )

        y -= PLATFORM_GAP

    return new_cupcakes


def reset_game():
    player = Player(
        WIDTH // 2 - 25,
        HEIGHT - 100
    )

    platforms = [
        pygame.Rect(
            0,
            HEIGHT - 20,
            WIDTH,
            20
        )
    ]

    cupcakes = generate_platforms_up_to(
        platforms,
        -HEIGHT * 3
    )

    return player, platforms, cupcakes, 0, 0


async def main():
    player, platforms, cupcakes, score, camera_offset = reset_game()

    game_over = False
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    player, platforms, cupcakes, score, camera_offset = reset_game()
                    game_over = False
                else:
                    player.shoot(
                        mouse_pos,
                        camera_offset
                    )

        if not game_over:
            player.apply_physics(platforms)

            player.update_aim(
                mouse_pos,
                camera_offset
            )

            if player.y - camera_offset < HEIGHT / 3:
                camera_offset = player.y - HEIGHT / 3

            cupcakes += generate_platforms_up_to(
                platforms,
                camera_offset - HEIGHT
            )

            cutoff = camera_offset + HEIGHT + 100

            platforms = [
                p for p in platforms
                if p.y < cutoff
            ]

            cupcakes = [
                c for c in cupcakes
                if c.y < cutoff
            ]

            for cupcake in cupcakes[:]:
                if player.rect.colliderect(cupcake):
                    cupcakes.remove(cupcake)
                    score += 1

            if player.y - camera_offset > HEIGHT:
                game_over = True

        pygame.display.set_caption(
            f"Cupcake Climber — Score: {score}"
        )

        screen.fill(
            (25, 30, 45)
        )

        for platform in platforms:
            pygame.draw.rect(
                screen,
                (100, 180, 100),
                (
                    platform.x,
                    platform.y - camera_offset,
                    platform.width,
                    platform.height
                )
            )

        for cupcake in cupcakes:
            screen.blit(
                cupcake_image,
                (
                    cupcake.x,
                    cupcake.y - camera_offset
                )
            )
        if not game_over:
            player.draw(
                screen,
                camera_offset
            )

            font = pygame.font.SysFont(
                None,
                28
            )
            screen.blit(
                font.render(
                    f"Shots: {player.ammo}",
                    True,
                    (255, 255, 255)
                ),
                (10, 10)
            )
            screen.blit(
                font.render(
                    "Reach 67 cupcakes to win",
                    True,
                    (255, 255, 255)
                ),
                (10, 40)
            )
        else:
            font = pygame.font.SysFont(
                None,
                48
            )
            text = font.render(
                "Game Over — click to restart",
                True,
                (255, 255, 255)
            )
            screen.blit(
                text,
                (
                    WIDTH // 2 - text.get_width() // 2,
                    HEIGHT // 2 - 20
                )
            )
        if not game_over and score >= 67:
            font = pygame.font.SysFont(
                None,
                48
            )
            text = font.render(
                "You Win!",
                True,
                (255, 255, 255)
            )
            screen.blit(
                text,
                (
                    WIDTH // 2 - text.get_width() // 2,
                    HEIGHT // 2 - 20
                )
            )
        pygame.display.flip()

        clock.tick(FPS)

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
