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
	State.NODDING: ["nodding", 8.0, false],
	State.ASKING: ["asking", 3.0, true],
}

var state: State = State.WORKING
var sprite := AnimatedSprite2D.new()
var bubble := Bubble.new()


func _ready() -> void:
	sprite.sprite_frames = _load_frames()
	sprite.scale = Vector2(SCALE, SCALE)
	sprite.animation_finished.connect(_on_anim_finished)
	add_child(sprite)
	bubble.closed.connect(_on_bubble_closed)
	add_child(bubble)
	bubble.position = Vector2(-118, -FRAME * SCALE / 2.0 - 70)
	_enter(State.WORKING)


## Strips live in art/apprentice_<name>.png (48 px frames, side by side).
## Loaded from disk so new art from tools/import_frames.py works without an editor import.
func _load_frames() -> SpriteFrames:
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	for s in ANIMS:
		var spec: Array = ANIMS[s]
		var name: String = spec[0]
		sf.add_animation(name)
		sf.set_animation_speed(name, spec[1])
		sf.set_animation_loop(name, spec[2])
		var img := Image.load_from_file(ProjectSettings.globalize_path("res://art/apprentice_%s.png" % name))
		if img == null:
			continue
		var tex := ImageTexture.create_from_image(img)
		for i in range(img.get_width() / FRAME):
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(i * FRAME, 0, FRAME, FRAME)
			sf.add_frame(name, at)
	return sf


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


func on_typed(text: String) -> bool:
	if text.strip_edges().is_empty():
		return false
	_enter(State.NODDING)
	return true


## Click area of the sprite, in this node's parent space.
func sprite_rect() -> Rect2:
	var half := FRAME * SCALE / 2.0
	return Rect2(position - Vector2(half, half), Vector2(FRAME * SCALE, FRAME * SCALE))


func _enter(s: State) -> void:
	state = s
	sprite.play(ANIMS[s][0])


func _on_anim_finished() -> void:
	if state == State.NODDING:
		_enter(State.WORKING)


func _on_bubble_closed() -> void:
	if state == State.ASKING:
		_enter(State.WORKING)
	shape_changed.emit()
