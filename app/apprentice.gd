class_name Apprentice
extends Node2D
## The apprentice: works quietly, looks up when you talk, nods, asks.

signal shape_changed  ## bubble shown/hidden -> window click area changes

enum State { WORKING, LISTENING, NODDING, ASKING }

const SCALE := 3
const FRAME := 48
const ANIMS := {
	State.WORKING: ["working", 8.0, true],
	State.LISTENING: ["listening", 2.0, true],
	State.NODDING: ["nodding", 4.0, false],  ## at 8 fps the nod was a twitch
	State.ASKING: ["asking", 3.0, true],
}
const TOSS := ["toss", 8.0, false]  ## now and then while working: drops a leaf in, then stirs on
const TOSS_EVERY := Vector2(45.0, 120.0)  ## seconds, random in this range

var state: State = State.WORKING
var skin := ""  ## set before _ready (or via set_skin) to start in another look
var sprite := AnimatedSprite2D.new()
var bubble := Bubble.new()
var toss_timer := Timer.new()


func _ready() -> void:
	sprite.sprite_frames = _load_frames()
	sprite.scale = Vector2(SCALE, SCALE)
	sprite.animation_finished.connect(_on_anim_finished)
	sprite.animation_looped.connect(_on_loop)
	add_child(sprite)
	bubble.closed.connect(_on_bubble_closed)
	add_child(bubble)
	bubble.resized.connect(shape_changed.emit)  # click area follows the bubble's real size
	bubble.position = Vector2(-118, -FRAME * SCALE / 2.0 - 70)
	_enter(State.WORKING)
	toss_timer.timeout.connect(_on_toss_timer)
	add_child(toss_timer)
	toss_timer.start(randf_range(TOSS_EVERY.x, TOSS_EVERY.y))


## Which look: "" = the wizard (art/), otherwise a folder in art/skins/ (blacksmith, healer, ...).
static func art_dir(skin: String) -> String:
	return "res://art/" if skin.is_empty() else "res://art/skins/%s/" % skin


## Swaps the look; the current pose keeps going in the new clothes.
func set_skin(s: String) -> void:
	skin = s
	sprite.sprite_frames = _load_frames()
	_enter(state)


## Strips live in <art_dir>/apprentice_<name>.png (48 px frames, side by side).
## Loaded from disk so new art from tools/import_frames.py works without an editor import.
func _load_frames() -> SpriteFrames:
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	for spec in ANIMS.values() + [TOSS]:
		var name: String = spec[0]
		sf.add_animation(name)
		sf.set_animation_speed(name, spec[1])
		sf.set_animation_loop(name, spec[2])
		var img := strip(skin, name)
		if img == null:
			continue
		var tex := ImageTexture.create_from_image(img)
		for i in range(img.get_width() / FRAME):
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(i * FRAME, 0, FRAME, FRAME)
			sf.add_frame(name, at)
	return sf


## One state's strip for a look, or null if it is missing.
static func strip(s: String, name: String) -> Image:
	var path := art_dir(s) + "apprentice_%s.png" % name
	if OS.has_feature("editor"):  # read the png itself: fresh art needs no reimport
		return Image.load_from_file(ProjectSettings.globalize_path(path)) if FileAccess.file_exists(path) else null
	var tex = load(path) if ResourceLoader.exists(path) else null  # export: the imported texture
	return tex.get_image() if tex else null


## First listening frame of a look, for the menu (the wizard's if that look's art is missing).
static func preview(s: String) -> Texture2D:
	var img := strip(s, "listening")
	if img == null:
		img = strip("", "listening")
	var at := AtlasTexture.new()
	at.atlas = ImageTexture.create_from_image(img)
	at.region = Rect2(0, 0, FRAME, FRAME)
	return at


func handle(msg: Dictionary) -> void:
	match msg.get("type", ""):
		"speech_start":
			if state != State.ASKING:
				_enter(State.LISTENING)
		"speech_end":
			if state == State.LISTENING:
				_enter(State.NODDING)
		"question":
			bubble.show_text(str(msg.get("text", "")))
			_enter(State.ASKING)
			shape_changed.emit()
		"paused":
			_enter(State.WORKING)
		"say":  # a command was done (or not): a short note and a nod, no question pose
			bubble.show_text(str(msg.get("text", "")))
			_enter(State.NODDING)
			shape_changed.emit()


func on_typed(text: String) -> bool:
	if text.strip_edges().is_empty():
		return false
	_enter(State.NODDING)
	return true


## Click area of the sprite, in this node's parent space.
func sprite_rect() -> Rect2:
	var half := FRAME * SCALE / 2.0
	return Rect2(position - Vector2(half, half), Vector2(FRAME * SCALE, FRAME * SCALE))


## Plays the toss once if the apprentice is just stirring. Returns whether it started.
func toss() -> bool:
	if state != State.WORKING or sprite.animation != ANIMS[State.WORKING][0]:
		return false
	sprite.play(TOSS[0])
	return true


func _on_toss_timer() -> void:
	toss()
	toss_timer.start(randf_range(TOSS_EVERY.x, TOSS_EVERY.y))


## Each stir at a slightly different pace, so it never ticks like a metronome.
func _on_loop() -> void:
	if sprite.animation == ANIMS[State.WORKING][0]:
		sprite.speed_scale = randf_range(0.9, 1.1)


func _enter(s: State) -> void:
	state = s
	sprite.speed_scale = 1.0
	sprite.play(ANIMS[s][0])


func _on_anim_finished() -> void:
	if state == State.NODDING or sprite.animation == TOSS[0]:
		_enter(State.WORKING)


func _on_bubble_closed() -> void:
	if state == State.ASKING:
		_enter(State.WORKING)
	shape_changed.emit()
