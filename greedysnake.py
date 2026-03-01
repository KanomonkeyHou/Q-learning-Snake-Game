import pygame
import random
import time
import numpy as np

# --- Configuration and Colors ---
WIDTH, HEIGHT = 720, 600  # Window size (grid area is smaller)
GRID_SIZE = 7
CELL_SIZE = 60
BORDER_COLOR = (20, 20, 100)  # Dark blue border
PATH_COLOR = (220, 220, 220)  # Light gray path
TEXT_COLOR = (0, 0, 0)  # Black text
PANEL_COLOR = (240, 240, 240)  # Light gray data panel

# Symbols for rendering
SYMBOL_HEAD = 'H'
SYMBOL_BODY = 'B'
SYMBOL_FOOD = 'F'
SYMBOL_SUPER = '$'
SYMBOL_POISON = '*'

# --- Pygame Setup ---
pygame.init()
pygame.display.set_caption("CDS524 - Advanced Q-Learning Snake AI")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("arial", 24)
info_font = pygame.font.SysFont("arial", 18)


# --- Define the Game Environment ---
class SnakeEnv:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.max_poisons = 3
        self.last_positions = []  # Store last visited cells to help prevent looping
        self.visited_path_len = 10  # History length
        self.reset()

    def reset(self):
        self.snake = [(self.size // 2, self.size // 2)]  # Head only, centered
        self.direction = 1  # 0:Up, 1:Right, 2:Down, 3:Left
        self.done = False
        self.score = 1
        self.steps = 0
        self.poison_count = 1
        self.last_positions = []
        self.death_reason = ""  # ADDED: Initialize death reason
        self._place_items()
        return self._get_state()

    def _place_items(self):
        # Place Food, Super Food, and Poisons
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if (r, c) not in self.snake]
        if len(empty_cells) < self.poison_count + 2:
            self.done = True  # Grid is too full
            return

        # Place regular food and super food
        food_items = random.sample(empty_cells, 2)
        self.food = food_items[0]
        self.super_food = food_items[1]

        # Determine current empty cells and place poisons
        empty_cells_no_food = [cell for cell in empty_cells if cell != self.food and cell != self.super_food]
        if len(empty_cells_no_food) < self.poison_count:
            # Not enough empty cells for all poisons, limit it.
            self.poisons = random.sample(empty_cells_no_food, len(empty_cells_no_food))
        else:
            self.poisons = random.sample(empty_cells_no_food, self.poison_count)

    def _get_state(self):
        # Improved state representation for decisive action
        head_r, head_c = self.snake[0]

        # Direction to nearest food (simple heuristic)
        # Use simple Manhattan distance to pick nearest.
        d_food = abs(self.food[0] - head_r) + abs(self.food[1] - head_c)
        d_super = abs(self.super_food[0] - head_r) + abs(self.super_food[1] - head_c)

        target = self.super_food if d_super <= d_food else self.food
        food_dir_r = 1 if target[0] > head_r else (-1 if target[0] < head_r else 0)
        food_dir_c = 1 if target[1] > head_c else (-1 if target[1] < head_c else 0)

        # Local danger detection (including border and poisons)
        dangers = []
        for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:  # Up, Right, Down, Left
            nr, nc = head_r + dr, head_c + dc
            if (nr < 0 or nr >= self.size or nc < 0 or nc >= self.size or
                    (nr, nc) in self.snake or (nr, nc) in self.poisons):
                dangers.append(1)
            else:
                dangers.append(0)

        # To help prevent looping, add last action to the state
        # State: (relative food dir r, c, dangers tuple, current direction)
        return (food_dir_r, food_dir_c, tuple(dangers), self.direction)

    def step(self, action):
        if self.done:
            return self._get_state(), 0, self.done

        self.steps += 1

        # --- 恢复“宽容模式”：如果它想180度掉头，我们忽略这个弱智操作，让它保持原向 ---
        if (action == 0 and self.direction != 2) or \
                (action == 1 and self.direction != 3) or \
                (action == 2 and self.direction != 0) or \
                (action == 3 and self.direction != 1):
            self.direction = action

        dr, dc = [(-1, 0), (0, 1), (1, 0), (0, -1)][self.direction]
        new_head = (self.snake[0][0] + dr, self.snake[0][1] + dc)

        # 具体的死因判定
        hit_wall = (new_head[0] < 0 or new_head[0] >= self.size or new_head[1] < 0 or new_head[1] >= self.size)
        bit_self = new_head in self.snake
        ate_poison = new_head in self.poisons

        if hit_wall or bit_self or ate_poison:
            self.done = True
            if hit_wall:
                self.death_reason = "Hit the Wall"
            elif bit_self:
                self.death_reason = "Bit Itself"
            elif ate_poison:
                self.death_reason = "Ate Poison"
            return self._get_state(), -200, self.done

        self.snake.insert(0, new_head)
        reward = -2  # 每走一步的小惩罚，逼它找最近的路

        # 奖励与生长
        growth = 0
        if new_head == self.food:
            reward = 30
            growth = 1
        elif new_head == self.super_food:
            reward = 60
            growth = 2

        if growth > 0:
            for _ in range(growth):
                self.snake.append(self.snake[-1])  # 增加身体
                self.score += 1

            # 难度递增机制
            if self.score > 10 and self.poison_count == 1:
                self.poison_count = 2
            if self.steps > 50 and self.poison_count < 3:
                self.poison_count = 3

            self._place_items()
        else:
            self.snake.pop()

        # 保留之前的防打转机制
        if new_head in self.last_positions:
            reward -= 10

        self.last_positions.append(new_head)
        if len(self.last_positions) > self.visited_path_len:
            self.last_positions.pop(0)

        return self._get_state(), reward, self.done

    def render(self):
        grid_width, grid_height = self.size * CELL_SIZE, self.size * CELL_SIZE
        # Draw Border
        pygame.draw.rect(screen, BORDER_COLOR, (0, 0, grid_width + 2 * CELL_SIZE, grid_height + 2 * CELL_SIZE))
        # Draw playable Path
        pygame.draw.rect(screen, PATH_COLOR, (CELL_SIZE, CELL_SIZE, grid_width, grid_height))

        # Grid World - Drawing items and text
        for r in range(self.size):
            for c in range(self.size):
                cell_rect = (CELL_SIZE + c * CELL_SIZE, CELL_SIZE + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                cell_content = '.'
                color = PATH_COLOR

                if (r, c) == self.snake[0]:
                    cell_content = SYMBOL_HEAD
                    color = (0, 255, 0)  # Green head
                elif (r, c) in self.snake[1:]:
                    cell_content = SYMBOL_BODY
                    color = (0, 0, 255)  # Blue body
                elif (r, c) == self.food:
                    cell_content = SYMBOL_FOOD
                    color = (255, 0, 0)  # Red food
                elif (r, c) == self.super_food:
                    cell_content = SYMBOL_SUPER
                    color = (255, 215, 0)  # Gold coin super food
                elif (r, c) in self.poisons:
                    cell_content = SYMBOL_POISON
                    color = (0, 0, 0)  # Black skull poison

                # Draw graphical block
                if cell_content != '.':
                    pygame.draw.rect(screen, color, cell_rect)

                # Draw text symbol
                if cell_content != '.':
                    text_surf = font.render(cell_content, True, TEXT_COLOR)
                    # Center the text
                    text_rect = text_surf.get_rect(
                        center=(cell_rect[0] + CELL_SIZE // 2, cell_rect[1] + CELL_SIZE // 2))
                    screen.blit(text_surf, text_rect)

        # Draw Right Data Panel
        panel_rect = (grid_width + 2 * CELL_SIZE, 0, WIDTH - (grid_width + 2 * CELL_SIZE), HEIGHT)
        pygame.draw.rect(screen, PANEL_COLOR, panel_rect)

        info_x = panel_rect[0] + 10
        screen.blit(info_font.render(f"Score (Length): {self.score}", True, TEXT_COLOR), (info_x, 20))
        screen.blit(info_font.render(f"Steps: {self.steps}", True, TEXT_COLOR), (info_x, 50))
        screen.blit(info_font.render(f"Poisons: {self.poison_count}", True, TEXT_COLOR), (info_x, 80))
        screen.blit(info_font.render(f"Epsilon: {agent.epsilon:.3f}", True, TEXT_COLOR), (info_x, 110))
        screen.blit(info_font.render(f"Learn Rate: {agent.lr:.3f}", True, TEXT_COLOR), (info_x, 140))
        screen.blit(info_font.render("--- Controls ---", True, TEXT_COLOR), (info_x, 200))
        screen.blit(info_font.render("1: Mode - Train", True, TEXT_COLOR), (info_x, 230))
        screen.blit(info_font.render("2: Mode - Demo", True, TEXT_COLOR), (info_x, 260))


# --- Q-Learning Core Algorithm ---
class QLearningAgent:
    def __init__(self, actions, learning_rate=0.1, discount_factor=0.9, epsilon=1.0, epsilon_decay=0.998):
        self.q_table = {}
        self.actions = actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay

    def get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        # Epsilon-greedy exploration strategy
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)

        q_values = [self.get_q(state, a) for a in self.actions]
        max_q = max(q_values)
        # Random choice among best actions
        best_actions = [a for a, q in zip(self.actions, q_values) if q == max_q]
        return random.choice(best_actions)

    def learn(self, state, action, reward, next_state):
        current_q = self.get_q(state, action)
        # Ensure that all possible next_actions are initialized. Q-table doesn't store them all yet.
        # This is equivalent to checking if next_state is new in get_q.
        max_next_q = max([self.get_q(next_state, a) for a in self.actions])

        # Q-Learning Update Formula (Temporal Difference)
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[(state, action)] = new_q


# --- Training and Demo Flow ---
env = SnakeEnv(size=GRID_SIZE)
agent = QLearningAgent(actions=[0, 1, 2, 3])

# --- Training, Demo and UI Flow ---
env = SnakeEnv(size=GRID_SIZE)
agent = QLearningAgent(actions=[0, 1, 2, 3])

# Define Game States
STATE_MENU = 0
STATE_TRAIN = 1
STATE_DEMO = 2

current_state = STATE_MENU  # Game starts at the menu
running = True
clock = pygame.time.Clock()

training_episodes = 2000
current_episode = 0
demo_fps = 3  # Default speed for demo


# --- Helper Function: Draw Start Menu ---
def draw_menu():
    screen.fill((255, 255, 255))
    # Title
    title_font = pygame.font.SysFont("arial", 48, bold=True)
    title_surf = title_font.render("Q-Learning Snake AI", True, (0, 0, 0))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 4))

    # Instructions
    inst_font = pygame.font.SysFont("arial", 24)
    instructions = [
        "Welcome to the AI Training Simulation.",
        "",
        "--- Controls ---",
        "[ENTER] : Start Training AI",
        "[ 2 ] : Skip to Demo Mode",
        "[UP/DOWN] : Adjust AI Speed in Demo Mode",
        "[ESC] : Quit Game",
        "",
        "--- Legend ---",
        "H: Head | B: Body | F: Food (+30) | $: Super Food (+60)",
        "*: Poison (Game Over) | Blue Border (Game Over)"
    ]

    start_y = HEIGHT // 2 - 50
    for i, line in enumerate(instructions):
        color = (50, 150, 50) if "[ENTER]" in line else (50, 50, 50)
        text_surf = inst_font.render(line, True, color)
        screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, start_y + i * 30))

    pygame.display.flip()


# --- Main Game Loop ---
print("Pygame Window is running. Waiting at Start Menu.")

while running:
    # 1. Global Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # Menu Controls
            if current_state == STATE_MENU:
                if event.key == pygame.K_RETURN:
                    current_state = STATE_TRAIN
                    agent.epsilon = 1.0  # Reset exploration
                    print("Started TRAIN Mode.")
                elif event.key == pygame.K_2:
                    current_state = STATE_DEMO
                    agent.epsilon = 0  # No exploration
                    env.done = True
                    print("Skipped to DEMO Mode.")

            # In-Game Controls
            elif current_state in [STATE_TRAIN, STATE_DEMO]:
                if event.key == pygame.K_1:
                    current_state = STATE_TRAIN
                    agent.epsilon = 0.1
                    print("Switched to TRAIN Mode.")
                elif event.key == pygame.K_2:
                    current_state = STATE_DEMO
                    agent.epsilon = 0
                    env.done = True
                    print("Switched to DEMO Mode.")
                # Speed control for Demo
                elif event.key == pygame.K_UP:
                    demo_fps += 1
                elif event.key == pygame.K_DOWN:
                    demo_fps = max(1, demo_fps - 1)

    # 2. State: Start Menu
    if current_state == STATE_MENU:
        draw_menu()
        clock.tick(15)  # Low framerate for menu

    # 3. State: Training Mode
    elif current_state == STATE_TRAIN:
        # Train in batches to keep UI responsive
        for _ in range(5):
            if current_episode >= training_episodes:
                current_state = STATE_DEMO
                agent.epsilon = 0

                # --- NEW FIX: Force reset state so we don't show the last training death ---
                state = env.reset()
                env.done = False
                demo_fps = 2  # 调低默认播放速度

                print("=== Training Complete. Switching to Demo Mode. ===")
                break

            state = env.reset()
            current_episode += 1

            while not env.done:
                action = agent.choose_action(state)
                next_state, reward, done = env.step(action)
                agent.learn(state, action, reward, next_state)
                state = next_state

        agent.epsilon = max(0.01, agent.epsilon * agent.epsilon_decay)

        # Render Training Loading Screen
        screen.fill((240, 240, 240))
        load_font = pygame.font.SysFont("arial", 32, bold=True)
        text_surf = load_font.render(f"TRAINING IN PROGRESS...", True, (200, 0, 0))
        ep_surf = font.render(f"Episode: {current_episode} / {training_episodes}", True, (0, 0, 0))
        eps_surf = font.render(f"Exploration Rate (Epsilon): {agent.epsilon:.3f}", True, (50, 50, 50))

        screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(ep_surf, (WIDTH // 2 - ep_surf.get_width() // 2, HEIGHT // 2 + 10))
        screen.blit(eps_surf, (WIDTH // 2 - eps_surf.get_width() // 2, HEIGHT // 2 + 50))
        pygame.display.flip()

    # 4. State: Demo Mode
    elif current_state == STATE_DEMO:
        if env.done:
            # --- NEW: Game Over Summary Screen ---
            # Draw a semi-transparent black overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            # Setup fonts for the summary
            over_font = pygame.font.SysFont("arial", 56, bold=True)
            reason_font = pygame.font.SysFont("arial", 32)

            # Render the text
            text_over = over_font.render("GAME OVER", True, (255, 50, 50))
            text_score = reason_font.render(f"Final Score (Length): {env.score}", True, (255, 255, 255))
            text_reason = reason_font.render(f"Cause of Death: {env.death_reason}", True, (255, 200, 0))

            # Position and draw the text on screen
            screen.blit(text_over, (WIDTH // 2 - text_over.get_width() // 2, HEIGHT // 2 - 80))
            screen.blit(text_score, (WIDTH // 2 - text_score.get_width() // 2, HEIGHT // 2))
            screen.blit(text_reason, (WIDTH // 2 - text_reason.get_width() // 2, HEIGHT // 2 + 50))

            pygame.display.flip()

            time.sleep(2)  # Pause for 2 seconds to let the viewer read the summary
            state = env.reset()  # Restart the game
            continue  # Skip the rest of this frame so we don't draw over the summary

        screen.fill((255, 255, 255))
        env.render()

        # Draw current speed indicator on UI
        speed_surf = info_font.render(f"Demo Speed: {demo_fps} FPS", True, (200, 0, 0))
        screen.blit(speed_surf, (WIDTH - 180, HEIGHT - 40))

        pygame.display.flip()

        action = agent.choose_action(state)
        state, reward, done = env.step(action)

        clock.tick(demo_fps)

pygame.quit()