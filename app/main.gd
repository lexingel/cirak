class_name Main
extends Node2D
## Frameless window: drag the apprentice, click it to type, right-click for the menu.

signal typed(text: String)
signal mic_changed(on: bool)
signal frequency_changed(level: String)

const SETTINGS := "user://settings.cfg"
const DRAG_SLOP := 4
const LEVELS := ["low", "mid", "high"]

var apprentice: Apprentice
var text_box := LineEdit.new()
var menu := PopupMenu.new()
var freq_menu := PopupMenu.new()
var cfg := ConfigFile.new()
var mic_on := true
var level := "mid"

var _pressed := false
var _dragging := false
var _press_mouse := Vector2i.ZERO
var _press_win := Vector2i.ZERO


static func clamp_to_screen(pos: Vector2i, size: Vector2i, rect: Rect2i) -> Vector2i:
	return Vector2i(
		clampi(pos.x, rect.position.x, rect.end.x - size.x),
		clampi(pos.y, rect.position.y, rect.end.y - size.y))


func _ready() -> void:
	apprentice = preload("res://apprentice.tscn").instantiate()
	apprentice.position = Vector2(130, 220 - 72)
	add_child(apprentice)
	apprentice.shape_changed.connect(_update_passthrough)

	text_box.placeholder_text = "Ne yapıyorsun?"
	text_box.position = Vector2(10, 30)
	text_box.size = Vector2(240, 30)
	text_box.visible = false
	text_box.text_submitted.connect(_on_text_submitted)
	text_box.gui_input.connect(_on_text_box_input)
	add_child(text_box)

	for i in LEVELS.size():
		freq_menu.add_radio_check_item(["Az", "Orta", "Çok"][i], i)
	freq_menu.id_pressed.connect(func(id): _set_level(LEVELS[id]))
	menu.add_child(freq_menu)
	menu.add_item("", 0)
	menu.add_submenu_node_item("Soru sıklığı", freq_menu)
	menu.add_separator()
	menu.add_item("Kapat", 2)
	menu.id_pressed.connect(_on_menu)
	add_child(menu)

	cfg.load(SETTINGS)
	mic_on = cfg.get_value("prefs", "mic", true)
	level = cfg.get_value("prefs", "frequency", "mid")
	_refresh_menu()
	var win := get_window()
	var screen := DisplayServer.screen_get_usable_rect(DisplayServer.window_get_current_screen())
	var default_pos := Vector2i(screen.end.x - 300, screen.end.y - 260)
	win.position = clamp_to_screen(cfg.get_value("win", "pos", default_pos), win.size, _all_screens_rect(win.position))
	_update_passthrough()


func _all_screens_rect(near: Vector2i) -> Rect2i:
	# ponytail: clamps to the screen nearest the saved spot's primary, not a true multi-monitor union
	var idx := 0
	for i in DisplayServer.get_screen_count():
		if DisplayServer.screen_get_usable_rect(i).has_point(near):
			idx = i
	return DisplayServer.screen_get_usable_rect(idx)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed and apprentice.sprite_rect().has_point(event.position):
				_pressed = true
				_dragging = false
				_press_mouse = DisplayServer.mouse_get_position()
				_press_win = get_window().position
			elif not event.pressed and _pressed:
				_pressed = false
				if _dragging:
					_save()
				else:
					_open_text_box()
		elif event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
			menu.popup(Rect2i(DisplayServer.mouse_get_position(), Vector2i.ZERO))
	elif event is InputEventMouseMotion and _pressed:
		var delta := DisplayServer.mouse_get_position() - _press_mouse
		if _dragging or delta.length() > DRAG_SLOP:
			_dragging = true
			get_window().position = _press_win + delta


func _open_text_box() -> void:
	text_box.visible = true
	text_box.grab_focus()
	_update_passthrough()


func _close_text_box() -> void:
	text_box.text = ""
	text_box.visible = false
	_update_passthrough()


func _on_text_submitted(t: String) -> void:
	if apprentice.on_typed(t):
		typed.emit(t)
	_close_text_box()


func _on_text_box_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		_close_text_box()


func _on_menu(id: int) -> void:
	match id:
		0:
			mic_on = not mic_on
			mic_changed.emit(mic_on)
			_save()
			_refresh_menu()
		2:
			get_tree().quit()


func _set_level(l: String) -> void:
	level = l
	frequency_changed.emit(l)
	_save()
	_refresh_menu()


func _refresh_menu() -> void:
	menu.set_item_text(menu.get_item_index(0), "Mikrofonu kapat" if mic_on else "Mikrofonu aç")
	for i in LEVELS.size():
		freq_menu.set_item_checked(i, LEVELS[i] == level)


func _save() -> void:
	cfg.set_value("win", "pos", get_window().position)
	cfg.set_value("prefs", "mic", mic_on)
	cfg.set_value("prefs", "frequency", level)
	cfg.save(SETTINGS)


## Clicks outside the apprentice (and the bubble / text box when open) fall through to the desktop.
func _update_passthrough() -> void:
	var r := apprentice.sprite_rect()
	if text_box.visible or apprentice.bubble.visible:
		r = Rect2(Vector2.ZERO, Vector2(get_window().size))
	DisplayServer.window_set_mouse_passthrough(PackedVector2Array([
		r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]))
