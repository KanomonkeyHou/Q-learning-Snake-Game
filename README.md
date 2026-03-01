# 🐍 Smart Snake AI: Tabular Q-Learning Agent

**Course:** CDS524 - Reinforcement Learning Project
**Author:** Asb

## 📖 Project Overview
This project implements a self-learning agent that masters a grid-based Snake game using the **Tabular Q-Learning** algorithm. Developed with **Python** and **Pygame**, the environment challenges the agent to navigate a 7x7 grid, maximize its score by collecting different types of food, and survive against dynamic hazards (walls, its own body, and increasing poisons).

Unlike hard-coded algorithms, this AI starts with zero knowledge and learns the optimal pathfinding policy through a meticulously designed reward shaping system and epsilon-greedy exploration.

## ✨ Key Features
* **Custom Reinforcement Learning Environment:** Built entirely from scratch, tailored for discrete Q-learning.
* **Dynamic Difficulty Progression:** The number of deadly poisons `*` increases dynamically as the snake's length surpasses 10 or its survival steps exceed 50.
* **State Machine UI:** Features a clean, interactive UI with three distinct modes:
  * `Start Menu`: Displays game rules and controls.
  * `Train Mode`: Runs in the background (no rendering) to allow the AI to simulate thousands of episodes in seconds.
  * `Demo Mode`: Visualizes the learned policy with adjustable playback speed and a clear Game Over summary panel.
* **Forgiving Logic:** Solved the "Reward Shaping Failure" by ignoring invalid 180-degree reverse inputs, preventing the AI from trapping itself during early exploration.

## 🛠️ Tech Stack & Requirements
* **Python 3.8+**
* **Pygame** (for UI rendering and event handling)
* **NumPy** (for mathematical operations)

**Installation:**
```bash
pip install pygame numpy
