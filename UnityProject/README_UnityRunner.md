# GestureBodyGame Unity Runner Module

This folder adds a Unity 3D URP implementation for a cyberpunk gesture runner with modular managers and reusable UI components.

## 1) Scene Structure

Create three scenes:

- `ModeSelectionScene`
- `GameplayScene`
- `SessionSummaryScene`

Add them to Build Settings in that order.

## 2) Script Layout

`Assets/Scripts/Core`
- `GameMode.cs`
- `GameState.cs`
- `ModeProfile.cs`
- `SessionData.cs`
- `SceneNames.cs`
- `PersistentGameContext.cs`

`Assets/Scripts/Managers`
- `GameManager.cs`
- `UIManager.cs`
- `ModeManager.cs`
- `SessionSummaryManager.cs`

`Assets/Scripts/Gameplay`
- `PlayerController.cs`
- `InfiniteRoadController.cs`
- `OrbSpawner.cs`
- `CollectibleOrb.cs`
- `ParallaxCityScroller.cs`
- `NeonLightPulse.cs`
- `AmbientParticleDrift.cs`

`Assets/Scripts/UI`
- `ModeCardView.cs`
- `NeonButtonAnimator.cs`
- `GlassPanelAnimator.cs`
- `SceneTransitionFader.cs`

`Assets/Scripts/Camera`
- `SmoothFollowCamera.cs`

Optional:

- Replace `SmoothFollowCamera` with a Cinemachine virtual camera if Cinemachine is installed.

## 3) Gameplay Scene Setup (3D)

Hierarchy suggestion:

- `GameplayRoot`
- `GameManager` (attach `GameManager.cs`)
- `RoadRoot` (attach `InfiniteRoadController.cs`)
- `CityParallaxRoot` (attach `ParallaxCityScroller.cs`)
- `OrbSpawner` (attach `OrbSpawner.cs`)
- `Player` (capsule + collider, attach `PlayerController.cs`)
- `Main Camera` (attach `SmoothFollowCamera.cs`)
- `Directional Light`
- `PostProcessVolume` (URP global volume: Bloom + Fog)
- `NeonLights` (point lights with `NeonLightPulse.cs`)
- `AmbientParticles` (Particle System + `AmbientParticleDrift.cs`)
- `GameplayCanvas` (Screen Space Overlay)

Environment targets requested:

- Infinite straight 3-lane road: set `laneWidth` in `PlayerController` and lane markers on road mesh.
- Night cyberpunk skyline: use emissive materials and `ParallaxCityScroller`.
- Neon street lights: place light poles with point lights + `NeonLightPulse`.
- Subtle fog + bloom: use URP Volume profile.
- Floating yellow/gold orbs: orb prefab with emissive material, trigger collider, `CollectibleOrb`.

## 4) Gameplay HUD Setup (Canvas)

Use a `Screen Space - Overlay` canvas and split into:

- `TopRightPanel` (glassmorphism panel)
- `BottomPanel` (mode/score/progress/instruction)

Attach `UIManager.cs` and wire:

- Combo text -> `Combo: 5`
- Calories text -> `Calories Burned: 12 kcal`
- Timer text -> `00:54`
- Intensity fill image
- Mode label -> example `Elderly Mode`
- Score label -> `Score: 9978`
- Progress fill image
- Instruction label -> `Keep shoulders, wrists, and hips visible.`

Style tips:

- Rounded corner sprites for panels.
- Dark transparent panel background (alpha ~0.35-0.5).
- Cyan/magenta accents on border images.
- Add `GlassPanelAnimator` on each panel for smooth fade and pulse.

## 5) Mode Selection Scene Setup

Hierarchy suggestion:

- `ModeSceneRoot`
- `ModeManager` (attach `ModeManager.cs`)
- `BackgroundCityBlur` (large quad with blurred cyberpunk texture)
- `CardsRoot`
- `ModeCard_Kids`
- `ModeCard_Elderly`
- `ModeCard_LegFree`
- `ModeCard_HandFree`
- `SelectionCanvas` (status text + footer instruction)

Card setup:

- Each card needs collider and renderer.
- Attach `ModeCardView.cs`.
- Configure `glowRenderers` and TMP labels.
- Add physics raycaster on camera and EventSystem in scene.

Footer text:

- `Press 1-4 or Click to choose. ENTER for calibration.`

Behavior:

- Hover: glow increases.
- Selected: card scales up.
- Idle: cards float subtly.

## 6) Session Summary Scene Setup

Hierarchy suggestion:

- `SummaryRoot`
- `SessionSummaryManager` (attach `SessionSummaryManager.cs`)
- `SummaryCanvas`
- `SummaryPanel` (centered glowing panel)
- `ScoreText`
- `BestScoreText`
- `CaloriesText`
- `TimeText`
- `IntensityMeterFill`
- `ReplayButton`
- `ChangeModeButton`
- `ViewStatsButton`

For each button:

- Add `Button` component.
- Add `NeonButtonAnimator`.
- Hook button events:
- Replay -> `SessionSummaryManager.ReplaySession()`
- Change Mode -> `SessionSummaryManager.ChangeMode()`
- View Stats -> `SessionSummaryManager.ViewStats()`

## 7) Reusable Prefabs Recommended

Create prefabs:

- `PF_GlassPanel` (Image + CanvasGroup + `GlassPanelAnimator`)
- `PF_ModeCard` (Mesh + collider + `ModeCardView`)
- `PF_NeonButton` (Button + `NeonButtonAnimator`)
- `PF_CollectibleOrb` (`CollectibleOrb` + trigger collider + emissive material)

## 8) URP / Visual Targets

- Renderer: URP Forward.
- Post FX: Bloom intensity around `0.6-1.1`.
- Fog: low density, cool color tint.
- Color palette: cyan + purple accents with mode-specific overrides.
- Keep motion smooth by using camera damping and animated UI values.
