# Sky Defender - Retro Airplane Shooter

A classic retro-style arcade shooter game built with vanilla HTML5, CSS, and JavaScript.

## Game Features

- **Retro pixel-art aesthetic** with vibrant colors and classic arcade feel
- **Horizontal airplane movement** with responsive controls
- **Shooting mechanics** - blast enemy planes out of the sky
- **4 enemy types** with unique behaviors:
  - BASIC (Red) - Standard enemy, straightforward movement
  - FAST (Orange) - Quick and agile
  - TANK (Magenta) - Heavily armored with more health
    - ZIGZAG (Cyan) - Unpredictable sine wave movement
- **Enemy AI** - Enemies shoot back at you!
- **Progressive difficulty** - Each level gets harder with faster spawns and tougher enemies
- **Lives system** with invulnerability frames
- **Particle explosion effects**
- **Complete menu system** - Start screen, pause, game over

## How to Play

1. Open `airplane-shooter.html` in any modern web browser
2. Click "START GAME"
3. Use controls:
   - **← → or A/D** - Move left/right
   - **SPACE** - Shoot
   - **P** - Pause/Resume

## Objective

- Destroy enemy planes to earn points
- Survive each level's duration to advance
- Dodge enemy planes and their bullets
- Start with 3 lives - don't let them hit zero!

## Scoring

- BASIC enemy: 100 points
- FAST enemy: 150 points
- ZIGZAG enemy: 200 points
- TANK enemy: 300 points

## Technical Details

- Single-file HTML implementation
- No external dependencies or build tools required
- HTML5 Canvas for rendering
- 60 FPS game loop with delta time
- Vanilla JavaScript (ES6 classes)
- Responsive design

## Files

- `airplane-shooter.html` - Main game file (complete standalone game)
- `tictactoe.html` - Bonus tic-tac-toe game

## Development

Built following retro game design principles with modern web technologies. The game uses:
- Canvas API for pixel-perfect rendering
- RequestAnimationFrame for smooth animations
- AABB collision detection
- Entity-component architecture

Enjoy the game! 🚀
