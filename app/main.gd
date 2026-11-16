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
const MOD_ID := 16
const FULL_LISTEN_ID := 17
const MORE_ID := 18
const STATUS_ID := 19
const LOOK_STRIPS := ["working", "listening", "nodding", "asking"]  ## a mod look needs these; toss is optional
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
		"first_hint": "Hi! Tell me what you're working on. Right-click me for help",
		"hide": "Hide for an hour", "hide_bye": "Say \"Apprentice, come back\" when you want me",
		"hide_no": "I can't hear you right now, so I couldn't come back. Turn the mic on first",
		"settings": "Settings", "no_listener": "Not listening: the listener isn't running",
		"no_mic": "No microphone found (typing still works)",
		"calm": "Calm apprentice", "mods": "Mod folder...",
		"full_listen": "Listen during fullscreen",
		"jar": "A jar is full, it's on the shelf now"},
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
		"first_hint": "Merhaba! Ne üzerinde çalıştığını anlat. Yardım için bana sağ tıkla",
		"hide": "1 saat saklan", "hide_bye": "Beni istediğinde \"Çırak, geri gel\" de",
		"hide_no": "Şu an seni duyamıyorum, geri gelemezdim. Önce mikrofonu aç",
		"settings": "Ayarlar", "no_listener": "Dinlemiyor: dinleyici çalışmıyor",
		"no_mic": "Mikrofon bulunamadı (yazmak yine çalışır)",
		"calm": "Sakin çırak", "mods": "Mod klasörü...",
		"full_listen": "Tam ekranda da dinle",
		"jar": "Bir kavanoz doldu, rafa koydum"},
}

var apprentice: Apprentice
var text_box := LineEdit.new()
var menu := PopupMenu.new()
var more_menu := PopupMenu.new()  ## "Settings": everything not needed every day
var freq_menu := PopupMenu.new()
var cfg := ConfigFile.new()
var mic_on := true
var full_listen := true  ## menu: keep listening while a fullscreen app hides the apprentice
var _mic_sent := true  ## what the listener was last told (mic_on, minus a fullscreen pause)
var level := "mid"
var lang := "en"
var lang_menu := PopupMenu.new()
var mic_menu := PopupMenu.new()
var skin_menu := PopupMenu.new()
var skin := ""
var skins: Array = []  ## SKINS + the user's own looks ("mod/<name>")
var jars := Jars.new()
var _talk_from := 0  ## ticks when the user started talking, 0 = not talking
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
var listener_up := false  ## the websocket is open
var no_mic := false  ## the listener found no microphone
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
	skins = SKINS + mod_looks(Apprentice.mods())
	skin = cfg.get_value("prefs", "skin", "")
	if not skins.has(skin):
		skin = ""
	apprentice = preload("res://apprentice.tscn").instantiate()
	apprentice.skin = skin
	apprentice.calm = cfg.get_value("prefs", "calm", true)  # calm by default: no unasked motion
	apprentice.position = Vector2(130, 220 - 72)
	add_child(apprentice)
	apprentice.shape_changed.connect(_update_passthrough)
	_layout()
	jars.seconds = cfg.get_value("prefs", "talk", 0.0)
	jars.stepped.connect(_save)
	jars.filled.connect(func(): apprentice.handle({"type": "say", "text": ui(lang, "jar")}))
	add_child(jars)

	var tb := StyleBoxFlat.new()
	tb.bg_color = Color("f6eedb")
	tb.border_color = Color("2a2230")
	tb.set_border_width_all(2)
	tb.set_corner_radius_all(8)
	tb.set_content_margin_all(6)
	for k in ["normal", "focus"]:
		text_box.add_theme_stylebox_override(k, tb)
	text_box.add_theme_color_override("font_color", Color("2a2230"))
	text_box.add_theme_color_override("font_placeholder_color", Color("2a2230", 0.5))
	text_box.add_theme_color_override("caret_color", Color("2a2230"))
	text_box.add_theme_font_size_override("font_size", 15)
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
	more_menu.add_child(mic_menu)
	for i in skins.size():
		skin_menu.add_radio_check_item("", i)
		skin_menu.set_item_icon(i, Apprentice.preview(skins[i]))
		skin_menu.set_item_icon_max_width(i, 32)
	skin_menu.id_pressed.connect(func(id): _set_skin(skins[id]))
	more_menu.add_child(skin_menu)
	for i in MODELS.size():
		model_menu.add_radio_check_item("", i)
	model_menu.id_pressed.connect(func(id): model_picked.emit(MODELS[id]))  # the listener answers with "brain"
	more_menu.add_child(model_menu)
	# the everyday few on top, the rest one level down: a short menu for a first look
	more_menu.add_submenu_node_item("", mic_menu, MIC_ID)
	more_menu.add_submenu_node_item("", skin_menu, SKIN_ID)
	more_menu.add_submenu_node_item("", model_menu, MODEL_ID)
	more_menu.add_item("", APPS_ID)
	more_menu.add_item("", PTT_ID)
	more_menu.add_check_item("", CALM_ID)
	more_menu.add_check_item("", FULL_LISTEN_ID)
	more_menu.add_item("", MOD_ID)
	more_menu.id_pressed.connect(_on_menu)
	menu.add_child(more_menu)
	menu.add_item("", HELP_ID)
	menu.add_item("", 0)
	menu.add_item("", HIDE_ID)
	menu.add_submenu_node_item("", freq_menu, 1)
	menu.add_submenu_node_item("", lang_menu, 3)
	menu.add_submenu_node_item("", more_menu, MORE_ID)
	menu.add_separator()
	menu.add_item("", 2)
	menu.id_pressed.connect(_on_menu)
	add_child(menu)

	mic_on = cfg.get_value("prefs", "mic", true)
	full_listen = cfg.get_value("prefs", "full_listen", true)
	_mic_sent = mic_on
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
	link.disconnected.connect(func():
		listener_up = false
		_refresh_status())
	link.connected.connect(func():
		listener_up = true
		_refresh_status()
		_set_paused(null)  # the listener re-sends "paused" if a call is still on
		link.send({"type": "mic", "on": _mic_sent})
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
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_save()  # the jar's last minutes
	elif what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
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
	apprentice.bubble.close(true)  # typing comes first; a waiting note shows after
	text_box.visible = true
	text_box.grab_focus()
	_update_passthrough()


func _close_text_box() -> void:
	text_box.text = ""
	text_box.visible = false
	_update_passthrough()
	apprentice.bubble.flush()


func _on_text_submitted(t: String) -> void:
	if not listener_up and not t.strip_edges().is_empty():  # no nod for words nobody gets
		_close_text_box()
		apprentice.handle({"type": "say", "text": ui(lang, "no_listener")})
		return
	if apprentice.on_typed(t):
		jars.add(5)  # a typed line counts like a few seconds of talk
		typed.emit(t)
	_close_text_box()


func _on_text_box_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		_close_text_box()


func _on_menu(id: int) -> void:
	match id:
		0:
			mic_on = not mic_on
			_sync_mic()
			_save()
			_refresh_menu()
		2:
			_save()
			get_tree().quit()
		FULL_LISTEN_ID:
			full_listen = not full_listen
			_sync_mic()
			_save()
			_refresh_menu()
		MOD_ID:
			OS.shell_open(open_mods(Apprentice.mods()))
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
			_ask_hide(HIDE_SECONDS)
		MICPERM_ID:
			OS.shell_open("ms-settings:privacy-microphone")  # the user turns it on; we never change it
		BRAIN_ID:
			if brain == "no_model":
				pull_model.emit()  # the listener downloads it and tells progress in the bubble
			else:
				OS.shell_open("https://ollama.com/download")
				apprentice.handle({"type": "say", "text": ui(lang, "after_ollama")})


func _on_link_message(msg: Dictionary) -> void:
	_count_talk(str(msg.get("type", "")))
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
			_ask_hide(int(msg.get("seconds", HIDE_SECONDS)))
		"show":
			hidden_until = 0
			_update_visibility()
		"mic_blocked":
			_set_mic_blocked(bool(msg.get("blocked", false)))
		"no_mic":
			no_mic = bool(msg.get("none", false))
			_refresh_status()
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
	_layout()
	_update_passthrough()
	_save()
	_refresh_menu()


## Jars beside the apprentice, in its pixel size (a look can be 64 px at 2x or 48 px at 3x).
func _layout() -> void:
	var r := apprentice.sprite_rect()
	jars.px = apprentice.scale_px
	jars.jar_at = Vector2(r.position.x - 5 * jars.px - 6, r.end.y)
	jars.shelf_at = Vector2(r.end.x + 2, r.end.y)
	jars.queue_redraw()
	queue_redraw()


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
	more_menu.set_item_text(more_menu.get_item_index(MIC_ID), ui(lang, "microphone"))
	more_menu.set_item_text(more_menu.get_item_index(APPS_ID), ui(lang, "apps"))
	more_menu.set_item_text(more_menu.get_item_index(SKIN_ID), ui(lang, "skin"))
	for i in skins.size():
		var names: Array = SKIN_NAMES.get(lang, SKIN_NAMES["en"])
		skin_menu.set_item_text(i, names[i] if i < names.size() else str(skins[i]).trim_prefix("mod/"))
		skin_menu.set_item_checked(i, skins[i] == skin)
	more_menu.set_item_text(more_menu.get_item_index(PTT_ID), ptt_label(lang, ptt_name))
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
	more_menu.set_item_text(more_menu.get_item_index(MODEL_ID), ui(lang, "model"))
	menu.set_item_text(menu.get_item_index(HELP_ID), ui(lang, "help"))
	menu.set_item_text(menu.get_item_index(HIDE_ID), ui(lang, "hide"))
	more_menu.set_item_text(more_menu.get_item_index(CALM_ID), ui(lang, "calm"))
	more_menu.set_item_checked(more_menu.get_item_index(CALM_ID), apprentice.calm)
	more_menu.set_item_text(more_menu.get_item_index(MOD_ID), ui(lang, "mods"))
	menu.set_item_text(menu.get_item_index(MORE_ID), ui(lang, "settings"))
	if menu.get_item_index(STATUS_ID) >= 0:
		menu.set_item_text(menu.get_item_index(STATUS_ID), status_text(lang, listener_up, no_mic))
	more_menu.set_item_text(more_menu.get_item_index(FULL_LISTEN_ID), ui(lang, "full_listen"))
	more_menu.set_item_checked(more_menu.get_item_index(FULL_LISTEN_ID), full_listen)
	queue_redraw()  # the mic dot
	for i in MODELS.size():
		model_menu.set_item_text(i, model_label(lang, i))
		model_menu.set_item_checked(i, MODELS[i] == model)


func _save() -> void:
	cfg.set_value("win", "pos", get_window().position)
	cfg.set_value("prefs", "mic", mic_on)
	cfg.set_value("prefs", "full_listen", full_listen)
	cfg.set_value("prefs", "frequency", level)
	cfg.set_value("prefs", "lang", lang)
	cfg.set_value("prefs", "mic_device", mic_device)
	cfg.set_value("prefs", "skin", skin)
	cfg.set_value("prefs", "calm", apprentice.calm)
	cfg.set_value("prefs", "talk", jars.seconds)
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
	DisplayServer.window_set_mouse_passthrough(click_polygon(apprentice.sprite_rect().merge(jars.area()), top))


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
	_sync_mic()
	var hide := should_hide(full_rect, win.position, win.size, Time.get_ticks_msec(), hidden_until)
	if hide == not visible:
		return
	visible = not hide
	if hide and text_box.visible:
		_close_text_box()
	_update_passthrough()


## Is the mic wanted? Off when the user turned it off, or a fullscreen app is in front and the user
## chose not to be heard then ("Apprentice, hide" alone never stops listening).
static func wants_mic(on: bool, listen_full: bool, fullscreen: bool) -> bool:
	return on and (listen_full or not fullscreen)


func _sync_mic() -> void:
	var win := get_window()
	var want := wants_mic(mic_on, full_listen, should_hide(full_rect, win.position, win.size, 0, 0))
	if want != _mic_sent:
		_mic_sent = want
		mic_changed.emit(want)


func _mic_state() -> String:
	return mic_state(mic_on, paused_by, mic_blocked, listener_up, no_mic)


## "Hide for an hour" only while it can hear "come back": hidden, nothing on screen takes a click.
static func can_hide(state: String) -> bool:
	return state == "on"


func _ask_hide(seconds: int) -> void:
	if not can_hide(_mic_state()):
		apprentice.handle({"type": "say", "text": ui(lang, "hide_no")})
		return
	apprentice.bubble.show_text(ui(lang, "hide_bye"))  # the user just asked: replace any question
	get_tree().create_timer(3.0).timeout.connect(_hide_for.bind(seconds))  # time to read how to call it back


## Greyed-out top line when it can't hear at all; "" when all is well.
static func status_text(l: String, up: bool, none: bool) -> String:
	return ui(l, "no_listener") if not up else (ui(l, "no_mic") if none else "")


func _refresh_status() -> void:
	queue_redraw()
	var t := status_text(lang, listener_up, no_mic)
	var idx := menu.get_item_index(STATUS_ID)
	if t.is_empty():
		if idx >= 0:
			menu.remove_item(idx)
		return
	if idx < 0:
		menu.add_item("", STATUS_ID)
		idx = menu.get_item_index(STATUS_ID)
		menu.set_item_disabled(idx, true)
		menu.set_item_index(idx, 0)
	menu.set_item_text(menu.get_item_index(STATUS_ID), t)


## The small dot by the apprentice: "on" listening, "paused" (a call), "off" (mic off or blocked).
static func mic_state(on: bool, paused, blocked: bool, up := true, none := false) -> String:
	if not up:
		return "none"
	if not on or blocked or none:
		return "off"
	return "on" if paused == null else "paused"


const MIC_COLORS := {"on": Color("4caf50"), "paused": Color("d9a441"), "off": Color("c0392b"), "none": Color("8a8a8a")}


func _draw() -> void:
	var r := apprentice.sprite_rect()
	var p := Vector2(r.end.x - 9, r.end.y - 30)  # right of the cauldron, above the bench (free in both art sizes)
	var st := _mic_state()
	draw_circle(p, 7.0, Color("2a2230"))
	draw_circle(p, 5.5, MIC_COLORS[st])
	# a shape per state, not only a colour: dot = listening, bars = paused, X = off, dash = not running
	match st:
		"on":
			draw_circle(p, 2.0, Color.WHITE)
		"paused":
			draw_rect(Rect2(p + Vector2(-2.5, -3), Vector2(1.5, 6)), Color.WHITE)
			draw_rect(Rect2(p + Vector2(1, -3), Vector2(1.5, 6)), Color.WHITE)
		"off":
			draw_line(p + Vector2(-2.5, -2.5), p + Vector2(2.5, 2.5), Color.WHITE, 1.5)
			draw_line(p + Vector2(2.5, -2.5), p + Vector2(-2.5, 2.5), Color.WHITE, 1.5)
		"none":
			draw_line(p + Vector2(-3, 0), p + Vector2(3, 0), Color.WHITE, 1.5)


## Talking time fills the jar: from speech_start to the end of that sentence, at most a minute each.
func _count_talk(t: String) -> void:
	if t == "speech_start":
		_talk_from = Time.get_ticks_msec()
	elif t in ["speech_end", "question", "say"] and _talk_from > 0:
		jars.add(minf((Time.get_ticks_msec() - _talk_from) / 1000.0, 60.0))
		_talk_from = 0


## The user's own looks: folders in <mods>/looks with every needed strip, as "mod/<name>".
static func mod_looks(root: String) -> Array:
	var out := []
	var looks := root.path_join("looks")
	if not DirAccess.dir_exists_absolute(looks):
		return out
	for name in DirAccess.get_directories_at(looks):
		if LOOK_STRIPS.all(func(n): return FileAccess.file_exists(looks.path_join(name).path_join("apprentice_%s.png" % n))):
			out.append("mod/" + name)
	return out


## Makes the mod folder (with a how-to) the first time; returns its path for the file browser.
static func open_mods(root: String) -> String:
	for sub in ["looks", "questions/en", "questions/tr"]:
		DirAccess.make_dir_recursive_absolute(root.path_join(sub))
	var readme := root.path_join("README.txt")
	if not FileAccess.file_exists(readme):
		var f := FileAccess.open(readme, FileAccess.WRITE)
		f.store_string(MOD_README)
		f.close()
	return root


const MOD_README := """Çırak mod klasörü / Çırak mod folder

questions\\tr\\*.txt  ve/and  questions\\en\\*.txt
  Her satıra bir soru; # ile başlayan satırlar yok sayılır. Çırak soruların yaklaşık üçte birini bunlardan sorar.
  One question per line; lines starting with # are skipped. About one question in three comes from these.

looks\\<ad-name>\\apprentice_working.png, apprentice_listening.png, apprentice_nodding.png, apprentice_asking.png
  (+ isteğe bağlı/optional apprentice_toss.png)
  Kare karelerin (48x48 ya da 64x64) yan yana dizildiği şeritler, Çırak'ın kendi çizimleriyle aynı düzen.
  Yeni görünüm, Çırak'ı yeniden açınca menüde (Çırak) çıkar.
  Strips of square frames (48x48 or 64x64) side by side, the same layout as the built-in art.
  A new look shows in the menu (Apprentice) after you restart Çırak.
"""
