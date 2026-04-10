# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sky Defender is a retro-style airplane shooter game built as a **single-file HTML application** with no external dependencies or build tools. The project follows a pattern established by `tictactoe.html` where complete games are self-contained in standalone HTML files.

## Running and Testing

Open `airplane-shooter.html` directly in any modern browser (Chrome, Firefox, Safari, Edge). No build step, no local server required. The game should run immediately.

Test all game states: Menu → Playing → Pause (P key) → Resume → Game Over → Restart cycle.

## Architecture

### Single-File Pattern

Both `airplane-shooter.html` and `tictactoe.html` follow this structure:
```html
<!DOCTYPE html>
<html>
  <head>
    <style>/* All CSS embedded here */</style>
  </head>
  <body>
    <!-- HTML structure -->
    <script>/* All JavaScript here */</script>
  </body>
</html>
```

**When adding features, maintain this single-file architecture.** Do not split into separate CSS/JS files or introduce build tools unless explicitly requested.

### JavaScript Class Hierarchy

The game uses ES6 classes organized in this order within the `<script>` tag:

1. **Constants** (STATES, COLORS, CONFIG, ENEMY_TYPES)
2. **Utility Functions** (checkCollision)
3. **InputManager** - Keyboard state tracking
4. **Particle** - Visual effects for explosions
5. **Bullet** - Projectiles (owner: 'player' or 'enemy')
6. **Player** - User-controlled airplane
7. **Enemy** - AI-controlled enemy planes with shooting
8. **Game** - Main controller orchestrating everything

### Game Class (Main Controller)

The `Game` class manages:
- **State machine**: MENU, PLAYING, PAUSED, GAME_OVER, LEVEL_TRANSITION
- **Game loop**: requestAnimationFrame with delta time (capped at 0.1s)
- **Entity arrays**: bullets, enemies, particles, stars
- **Collision detection**: Player bullets vs enemies, enemy bullets vs player, enemies vs player
- **Level progression**: Timer-based with difficulty scaling
- **Spawning**: Interval-based enemy spawning (varies by level)

State transitions are handled by showing/hiding DOM overlays (menu-overlay, pause-overlay, game-over-overlay, level-transition-overlay).

### Enemy System

Enemies have:
- **4 types**: BASIC (red), FAST (orange), TANK (magenta), ZIGZAG (cyan)
- **Movement patterns**: straight, diagonalLeft, diagonalRight, zigzag (sine wave)
- **Shooting AI**: Each enemy shoots bullets downward at intervals (1.5-2.5s based on type)
- **Health scaling**: Base health + floor((level-1)/2) for TANK types

Enemy spawning unlocks types progressively:
- Level 1: BASIC only
- Level 2: BASIC + FAST
- Level 3+: All types including TANK

### Retro Visual Style

**Critical**: Canvas rendering MUST maintain retro pixel-art aesthetic:

```javascript
ctx.imageSmoothingEnabled = false; // REQUIRED for pixel-perfect rendering
```

- Use blocky geometric shapes (triangles, rectangles) - no curves or smooth gradients
- Stick to the COLORS palette (bright, saturated retro colors)
- Player airplane: green triangle pointing up with side wings
- Enemy airplanes: colored triangles pointing down with side wings (wing size varies by type)
- Particles: small colored squares with fade-out alpha

Canvas is 480×640px for consistent retro resolution.

## Configuration and Tuning

Game behavior is controlled via constants at the top of the `<script>` section:

- **CONFIG**: Player speed, shoot cooldown, bullet speed/dimensions
- **ENEMY_TYPES**: Enemy stats (size, health, score value, color)
- **Difficulty scaling**: Hardcoded in `Game.nextLevel()` and `Game.spawnEnemy()`
  - Spawn interval decreases by 0.2s per level (min 0.5s)
  - Enemy speed increases by 20 px/s per level (max 200 px/s)
  - Level duration increases by 10s per level

When balancing difficulty, modify these values rather than changing core game logic.

## Git Workflow

**IMPORTANT**: All changes must be committed to Git and pushed to GitHub.

After making changes:
```bash
git add <modified-files>
git commit -m "Description of changes

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

The repository is at: https://github.com/robertooya/sky-defender

## Collision Detection

Uses AABB (Axis-Aligned Bounding Box) via `checkCollision(a, b)` utility function. All entities provide `getBounds()` method returning `{x, y, width, height}`.

Three collision pairs checked each frame:
1. Player bullets vs enemies → damage enemy, award points
2. Enemy bullets vs player → damage player (if not invulnerable)
3. Enemies vs player → damage player, destroy enemy

Player has 2s invulnerability after taking damage (flashing visual effect).

## UI System

**Dual rendering approach**:
- **Overlays**: Menu, pause, game over, level transition → HTML/CSS overlays with `.hidden` class toggle
- **HUD**: Score, level, lives → Canvas-rendered at top of screen during gameplay

This hybrid allows retro canvas gameplay with modern HTML UI for menus/modals.
