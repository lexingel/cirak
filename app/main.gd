class_name Main
extends Node2D
## Frameless window: drag the apprentice, click it to type, right-click for the menu.

signal typed(text: String)
signal mic_changed(on: bool)
signal frequency_changed(level: String)
signal lang_changed(lang: String)
signal mic_device_changed(name: String)
signal edit_apps
signal pick_ptt_key
signal pull_model
signal model_picked(name: String)

const SETTINGS := "user://settings.cfg"
const DRAG_SLOP := 4
const LEVELS := ["off", "low", "mid", "high"]  ## "off": listens, never asks
const LANGS := ["en", "tr"]
const PAUSE_ID := 5
const MIC_ID := 6
const APPS_ID := 7
const PTT_ID := 8
const SKIN_ID := 9
const BRAIN_ID := 10
const MODEL_ID := 11
const MICPERM_ID := 12
const HELP_ID := 13
const HIDE_ID := 14
const HIDE_SECONDS := 3600
const CALM_ID := 15
const MODELS := ["qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b"]  ## the listener's asker.MODELS
const MODEL_SIZE := ["1 GB", "2 GB", "4.7 GB"]
const MODEL_NOTE := {
	"en": ["fast, free licence; weaker in Turkish", "better Turkish; research licence (not for commercial use)",
		"best questions; slow without a graphics card"],
	"tr": ["hızlı, serbest lisans; Türkçesi zayıf", "Türkçesi daha iyi; araştırma lisansı (ticari kullanım yok)",
		"en iyi sorular; ekran kartı yoksa yavaş"],
}
const SKINS := ["", "demirci", "sifaci", "katip", "okcu", "asci"]  ## "" = the wizard
const SKIN_NAMES := {
	"en": ["Wizard", "Blacksmith", "Healer", "Scribe", "Archer", "Cook"],
	"tr": ["Büyücü", "Demirci", "Şifacı", "Katip", "Okçu", "Aşçı"],
}
const TEXT := {
	"en": {"mic_off": "Turn mic off", "mic_on": "Turn mic on", "frequency": "Question frequency",
		"off": "Never (just listen)", "low": "Rarely", "mid": "Sometimes", "high": "Often", "language": "Language",
		"close": "Close", "placeholder": "What are you working on?", "paused": "Listening paused",
		"microphone": "Microphone", "default_mic": "Windows default",
		"apps": "Apps I may open...", "skin": "Apprentice", "ptt": "Command key: %s...", "ptt_default": "Right Ctrl",
		"ptt_pick": "Press the key you'll hold for commands (Esc: keep the old one)",
		"no_ollama": "Better questions: get Ollama (free)...",
		"no_model": "Better questions: download %s (%s)...", "model": "Question model", "help": "What can you do?",
		"mic_blocked": "Windows microphone permission is off: open Settings...",
		"mic_blocked_say": "Windows' microphone permission is off, so I hear nothing. Right-click me to open Settings",
		"after_ollama": "Install Ollama and start it; I'll notice within a minute",
		"first_hint": "Right-click me for the microphone, language and what I can do",
		"hide": "Hide for an hour (say \"Apprentice, come back\")",
		"calm": "Calm apprentice (no tossing)"},
	"tr": {"mic_off": "Mikrofonu kapat", "mic_on": "Mikrofonu aç", "frequency": "Soru sıklığı",
		"off": "Hiç (sadece dinle)", "low": "Az", "mid": "Orta", "high": "Çok", "language": "Dil",
		"close": "Kapat", "placeholder": "Ne yapıyorsun?", "paused": "Dinleme duraklatıldı",
		"microphone": "Mikrofon", "default_mic": "Windows varsayılanı",
		"apps": "Açabileceğim uygulamalar...", "skin": "Çırak", "ptt": "Komut tuşu: %s...", "ptt_default": "Sağ Ctrl",
		"ptt_pick": "Komut için basılı tutacağın tuşa bas (Esc: eskisi kalsın)",
		"no_ollama": "Daha iyi sorular: Ollama'yı indir (ücretsiz)...",
		"no_model": "Daha iyi sorular: %s indir (%s)...", "model": "Soru modeli", "help": "Neler yapabilirsin?",
		"mic_blocked": "Windows mikrofon izni kapalı: Ayarlar'ı aç...",
		"mic_blocked_say": "Windows'un mikrofon izni kapalı, hiçbir şey duymuyorum. Ayarlar için bana sağ tıkla",
		"after_ollama": "Ollama'yı kurup açınca bir dakika içinde fark ederim",
		"first_hint": "Mikrofon, dil ve neler yapabildiğim için bana sağ tıkla",
		"hide": "1 saat saklan (\"Çırak, geri gel\" de)",
		"calm": "Sakin çırak (malzeme atmaz)"},
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
var skin_menu := PopupMenu.new()
var skin := ""
var mics: Array = []  ## mic names the listener reported; the menu lists "" (default) + these
var mic_device := ""
var ptt_vk := 0xA3  ## push-to-talk key as a Windows key code; the listener picks and names it
var ptt_name := ""  ## "" = Right Ctrl, never changed
var paused_by = null  ## null = listening; "" or an app name = paused by a call
var brain := "ok"  ## questions: "ok" (local model), "no_model", "no_ollama" (from the listener)
var model := ""  ## the question model the listener uses (it keeps the choice in model.txt)
var model_menu := PopupMenu.new()
var _told_mic_blocked := false
var mic_blocked := false
var full_rect = null  ## [l, t, r, b] of a monitor a fullscreen app covers, or null
var hidden_until := 0  ## Time.get_ticks_msec() until which the user asked it out of sight

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


## Menu line for the push-to-talk key; clicking it picks a new one.
static func ptt_label(l: String, name: String) -> String:
	return ui(l, "ptt") % (ui(l, "ptt_default") if name.is_empty() else name)


static func mic_label(l: String, name: String) -> String:
	return ui(l, "default_mic") if name.is_empty() else name


static func clamp_to_screen(pos: Vector2i, size: Vector2i, rect: Rect2i) -> Vector2i:
	return Vector2i(
		clampi(pos.x, rect.position.x, rect.end.x - size.x),
		clampi(pos.y, rect.position.y, rect.end.y - size.y))


func _ready() -> void:
	cfg.load(SETTINGS)
	skin = cfg.get_value("prefs", "skin", "")
	if not SKINS.has(skin):
		skin = ""
	apprentice = preload("res://apprentice.tscn").instantiate()
	apprentice.skin = skin
	apprentice.calm = cfg.get_value("prefs", "calm", false)
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
	for i in SKINS.size():
		skin_menu.add_radio_check_item("", i)
		skin_menu.set_item_icon(i, Apprentice.preview(SKINS[i]))
		skin_menu.set_item_icon_max_width(i, 32)
	skin_menu.id_pressed.connect(func(id): _set_skin(SKINS[id]))
	menu.add_child(skin_menu)
	menu.add_submenu_node_item("", skin_menu, SKIN_ID)
	for i in MODELS.size():
		model_menu.add_radio_check_item("", i)
	model_menu.id_pressed.connect(func(id): model_picked.emit(MODELS[id]))  # the listener answers with "brain"
	menu.add_child(model_menu)
	menu.add_submenu_node_item("", model_menu, MODEL_ID)
	menu.add_item("", APPS_ID)
	menu.add_item("", PTT_ID)
	menu.add_item("", HELP_ID)
	menu.add_item("", HIDE_ID)
	menu.add_check_item("", CALM_ID)
	menu.add_separator()
	menu.add_item("", 2)
	menu.id_pressed.connect(_on_menu)
	add_child(menu)

	mic_on = cfg.get_value("prefs", "mic", true)
	level = cfg.get_value("prefs", "frequency", "mid")
	lang = cfg.get_value("prefs", "lang", "en")
	mic_device = cfg.get_value("prefs", "mic_device", "")
	ptt_vk = cfg.get_value("prefs", "ptt_vk", 0xA3)
	ptt_name = cfg.get_value("prefs", "ptt_name", "")
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
		link.send({"type": "mic_device", "name": mic_device})
		link.send({"type": "ptt_key", "vk": ptt_vk}))
	pick_ptt_key.connect(func(): link.send({"type": "pick_ptt_key"}))
	pull_model.connect(func(): link.send({"type": "pull_model"}))
	model_picked.connect(func(n): link.send({"type": "model", "name": n}))
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
		PTT_ID:
			apprentice.handle({"type": "say", "text": ui(lang, "ptt_pick")})
			pick_ptt_key.emit()  # the listener waits for the key and answers with "ptt_key"
		HELP_ID:
			var page := help_file(lang)
			if page != "":
				OS.shell_open(ProjectSettings.globalize_path(page))
		CALM_ID:
			apprentice.calm = not apprentice.calm
			_save()
			_refresh_menu()
		HIDE_ID:
			_hide_for(HIDE_SECONDS)
		MICPERM_ID:
			OS.shell_open("ms-settings:privacy-microphone")  # the user turns it on; we never change it
		BRAIN_ID:
			if brain == "no_model":
				pull_model.emit()  # the listener downloads it and tells progress in the bubble
			else:
				OS.shell_open("https://ollama.com/download")
				apprentice.handle({"type": "say", "text": ui(lang, "after_ollama")})


func _on_link_message(msg: Dictionary) -> void:
	match msg.get("type", ""):
		"paused":
			_set_paused(str(msg.get("who", "")))
		"resumed":
			_set_paused(null)
		"mics":
			mics = msg.get("list", [])
			_refresh_menu()
			if not cfg.get_value("prefs", "hinted", false):  # once ever: where the menu is
				cfg.set_value("prefs", "hinted", true)
				_save()
				apprentice.handle({"type": "say", "text": ui(lang, "first_hint")})
		"brain":
			model = str(msg.get("model", model))
			_set_brain(str(msg.get("state", "ok")))
			_refresh_menu()  # ticks the model even when the state didn't change
		"fullscreen":
			full_rect = msg.get("rect")
			_update_visibility()
		"hide":
			_hide_for(int(msg.get("seconds", HIDE_SECONDS)))
		"show":
			hidden_until = 0
			_update_visibility()
		"mic_blocked":
			_set_mic_blocked(bool(msg.get("blocked", false)))
		"ptt_key":
			ptt_vk = int(msg.get("vk", 0xA3))  # JSON numbers arrive as floats
			ptt_name = str(msg.get("name", ""))
			_save()
			_refresh_menu()


func _set_paused(who) -> void:
	paused_by = who
	queue_redraw()
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


## Menu line for better questions: get Ollama, or download the model; none once the model answers.
static func brain_text(l: String, state: String, m: String) -> String:
	if state == "no_model":
		var i := MODELS.find(m)
		return ui(l, "no_model") % [m, MODEL_SIZE[i] if i >= 0 else "?"]
	return "" if state == "ok" else ui(l, state)


## The help page in the user's language, copied out of the exe so the browser can open it ("" if missing).
static func help_file(l: String) -> String:
	var html := FileAccess.get_file_as_string("res://help/help_%s.html" % ("tr" if l == "tr" else "en"))
	if html.is_empty():
		return ""
	var out := "user://help_%s.html" % l
	var f := FileAccess.open(out, FileAccess.WRITE)
	if f == null:
		return ""
	f.store_string(html)
	f.close()
	return out


## "qwen2.5:3b · 2 GB · better Turkish; ..." for the Question model submenu.
static func model_label(l: String, i: int) -> String:
	return "%s · %s · %s" % [MODELS[i], MODEL_SIZE[i], MODEL_NOTE.get(l, MODEL_NOTE["en"])[i]]


func _set_brain(state: String) -> void:
	brain = state
	var idx := menu.get_item_index(BRAIN_ID)
	if state == "ok":
		if idx >= 0:
			menu.remove_item(idx)
		return
	if idx < 0:
		menu.add_item("", BRAIN_ID)
		menu.set_item_index(menu.get_item_index(BRAIN_ID), menu.get_item_count() - 3)  # above the separator
	_refresh_menu()


## Windows' mic privacy switch is off: a menu line to Settings, and the apprentice says it once.
func _set_mic_blocked(blocked: bool) -> void:
	mic_blocked = blocked
	queue_redraw()
	var idx := menu.get_item_index(MICPERM_ID)
	if not blocked:
		if idx >= 0:
			menu.remove_item(idx)
		return
	if idx < 0:
		menu.add_item("", MICPERM_ID)
		menu.set_item_index(menu.get_item_index(MICPERM_ID), 0)  # top: it explains the silence
	_refresh_menu()
	if not _told_mic_blocked:
		_told_mic_blocked = true
		apprentice.handle({"type": "say", "text": ui(lang, "mic_blocked_say")})


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


func _set_skin(s: String) -> void:
	skin = s
	apprentice.set_skin(s)
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
	menu.set_item_text(menu.get_item_index(SKIN_ID), ui(lang, "skin"))
	for i in SKINS.size():
		skin_menu.set_item_text(i, SKIN_NAMES.get(lang, SKIN_NAMES["en"])[i])
		skin_menu.set_item_checked(i, SKINS[i] == skin)
	menu.set_item_text(menu.get_item_index(PTT_ID), ptt_label(lang, ptt_name))
	mic_menu.clear()
	var names := _mic_names()
	for i in names.size():
		mic_menu.add_radio_check_item(mic_label(lang, names[i]), i)
		mic_menu.set_item_checked(i, names[i] == mic_device)
	text_box.placeholder_text = ui(lang, "placeholder")
	if paused_by != null:
		menu.set_item_text(menu.get_item_index(PAUSE_ID), pause_text(lang, paused_by))
	if menu.get_item_index(BRAIN_ID) >= 0:
		menu.set_item_text(menu.get_item_index(BRAIN_ID), brain_text(lang, brain, model))
	if menu.get_item_index(MICPERM_ID) >= 0:
		menu.set_item_text(menu.get_item_index(MICPERM_ID), ui(lang, "mic_blocked"))
	menu.set_item_text(menu.get_item_index(MODEL_ID), ui(lang, "model"))
	menu.set_item_text(menu.get_item_index(HELP_ID), ui(lang, "help"))
	menu.set_item_text(menu.get_item_index(HIDE_ID), ui(lang, "hide"))
	menu.set_item_text(menu.get_item_index(CALM_ID), ui(lang, "calm"))
	menu.set_item_checked(menu.get_item_index(CALM_ID), apprentice.calm)
	queue_redraw()  # the mic dot
	for i in MODELS.size():
		model_menu.set_item_text(i, model_label(lang, i))
		model_menu.set_item_checked(i, MODELS[i] == model)


func _save() -> void:
	cfg.set_value("win", "pos", get_window().position)
	cfg.set_value("prefs", "mic", mic_on)
	cfg.set_value("prefs", "frequency", level)
	cfg.set_value("prefs", "lang", lang)
	cfg.set_value("prefs", "mic_device", mic_device)
	cfg.set_value("prefs", "skin", skin)
	cfg.set_value("prefs", "calm", apprentice.calm)
	cfg.set_value("prefs", "ptt_vk", ptt_vk)
	cfg.set_value("prefs", "ptt_name", ptt_name)
	cfg.save(SETTINGS)


## Clicks outside the apprentice (and the bubble / text box when open) fall through to the desktop.
func _update_passthrough() -> void:
	if not visible:  # out of sight: a 1 px corner, every click goes to the game or desktop
		DisplayServer.window_set_mouse_passthrough(PackedVector2Array([Vector2.ZERO, Vector2(1, 0), Vector2(0, 1)]))
		return
	var top := Rect2()
	if apprentice.bubble.visible:
		top = Rect2(apprentice.position + apprentice.bubble.position, apprentice.bubble.size)
	if text_box.visible:
		var box := Rect2(text_box.position, text_box.size)
		top = box if not top.has_area() else top.merge(box)
	DisplayServer.window_set_mouse_passthrough(click_polygon(apprentice.sprite_rect(), top))


## Should the apprentice step aside? A fullscreen app on its monitor, or the user said "hide".
static func should_hide(rect, win_pos: Vector2i, win_size: Vector2i, now: int, until: int) -> bool:
	if now < until:
		return true
	if rect == null or (rect as Array).size() != 4:
		return false
	var c := win_pos + win_size / 2
	return c.x >= rect[0] and c.x < rect[2] and c.y >= rect[1] and c.y < rect[3]


func _hide_for(seconds: int) -> void:
	hidden_until = Time.get_ticks_msec() + seconds * 1000
	get_tree().create_timer(seconds + 0.5).timeout.connect(_update_visibility)
	_update_visibility()


func _update_visibility() -> void:
	var win := get_window()
	var hide := should_hide(full_rect, win.position, win.size, Time.get_ticks_msec(), hidden_until)
	if hide == not visible:
		return
	visible = not hide
	if hide and text_box.visible:
		_close_text_box()
	_update_passthrough()


## The small dot by the apprentice: "on" listening, "paused" (a call), "off" (mic off or blocked).
static func mic_state(on: bool, paused, blocked: bool) -> String:
	if not on or blocked:
		return "off"
	return "on" if paused == null else "paused"


const MIC_COLORS := {"on": Color("4caf50"), "paused": Color("d9a441"), "off": Color("c0392b")}


func _draw() -> void:
	var r := apprentice.sprite_rect()
	var p := Vector2(r.end.x - 26, r.end.y - 16)  # just right of the cauldron
	var st := mic_state(mic_on, paused_by, mic_blocked)
	draw_circle(p, 5.0, Color("2a2230"))
	draw_circle(p, 3.5, MIC_COLORS[st])
	if st == "off":
		draw_line(p + Vector2(-2, -2), p + Vector2(2, 2), Color.WHITE, 1.0)
		draw_line(p + Vector2(2, -2), p + Vector2(-2, 2), Color.WHITE, 1.0)
