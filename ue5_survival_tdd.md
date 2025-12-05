# PROJECT PANDORA - Technical Design Document
## Unreal Engine 5 Implementation Guide

---

## 1. PROJECT SETUP

### 1.1 Engine Configuration
- **Engine Version**: Unreal Engine 5.3+ (Lumen, Nanite support)
- **Project Template**: Third Person
- **Target Platforms**: PC (Primary), Console (Secondary)
- **Performance Target**: 60 FPS on High settings (1080p)

### 1.2 Project Structure
```
Content/
├── Core/
│   ├── GameModes/
│   ├── PlayerController/
│   ├── SaveSystem/
│   └── GameInstance/
├── Characters/
│   ├── Player/
│   ├── Enemies/
│   └── NPCs/
├── Weapons/
│   ├── Firearms/
│   ├── Melee/
│   └── Throwables/
├── Systems/
│   ├── SurvivalSystem/
│   ├── CraftingSystem/
│   ├── MutationSystem/
│   └── MissionSystem/
├── Levels/
│   ├── MainMenu/
│   ├── Cabin_Hub/
│   └── Islands/
├── UI/
│   ├── HUD/
│   ├── Menus/
│   └── Widgets/
├── Audio/
├── VFX/
└── Materials/
```

### 1.3 Core Settings
- **World Settings**: Enable World Composition for large islands
- **Collision Channels**: 
  - Player
  - Enemy
  - Environment
  - Projectile
  - Interactable
- **Physics**: Enable Chaos Physics for destruction

---

## 2. CHARACTER SYSTEM

### 2.1 Player Character Blueprint (BP_PlayerCharacter)

**Parent Class**: ACharacter

**Components**:
```cpp
// Key Components
- CapsuleComponent (Collision)
- SkeletalMeshComponent (Character Mesh)
- CameraComponent (Third Person)
- SpringArmComponent (Camera Boom)
- InventoryComponent (Custom)
- SurvivalStatsComponent (Custom)
- WeaponManagerComponent (Custom)
```

**Core Stats** (Float Variables):
```cpp
// Survival Stats
- Health (0-100)
- Stamina (0-100)
- Hunger (0-100)
- Thirst (0-100)
- Body Temperature (92-104°F)

// Combat Stats
- Aim Stability (0-1)
- Movement Speed Modifier (0.5-1.5)
```

**Movement Implementation**:
```
Blueprint: Event Graph

[Event Tick]
  ├─> [Update Stamina Drain] (if sprinting)
  ├─> [Apply Hunger/Thirst Effects] (speed reduction if low)
  └─> [Update Camera Shake] (based on stamina)

[Input Action: Sprint]
  ├─> [Check Stamina > 10]
  │     ├─ TRUE: Set Max Walk Speed = 600
  │     └─ FALSE: Set Max Walk Speed = 300
  └─> [Consume Stamina] (5 per second)

[Input Action: Crouch]
  ├─> [Toggle Crouch]
  └─> [Set Max Walk Speed = 150]
```

### 2.2 Player Animation Blueprint (ABP_Player)

**State Machine: Locomotion**
```
Idle/Walk/Run State Machine:
- Idle (Speed = 0)
- Walk (Speed 0-300)
- Run (Speed 300-600)
- Sprint (Speed > 600)

Aim Offset:
- Pitch (-90 to 90)
- Yaw (-90 to 90)

Layered Animations:
- Upper Body (Weapon animations)
- Lower Body (Locomotion)
```

**Animation Montages Needed**:
- Reload (per weapon type)
- Weapon Swap
- Melee Attack
- Take Damage
- Death
- Interaction (pickup, open door, etc.)

### 2.3 AI Enemy Base (BP_EnemyBase)

**Parent Class**: ACharacter with AI Controller

**AI Components**:
```cpp
- AIPerceptionComponent (Sight, Hearing, Damage)
- BehaviorTreeComponent
- BlackboardComponent
- NavigationComponent
```

**Enemy Stats** (varies by mutation stage):
```cpp
// Stage 1 Mutations
- Health: 100-200
- Damage: 15-25
- Speed: 400-500
- Detection Range: 2000 units
- Attack Range: 200 units

// Stage 2 Mutations
- Health: 300-500
- Damage: 35-50
- Speed: 450-600
- Detection Range: 3000 units
- Attack Range: 300 units
- Special Abilities: Enabled

// Stage 3 Mutations
- Health: 800-1500
- Damage: 60-100
- Speed: 500-700
- Detection Range: 4000 units
- Attack Range: 400 units
- Special Abilities: Advanced
```

---

## 3. WEAPON SYSTEM

### 3.1 Weapon Base Class (BP_WeaponBase)

**Parent Class**: AActor

**Components**:
```cpp
- SkeletalMeshComponent (Weapon Mesh)
- AmmoComponent (Custom)
- RecoilComponent (Custom)
```

**Weapon Properties** (per weapon):
```cpp
UPROPERTY(EditDefaultsOnly, Category = "Weapon Stats")
- WeaponName: FText
- WeaponType: EWeaponType (Enum: Pistol, Rifle, Shotgun, Sniper)
- Damage: float
- FireRate: float (rounds per minute)
- MagazineSize: int32
- MaxAmmo: int32
- ReloadTime: float
- Range: float
- RecoilPattern: UCurveFloat
- bIsAutomatic: bool
- bIsSuppressed: bool
```

**Firing Implementation**:
```
Blueprint: Fire Weapon Function

[Input: Fire]
  ├─> [Check Current Ammo > 0]
  │     ├─ TRUE: Continue
  │     └─ FALSE: Play Empty Click Sound, Return
  ├─> [Line Trace from Camera]
  │     ├─> Start: Camera Location
  │     ├─> End: Camera Forward * Range
  │     └─> Channel: ECC_Weapon
  ├─> [Check Hit Result]
  │     ├─ Hit Enemy:
  │     │   ├─> Apply Damage (UGameplayStatics::ApplyDamage)
  │     │   ├─> Spawn Blood VFX
  │     │   └─> Play Hit Sound
  │     └─ Hit Environment:
  │         ├─> Spawn Impact VFX (based on material)
  │         └─> Play Impact Sound
  ├─> [Apply Recoil]
  │     ├─> Add Controller Pitch Input (Vertical Recoil)
  │     └─> Add Controller Yaw Input (Horizontal Recoil)
  ├─> [Play Fire Effects]
  │     ├─> Spawn Muzzle Flash
  │     ├─> Play Fire Sound
  │     └─> Play Camera Shake
  ├─> [Subtract Ammo] (CurrentAmmo--)
  └─> [Check Automatic Fire]
        └─ If TRUE: Set Timer for next shot (60/FireRate)
```

### 3.2 Weapon Manager Component (C++ or Advanced Blueprint)

**Manages**:
- Current equipped weapon
- Weapon inventory (array of weapons)
- Weapon switching
- Ammo pooling

**Implementation**:
```cpp
class UWeaponManagerComponent : public UActorComponent
{
    UPROPERTY()
    TArray<ABP_WeaponBase*> WeaponInventory;
    
    UPROPERTY()
    ABP_WeaponBase* CurrentWeapon;
    
    UPROPERTY()
    int32 CurrentWeaponIndex;
    
    UFUNCTION()
    void EquipWeapon(int32 Index);
    
    UFUNCTION()
    void AddWeapon(ABP_WeaponBase* NewWeapon);
    
    UFUNCTION()
    void NextWeapon();
    
    UFUNCTION()
    void PreviousWeapon();
};
```

---

## 4. SURVIVAL SYSTEM

### 4.1 Survival Stats Component (BP_SurvivalStatsComponent)

**Parent Class**: UActorComponent

**Tick Function** (Every 1 second using Timer):
```
[Timer: Update Survival Stats - 1.0s Interval]
  ├─> [Decrease Hunger] (-0.5 per second)
  ├─> [Decrease Thirst] (-0.7 per second)
  ├─> [Check Temperature]
  │     ├─ If Cold: Decrease Health (-2/sec if < 95°F)
  │     └─ If Hot: Increase Thirst drain (+0.3/sec if > 100°F)
  ├─> [Apply Hunger Effects]
  │     ├─ If < 30: Reduce Max Stamina by 30%
  │     └─ If < 10: Apply Health damage (-1/sec)
  ├─> [Apply Thirst Effects]
  │     ├─ If < 30: Reduce Stamina Regen by 50%
  │     └─ If < 10: Apply Health damage (-2/sec)
  └─> [Update HUD] (Call UI update event)
```

### 4.2 Crafting System (BP_CraftingSystem)

**Data Table Structure** (DT_CraftingRecipes):
```cpp
struct FCraftingRecipe : public FTableRowBase
{
    UPROPERTY()
    FName RecipeID;
    
    UPROPERTY()
    FText ItemName;
    
    UPROPERTY()
    TArray<FItemRequirement> RequiredItems;
    // Example: [Wood x5, Metal x2]
    
    UPROPERTY()
    TSubclassOf<AActor> ResultItem;
    
    UPROPERTY()
    float CraftingTime;
    
    UPROPERTY()
    bool bRequiresWorkbench;
};
```

**Crafting Implementation**:
```
Blueprint: Craft Item Function

[Input: Craft Recipe]
  ├─> [Check Required Items in Inventory]
  │     └─ If Missing: Show "Insufficient Materials", Return
  ├─> [Check Workbench Requirement]
  │     └─ If Required but not near: Show "Requires Workbench", Return
  ├─> [Start Crafting Timer]
  │     ├─> Show Crafting Progress Bar
  │     ├─> Disable Movement during craft
  │     └─> After Time: Complete Craft
  ├─> [Remove Materials from Inventory]
  ├─> [Spawn Result Item]
  │     └─> Add to Inventory
  └─> [Play Crafting Complete Effect]
```

---

## 5. ENEMY AI SYSTEM

### 5.1 Behavior Tree Structure (BT_EnemyBase)

**Blackboard Keys**:
```
- TargetActor (Object - Player reference)
- LastKnownLocation (Vector)
- PatrolPoint (Vector)
- bIsInCombat (Bool)
- bCanSeeTarget (Bool)
- DistanceToTarget (Float)
- CurrentState (Enum: Idle, Patrol, Investigate, Chase, Attack)
```

**Behavior Tree Layout**:
```
ROOT
└─ Selector: Combat or Patrol
    ├─ Sequence: Combat Behavior [If bIsInCombat = TRUE]
    │   ├─ Selector: Attack or Chase
    │   │   ├─ Sequence: Attack [If DistanceToTarget < AttackRange]
    │   │   │   ├─ Task: Face Target
    │   │   │   ├─ Task: Play Attack Animation
    │   │   │   └─ Task: Apply Damage to Target
    │   │   └─ Task: Move To Target [If DistanceToTarget > AttackRange]
    │   └─ Decorator: Cooldown (1.0s between attacks)
    └─ Sequence: Patrol Behavior [If bIsInCombat = FALSE]
        ├─ Task: Get Random Patrol Point
        ├─ Task: Move To Patrol Point
        └─ Task: Wait (3-5 seconds)
```

### 5.2 AI Perception Setup

**In BP_EnemyBase**:
```
[AIPerceptionComponent]
├─ Sight Config:
│   ├─ Detection Range: 2000-4000 (based on mutation stage)
│   ├─ Lose Sight Range: 2500-5000
│   ├─ Peripheral Vision Angle: 90-180 degrees
│   └─ Auto Success Range: 500 (close range auto-detect)
├─ Hearing Config:
│   ├─ Detection Range: 3000
│   └─ Detect Gunshots, Footsteps, Explosions
└─ Damage Config:
    └─ Always detect when damaged

[Event: On Target Perception Updated]
├─> If Sensed Successfully:
│   ├─> Set bIsInCombat = TRUE
│   ├─> Set TargetActor = Player
│   └─> Alert Nearby Allies (within 1500 units)
└─> If Lost Sight:
    ├─> Set LastKnownLocation
    ├─> Investigate for 10 seconds
    └─> If not found: Return to Patrol
```

### 5.3 Mutation Stages Implementation

**Create Child Blueprints**:
- BP_Enemy_Stage1 (Inherits from BP_EnemyBase)
- BP_Enemy_Stage2 (Inherits from BP_EnemyBase)
- BP_Enemy_Stage3 (Inherits from BP_EnemyBase)

**Stage-Specific Modifications**:

**BP_Enemy_Stage2**:
```
[Begin Play]
├─> Set Health = 400
├─> Set Speed = 550
├─> Enable Special Ability:
│   └─ Leap Attack (every 15 seconds)
│       ├─> Launch Character toward player
│       ├─> Play leap animation
│       └─> Deal heavy damage on land
└─> Update Material (add glowing crystals)
```

**BP_Enemy_Stage3**:
```
[Begin Play]
├─> Set Health = 1000
├─> Set Speed = 650
├─> Enable Advanced Abilities:
│   ├─ Regeneration (5 HP/second)
│   ├─ Teleport (short distance, 20s cooldown)
│   └─ Area Slam Attack
└─> Add Armor System (reduce damage by 30%)

[Event: On Take Damage]
├─> If Health < 30%:
│   ├─> Enter Berserk Mode
│   ├─> Increase Speed by 50%
│   └─> Increase Attack Rate by 100%
```

---

## 6. MISSION & LEVEL SYSTEM

### 6.1 Mission Structure (BP_MissionManager)

**Mission Data Structure** (DT_Missions):
```cpp
struct FMissionData : public FTableRowBase
{
    UPROPERTY()
    FName MissionID;
    
    UPROPERTY()
    FText MissionName;
    
    UPROPERTY()
    FText Description;
    
    UPROPERTY()
    FName IslandLevelName;
    
    UPROPERTY()
    TArray<FMissionObjective> Objectives;
    // Example: Kill 30 Enemies, Find 3 Documents, etc.
    
    UPROPERTY()
    int32 RewardMoney;
    
    UPROPERTY()
    TArray<TSubclassOf<AActor>> RewardItems;
    
    UPROPERTY()
    FName NextMissionID;
};
```

**Mission Objective System**:
```cpp
enum EMissionObjectiveType
{
    KillEnemies,
    FindDocuments,
    ReachLocation,
    Survive,
    Escort,
    Destroy
};

struct FMissionObjective
{
    EMissionObjectiveType Type;
    int32 RequiredCount;
    int32 CurrentProgress;
    FString Description;
    bool bIsCompleted;
};
```

**Mission Flow**:
```
[Game Instance: Mission Manager]

[Start Mission]
├─> Load Island Level (via Level Streaming)
├─> Spawn Player at Insertion Point
├─> Initialize Objectives
├─> Spawn Mission Actors (enemies, items, etc.)
└─> Start Mission Timer (if applicable)

[Update Objective Progress]
├─> Listen for Events:
│   ├─ Enemy Killed → Update Kill Count
│   ├─ Item Picked Up → Update Collection Count
│   └─ Location Reached → Mark Location Complete
├─> Check Objective Completion
│   └─ If All Complete:
│       ├─> Trigger Extraction Sequence
│       └─> Enable Extraction Zone

[Complete Mission]
├─> Call Extraction Helicopter (Hawk)
├─> Cutscene: Echo Team Arrival
├─> Award Money & Items
├─> Save Progress
├─> Return to Hub (Cabin)
└─> Unlock Next Mission
```

### 6.2 Level Streaming System

**Persistent Level**: MainWorld
- Contains: Sky, Ocean, Base Systems

**Streaming Levels**:
```
Levels/Cabin_Hub (Always Loaded in Hub)
Levels/Island_Sierra_01
Levels/Island_Sierra_02
...
Levels/Island_Sierra_12

[Level Blueprint: Load Island]
├─> Unload Current Island
├─> Load Target Island (Async)
├─> Wait for Load Complete
├─> Teleport Player to Insertion Point
└─> Initialize Mission
```

### 6.3 Save System (BP_SaveGameSystem)

**Save Game Object** (C++):
```cpp
class USaveGame_Pandora : public USaveGame
{
    UPROPERTY()
    FString PlayerName;
    
    UPROPERTY()
    int32 CurrentMissionIndex;
    
    UPROPERTY()
    TArray<FName> CompletedMissions;
    
    UPROPERTY()
    int32 PlayerMoney;
    
    UPROPERTY()
    TArray<FInventoryItem> Inventory;
    
    UPROPERTY()
    TArray<FWeaponData> UnlockedWeapons;
    
    UPROPERTY()
    FPlayerStats PlayerStats;
    
    UPROPERTY()
    TArray<FName> FoundDocuments;
};
```

**Save/Load Implementation**:
```
[Save Game Function]
├─> Create Save Game Object
├─> Populate with Current Data:
│   ├─ Mission Progress
│   ├─ Player Stats
│   ├─ Inventory
│   └─ Unlocks
├─> UGameplayStatics::SaveGameToSlot()
└─> Show "Game Saved" notification

[Load Game Function]
├─> UGameplayStatics::LoadGameFromSlot()
├─> Check if Save Exists
│   ├─ TRUE: Load Data, Apply to Game
│   └─ FALSE: Start New Game
└─> Restore Player State
```

---

## 7. UI SYSTEM

### 7.1 HUD Widget (WBP_GameHUD)

**Widget Components**:
```
Canvas Panel (Root)
├─ Health Bar (Progress Bar)
│   └─ Text: Health Value
├─ Stamina Bar (Progress Bar)
│   └─ Text: Stamina Value
├─ Hunger/Thirst Icons (Images)
│   └─ Values as Text Overlays
├─ Weapon Info Panel (Horizontal Box)
│   ├─ Weapon Name (Text)
│   ├─ Ammo Counter (Text): "24 / 120"
│   └─ Weapon Icon (Image)
├─ Crosshair (Image - Center Screen)
├─ Compass (Widget at top)
├─ Objective Panel (Vertical Box - Top Right)
│   └─ Active Objectives List
└─ Minimap (Canvas Panel - Bottom Right)
```

**HUD Update Logic**:
```
[Event: Update HUD] (called from Player Stats Component)
├─> Get Player Reference
├─> Bind Health:
│   └─ ProgressBar->SetPercent(Health / MaxHealth)
├─> Bind Stamina:
│   └─> ProgressBar->SetPercent(Stamina / MaxStamina)
├─> Bind Ammo:
│   └─> Text->SetText(CurrentAmmo + " / " + TotalAmmo)
├─> Bind Objectives:
│   └─> Update Objective Text with Progress
└─> Update Compass Direction
```

### 7.2 Interaction System

**Interactable Base** (BP_InteractableBase):
```cpp
Components:
- StaticMeshComponent
- WidgetComponent (World Space UI)

Variables:
- InteractionText: FText ("Press E to Pick Up")
- bCanInteract: bool
- InteractionDistance: float (200 units)

Functions:
- OnInteract() - Override in child blueprints
```

**Player Interaction Check**:
```
[Event Tick: Check Interaction]
├─> Line Trace from Camera (200 units)
├─> Check if Hit Actor Implements Interactable Interface
│   ├─ TRUE:
│   │   ├─> Show Interaction Widget
│   │   └─> Store Current Interactable
│   └─ FALSE:
│       └─> Hide Interaction Widget
└─> [Input: Interact Key (E)]
    └─> Call OnInteract() on Current Interactable
```

---

## 8. CUTSCENE SYSTEM

### 8.1 Sequencer Setup

**For Each Cutscene**:
```
Create Level Sequence Asset:
Content/Cinematics/LS_Opening_Cutscene

Tracks:
├─ Camera Cut Track (switches between cameras)
├─ Cine Camera Actors (multiple for different angles)
├─ Character Animation Tracks
├─ Audio Tracks (Dialogue, Music, SFX)
├─ Fade Track (fade in/out)
└─ Event Track (trigger gameplay events)
```

**Example: Opening Cutscene (LS_Opening)**:
```
Timeline:
0:00 - Fade In from Black
0:02 - Camera: Car driving through forest (Cinematic Camera 1)
0:08 - Camera: Interior car shot (Cinematic Camera 2)
0:12 - Camera: Car arrives at cabin (Cinematic Camera 3)
0:15 - Character exits car, walks to cabin
0:20 - Interior: Hangs medals on wall
0:25 - Camera pan to trophy wall
0:30 - Character takes shotgun, loads it
0:35 - Character lies in bed
0:40 - Fade to Black
0:42 - Event Track: End Cutscene, Start Gameplay
```

**Playing Cutscenes**:
```
[Level Blueprint: Play Opening Cutscene]
├─> Disable Player Input
├─> Create Level Sequence Player
├─> Play Sequence: LS_Opening
├─> Bind Event: On Sequence Finished
│   ├─> Enable Player Input
│   ├─> Start Gameplay
│   └─> Destroy Sequence Player
```

### 8.2 In-Mission Cinematics

**Trigger Volumes for Story Beats**:
```
[BP_CinematicTrigger]
├─ Box Collision Component
└─ [Event: On Actor Begin Overlap]
    ├─> Check if Overlapping Actor is Player
    ├─> If TRUE:
    │   ├─> Disable Player Input
    │   ├─> Play Specific Level Sequence
    │   ├─> On Finished: Re-enable Input
    │   └─> Destroy Trigger (one-time use)
```

---

## 9. AUDIO SYSTEM

### 9.1 Sound Design Structure

**Audio Categories**:
```
Content/Audio/
├─ Music/
│   ├─ MainTheme
│   ├─ CombatMusic
│   ├─ AmbientMusic
│   └─ CutsceneMusic
├─ SFX/
│   ├─ Weapons/
│   ├─ Creatures/
│   ├─ Environment/
│   └─ UI/
├─ Dialogue/
│   ├─ Player/
│   ├─ Morrison/
│   ├─ Hawk/
│   └─ Echo_Team/
└─ Ambience/
    ├─ Forest/
    ├─ Island/
    └─ Facility/
```

### 9.2 Adaptive Music System

**Music Manager** (BP_MusicManager):
```
[State-Based Music Crossfading]

States:
- Exploration (Ambient music)
- Combat (Intense music)
- Stealth (Tension music)
- SafeZone (Calm music)

[Event: Music State Changed]
├─> Fade Out Current Music (2 seconds)
├─> Wait for Fade Complete
├─> Fade In New Music (2 seconds)
└─> Set Current State

[Combat Detection]
├─> Listen for: Enemy Alerted Event
├─> Switch to Combat Music
└─> Timer: If no enemies for 30s → Return to Exploration

```

### 9.3 3D Sound Implementation

**Creature Audio Component**:
```
[Audio Component on BP_EnemyBase]
├─ Attenuation Settings:
│   ├─ Inner Radius: 500 units
│   ├─ Falloff Distance: 5000 units
│   └─ Spatialization Algorithm: HRTF
├─ Sounds:
│   ├─ Idle Breathing (Looping)
│   ├─ Footsteps (based on movement)
│   ├─ Attack Roars
│   └─ Death Sounds
└─ Random Variations (avoid repetition)
```

---

## 10. VISUAL EFFECTS (VFX)

### 10.1 Niagara Systems

**Key VFX Needed**:

**Blood Effects** (NS_BloodSpray):
```
Emitter Setup:
├─ Spawn Rate: 100 particles
├─ Lifetime: 0.5-1.5 seconds
├─ Velocity: Burst outward from hit location
├─ Gravity: Enabled (-980)
├─ Collision: Enabled (stick to surfaces)
└─ Material: Blood droplet texture
```

**Muzzle Flash** (NS_MuzzleFlash):
```
Emitter Setup:
├─ Spawn Burst: 20 particles (instant)
├─ Lifetime: 0.1 seconds
├─ Size: 10-30 units
├─ Light Module: Orange flash (intensity 5000)
└─ Material: Flash sprite
```

**Crystal Glow** (NS_CrystalAura):
```
Emitter Setup:
├─ Spawn Rate: 50 particles/sec
├─ Lifetime: 2-4 seconds
├─ Velocity: Slow upward drift
├─ Size: 5-15 units
├─ Color: Cyan/Green gradient
└─ Material: Glowing particle
```

**Mutation Transformation** (NS_MutationEffect):
```
Multi-Emitter System:
├─ Emitter 1: Flesh Tearing
│   └─ Rapid particles burst, blood-like
├─ Emitter 2: Crystal Growth
│   └─ Crystalline structures emerging
└─ Emitter 3: Energy Discharge
    └─ Lightning-like arcs
```

### 10.2 Post-Process Effects

**Camera Effects for Damage**:
```
[Material: M_DamagePP]
├─ Vignette Effect (darkens edges when low health)
├─ Desaturation (when near death)
└─ Blood Splatter Overlay (when hit)

[Player Character: Event Take Damage]
├─> Spawn Post Process Volume (temporary)
├─> Set Material: M_DamagePP
├─> Intensity based on damage amount
├─> Fade out over 2 seconds
└─> Destroy volume
```

**Mutation Vision** (When near high crystal concentration):
```
[Post Process: Mutation Influence]
├─ Chromatic Aberration: Increased
├─ Lens Distortion: Warping
├─ Color Grading: Tint toward cyan/green
└─ Vignette: Pulsing effect
```

---

## 11. OPTIMIZATION & PERFORMANCE

### 11.1 LOD (Level of Detail) Settings

**Character LODs**:
```
LOD 0 (0-1000 units): Full detail
LOD 1 (1000-2500 units): 50% triangles
LOD 2 (2500-5000 units): 25% triangles
LOD 3 (5000+ units): Impostor or cull
```

**Foliage Settings**:
```
[Foliage Type Settings]
├─ Cull Distance: 5000-10000 (based on size)
├─ LOD0: 0-1500
├─ LOD1: 1500-3500
├─ LOD2: 3500-5000
└─ Enable Grass Culling (outside camera frustum)
```

### 11.2 Occlusion Culling

**Enable Precomputed Visibility**:
```
World Settings:
└─ Precomputed Visibility: TRUE
    └─ Place PrecomputedVisibilityVolumes in dense areas
```

**Distance Culling**:
```
[Actor Settings]
├─ Max Draw Distance: Set per actor type
│   ├─ Small Props: 3000
│   ├─ Medium Props: 5000
│   └─ Large Structures: 10000
└─ Enable Distance Culling
```

### 11.3 AI Optimization

**AI Perception Optimization**:
```
[AIPerceptionSystemSettings]
├─ Update Interval: 0.5 seconds (not every frame)
├─ Max Active Sounds: 20
└─ Only update perception for enemies near player
```

**Behavior Tree Optimization**:
```
[Best Practices]
├─ Use Decorators for Conditions (cheaper than tasks)
├─ Cache expensive operations in Blackboard
├─ Limit simultaneous active AI to 15-20
└─ Disable AI for enemies far from player (>10000 units)
```

### 11.4 Texture Streaming

**Texture Settings**:
```
Project Settings > Engine > Rendering:
├─ Texture Streaming: Enabled
├─ Pool Size: 2000 MB
└─ Use Mip Maps: TRUE

[Per Texture]
├─ Never Stream: FALSE (unless UI/HUD)
├─ Compression: BC7 for high quality, BC1 for performance
└─ Max Texture Size: 2048x2048 (4096 for terrain)
```

---

## 12. NETWORK CONSIDERATIONS (If Multiplayer)

### 12.1 Replication Setup

**Player Character Replication**:
```cpp
BP_PlayerCharacter:
├─ Replicates: TRUE
├─ Replicate Movement: TRUE