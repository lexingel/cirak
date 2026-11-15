class_name Main
extends Node2D
## Frameless window: drag the apprentice, click it to type, right-click for the menu.

signal typed(text: String)
signal mic_changed(on: bool)
signal frequency_changed(level: String)
signal lang_changed(lang: String)
signal mic_device_changed(name: String)
signal edit_apps

const SETTINGS := "user://settings.cfg"
const DRAG_SLOP := 4
const LEVELS := ["low", "mid", "high"]
const LANGS := ["en", "tr"]
const PAUSE_ID := 5
const MIC_ID := 6
const APPS_ID := 7
const PTT_ID := 8
const TEXT := {
	"en": {"mic_off": "Turn mic off", "mic_on": "Turn mic on", "frequency": "Question frequency",
		"low": "Rarely", "mid": "Sometimes", "high": "Often", "language": "Language",
		"close": "Close", "placeholder": "What are you working on?", "paused": "Listening paused",
		"microphone": "Microphone", "default_mic": "Windows default",
		"apps": "Apps I may open...", "ptt": "Hold Right Ctrl to give a command"},
	"tr": {"mic_off": "Mikrofonu kapat", "mic_on": "Mikrofonu aç", "frequency": "Soru sıklığı",
		"low": "Az", "mid": "Orta", "high": "Çok", "language": "Dil",
		"close": "Kapat", "placeholder": "Ne yapıyorsun?", "paused": "Dinleme duraklatıldı",
		"microphone": "Mikrofon", "default_mic": "Windows varsayılanı",
		"apps": "Açabileceğim uygulamalar...", "ptt": "Komut için Sağ Ctrl'ye basılı tut"},
}

var apprentice: Apprentice
var text_box := LineEdit.new()
var menu := PopupMenu.new()
var freq_menu := PopupMenu.new()
var cfg := ConfigFile.new()
var mic_on := true
var level := "mid"
var lang := "en"
var lang_menu := PopupMenu.new()
var mic_menu := PopupMenu.new()
var mics: Array = []  ## mic names the listener reported; the menu lists "" (default) + these
var mic_device := ""
var paused_by = null  ## null = listening; "" or an app name = paused by a call

var _pressed := false
var _dragging := false
var _press_mouse := Vector2i.ZERO
var _press_win := Vector2i.ZERO


static func ui(l: String, key: String) -> String:
	return TEXT.get(l, TEXT["en"])[key]


## Greyed-out menu line saying why the apprentice isn't listening.
static func pause_text(l: String, who: String) -> String:
	var t := ui(l, "paused")
	return t if who.is_empty() else "%s (%s)" % [t, who]


static func mic_label(l: String, name: String) -> String:
	return ui(l, "default_mic") if name.is_empty() else name


static func clamp_to_screen(pos: Vector2i, size: Vector2i, rect: Rect2i) -> Vector2i:
	return Vector2i(
		clampi(pos.x, rect.position.x, rect.end.x - size.x),
		clampi(pos.y, rect.position.y, rect.end.y - size.y))


func _ready() -> void:
	apprentice = preload("res://apprentice.tscn").instantiate()
	apprentice.position = Vector2(130, 220 - 72)
	add_child(apprentice)
	apprentice.shape_changed.connect(_update_passthrough)

	text_box.position = Vector2(10, 30)
	text_box.size = Vector2(240, 30)
	text_box.visible = false
	text_box.text_submitted.connect(_on_text_submitted)
	text_box.gui_input.connect(_on_text_box_input)
	add_child(text_box)

	for i in LEVELS.size():
		freq_menu.add_radio_check_item("", i)
	freq_menu.id_pressed.connect(func(id): _set_level(LEVELS[id]))
	lang_menu.add_radio_check_item("English", 0)
	lang_menu.add_radio_check_item("Türkçe", 1)
	lang_menu.id_pressed.connect(func(id): _set_lang(LANGS[id]))
	menu.add_child(freq_menu)
	menu.add_child(lang_menu)
	mic_menu.id_pressed.connect(func(id): _set_mic_device(_mic_names()[id]))
	menu.add_child(mic_menu)
	menu.add_item("", 0)
	menu.add_submenu_node_item("", freq_menu, 1)
	menu.add_submenu_node_item("", lang_menu, 3)
	menu.add_submenu_node_item("", mic_menu, MIC_ID)
	menu.add_item("", APPS_ID)
	menu.add_item("", PTT_ID)
	menu.set_item_disabled(menu.get_item_index(PTT_ID), true)  # a hint, not a button
	menu.add_separator()
	menu.add_item("", 2)
	menu.id_pressed.connect(_on_menu)
	add_child(menu)

	cfg.load(SETTINGS)
	mic_on = cfg.get_value("prefs", "mic", true)
	level = cfg.get_value("prefs", "frequency", "mid")
	lang = cfg.get_value("prefs", "lang", "en")
	mic_device = cfg.get_value("prefs", "mic_device", "")
	_refresh_menu()

	var link := Link.new()
	add_child(link)
	link.message.connect(apprentice.handle)
	link.message.connect(_on_link_message)
	link.connected.connect(func():
		_set_paused(null)  # a fresh listener re-sends "paused" if a call is still on
		link.send({"type": "mic", "on": mic_on})
		link.send({"type": "frequency", "level": level})
		link.send({"type": "lang", "lang": lang})
		link.send({"type": "mic_device", "name": mic_device}))
	mic_device_changed.connect(func(n): link.send({"type": "mic_device", "name": n}))
	edit_apps.connect(func(): link.send({"type": "edit_apps"}))
	lang_changed.connect(func(l): link.send({"type": "lang", "lang": l}))
	typed.connect(func(t): link.send({"type": "typed", "text": t}))
	mic_changed.connect(func(on): link.send({"type": "mic", "on": on}))
	frequency_changed.connect(func(l): link.send({"type": "frequency", "level": l}))

	var win := get_window()
	var screen := DisplayServer.screen_get_usable_rect(DisplayServer.window_get_current_screen())
	var default_pos := Vector2i(screen.end.x - 300, screen.end.y - 260)
	var screens := []
	for i in DisplayServer.get_screen_count():
		screens.append(DisplayServer.screen_get_usable_rect(i))
	win.position = restore_pos(cfg.get_value("win", "pos", default_pos), win.size, screens)
	text_box.focus_exited.connect(_close_text_box)
	_update_passthrough()


## Saved spot on a monitor that still exists -> keep it there; otherwise pull it onto the first screen.
static func restore_pos(saved: Vector2i, size: Vector2i, screens: Array) -> Vector2i:
	for r in screens:
		if r.has_point(saved):
			return clamp_to_screen(saved, size, r)
	return clamp_to_screen(saved, size, screens[0])


## Click area: the sprite, plus (when shown) a wider strip on top for the bubble / text box.
static func click_polygon(sprite: Rect2, top: Rect2) -> PackedVector2Array:
	var s := sprite
	if not top.has_area():
		return PackedVector2Array([s.position, Vector2(s.end.x, s.position.y), s.end, Vector2(s.position.x, s.end.y)])
	var t := top
	return PackedVector2Array([
		t.position, Vector2(t.end.x, t.position.y), t.end, Vector2(s.end.x, t.end.y),
		s.end, Vector2(s.position.x, s.end.y), Vector2(s.position.x, t.end.y), Vector2(t.position.x, t.end.y)])


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		_pressed = false  # a release we never saw must not leave a drag stuck on
		if text_box.visible:
			_close_text_box()


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
	apprentice.bubble.close()  # typing comes first; the question can wait
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
		APPS_ID:
			edit_apps.emit()  # the listener opens its apps.json in Notepad


func _on_link_message(msg: Dictionary) -> void:
	match msg.get("type", ""):
		"paused":
			_set_paused(str(msg.get("who", "")))
		"resumed":
			_set_paused(null)
		"mics":
			mics = msg.get("list", [])
			_refresh_menu()


func _set_paused(who) -> void:
	paused_by = who
	var idx := menu.get_item_index(PAUSE_ID)
	if who == null:
		if idx >= 0:
			menu.remove_item(idx)
		return
	if idx < 0:
		menu.add_item("", PAUSE_ID)
		idx = menu.get_item_index(PAUSE_ID)
		menu.set_item_disabled(idx, true)
		menu.set_item_index(idx, 0)
	_refresh_menu()


func _mic_names() -> Array:
	var names := [""]
	names.append_array(mics)
	if not mic_device.is_empty() and not mics.has(mic_device):
		names.append(mic_device)  # saved mic that isn't plugged in now: keep it visible
	return names


func _set_mic_device(n: String) -> void:
	mic_device = n
	mic_device_changed.emit(n)
	_save()
	_refresh_menu()


func _set_level(l: String) -> void:
	level = l
	frequency_changed.emit(l)
	_save()
	_refresh_menu()


func _set_lang(l: String) -> void:
	lang = l
	lang_changed.emit(l)
	_save()
	_refresh_menu()


func _refresh_menu() -> void:
	menu.set_item_text(menu.get_item_index(0), ui(lang, "mic_off" if mic_on else "mic_on"))
	menu.set_item_text(menu.get_item_index(1), ui(lang, "frequency"))
	menu.set_item_text(menu.get_item_index(3), ui(lang, "language"))
	menu.set_item_text(menu.get_item_index(2), ui(lang, "close"))
	for i in LEVELS.size():
		freq_menu.set_item_text(i, ui(lang, LEVELS[i]))
		freq_menu.set_item_checked(i, LEVELS[i] == level)
	for i in LANGS.size():
		lang_menu.set_item_checked(i, LANGS[i] == lang)
	menu.set_item_text(menu.get_item_index(MIC_ID), ui(lang, "microphone"))
	menu.set_item_text(menu.get_item_index(APPS_ID), ui(lang, "apps"))
	menu.set_item_text(menu.get_item_index(PTT_ID), ui(lang, "ptt"))
	mic_menu.clear()
	var names := _mic_names()
	for i in names.size():
		mic_menu.add_radio_check_item(mic_label(lang, names[i]), i)
		mic_menu.set_item_checked(i, names[i] == mic_device)
	text_box.placeholder_text = ui(lang, "placeholder")
	if paused_by != null:
		menu.set_item_text(menu.get_item_index(PAUSE_ID), pause_text(lang, paused_by))


func _save() -> void:
	cfg.set_value("win", "pos", get_window().position)
	cfg.set_value("prefs", "mic", mic_on)
	cfg.set_value("prefs", "frequency", level)
	cfg.set_value("prefs", "lang", lang)
	cfg.set_value("prefs", "mic_device", mic_device)
	cfg.save(SETTINGS)


## Clicks outside the apprentice (and the bubble / text box when open) fall through to the desktop.
func _update_passthrough() -> void:
	var top := Rect2()
	if apprentice.bubble.visible:
		top = Rect2(apprentice.position + apprentice.bubble.position, apprentice.bubble.size)
	if text_box.visible:
		var box := Rect2(text_box.position, text_box.size)
		top = box if not top.has_area() else top.merge(box)
	DisplayServer.window_set_mouse_passthrough(click_polygon(apprentice.sprite_rect(), top))
