extends SceneTree

const ApprenticeScene = preload("res://apprentice.tscn")
const MainScript = preload("res://main.gd")
const LinkScript = preload("res://link.gd")

var failures := 0


func check(cond: bool, what: String) -> void:
	if not cond:
		failures += 1
		printerr("FAIL: ", what)


func _initialize() -> void:
	_run.call_deferred()  # nodes added inside _initialize don't get _ready yet


func _run() -> void:
	for t in ["test_states", "test_blank_typed_ignored", "test_clamp_to_screen", "test_parse", "test_restore_on_second_monitor", "test_click_polygon", "test_relaunch", "test_ui_text", "test_toss", "test_pause_text", "test_mic_label", "test_stuck_connect", "test_small_polish", "test_say", "test_command_menu", "test_skins"]:
		call(t)
	print("tests done, failures: ", failures)
	quit(1 if failures else 0)


func new_apprentice():
	var a = ApprenticeScene.instantiate()
	root.add_child(a)
	return a


func test_states() -> void:
	var a = new_apprentice()
	check(a.state == a.State.WORKING, "starts working")
	check(a.sprite.sprite_frames.get_frame_count("working") >= 2, "working strip loaded")
	a.handle({"type": "speech_start"})
	check(a.state == a.State.LISTENING, "speech_start -> listening")
	a.handle({"type": "question", "text": "Takıldığın yer neresi?"})
	check(a.state == a.State.ASKING, "question -> asking")
	check(a.bubble.visible and a.bubble.text() == "Takıldığın yer neresi?", "bubble shows question")
	a.handle({"type": "paused", "reason": "call"})
	check(a.state == a.State.WORKING, "paused -> working")
	a.handle({"type": "nonsense"})
	check(a.state == a.State.WORKING, "unknown message ignored")


func test_blank_typed_ignored() -> void:
	var a = new_apprentice()
	check(a.on_typed("   ") == false and a.state == a.State.WORKING, "blank typed ignored")
	check(a.on_typed("menüyü yapıyorum") == true and a.state == a.State.NODDING, "typed -> nodding")


func test_clamp_to_screen() -> void:
	var r := Rect2i(0, 0, 1920, 1080)
	check(MainScript.clamp_to_screen(Vector2i(3000, 50), Vector2i(260, 220), r) == Vector2i(1660, 50), "clamp right edge")
	check(MainScript.clamp_to_screen(Vector2i(100, 100), Vector2i(260, 220), r) == Vector2i(100, 100), "inside unchanged")
	check(MainScript.clamp_to_screen(Vector2i(-500, -40), Vector2i(260, 220), r) == Vector2i(0, 0), "clamp top-left")


func test_parse() -> void:
	check(LinkScript.parse('{"type":"question","text":"Ne var?"}').get("text") == "Ne var?", "parse question")
	check(LinkScript.parse("bozuk{") == {}, "bad json -> empty")
	check(LinkScript.parse('{"text":"tipsiz"}') == {}, "no type -> empty")
	check(LinkScript.parse('[1,2]') == {}, "non-object -> empty")


func test_restore_on_second_monitor() -> void:
	var screens := [Rect2i(0, 0, 2560, 1440), Rect2i(2560, 0, 1920, 1080)]
	check(MainScript.restore_pos(Vector2i(3000, 500), Vector2i(260, 220), screens) == Vector2i(3000, 500), "stays on monitor 2")
	check(MainScript.restore_pos(Vector2i(9000, 500), Vector2i(260, 220), screens) == Vector2i(2300, 500), "gone monitor -> pulled onto first")


func test_click_polygon() -> void:
	var sprite := Rect2(58, 76, 144, 144)
	var only := MainScript.click_polygon(sprite, Rect2())
	check(only.size() == 4, "sprite only: a box")
	var poly := MainScript.click_polygon(sprite, Rect2(12, 4, 236, 50))
	check(Geometry2D.is_point_in_polygon(Vector2(20, 20), poly), "bubble area catches clicks")
	check(Geometry2D.is_point_in_polygon(Vector2(130, 150), poly), "sprite catches clicks")
	check(not Geometry2D.is_point_in_polygon(Vector2(5, 210), poly), "empty corner passes through")


func test_relaunch() -> void:
	check(LinkScript.needs_relaunch(false, 12.0), "dead listener relaunched after backoff")
	check(not LinkScript.needs_relaunch(false, 3.0), "not hammering")
	check(not LinkScript.needs_relaunch(true, 60.0), "running listener left alone")


func test_ui_text() -> void:
	check(MainScript.TEXT["en"].keys() == MainScript.TEXT["tr"].keys(), "both languages have every label")
	check(MainScript.ui("en", "close") == "Close" and MainScript.ui("tr", "close") == "Kapat", "label lookup")
	check(MainScript.ui("xx", "close") == "Close", "unknown language -> English")


func test_toss() -> void:
	var a = new_apprentice()
	check(a.sprite.sprite_frames.get_frame_count("toss") == 10, "toss strip loaded")
	check(a.toss() and a.sprite.animation == "toss" and a.state == a.State.WORKING, "toss plays while working")
	a._on_anim_finished()
	check(a.sprite.animation == "working", "back to stirring after toss")
	a.toss()
	a.handle({"type": "speech_start"})
	check(a.sprite.animation == "listening", "talking interrupts a toss")
	check(not a.toss() and a.sprite.animation == "listening", "no toss unless working")
	check(a.toss_timer.wait_time >= 45.0, "toss is rare")


func test_pause_text() -> void:
	check(MainScript.pause_text("en", "Discord.exe") == "Listening paused (Discord.exe)", "pause line names the app")
	check(MainScript.pause_text("tr", "Discord.exe") == "Dinleme duraklatıldı (Discord.exe)", "pause line in Turkish")
	check(MainScript.pause_text("en", "") == "Listening paused", "no name -> plain line")


func test_mic_label() -> void:
	check(MainScript.mic_label("en", "") == "Windows default", "empty mic = Windows default")
	check(MainScript.mic_label("tr", "") == "Windows varsayılanı", "default in Turkish")
	check(MainScript.mic_label("en", "Mikrofon (USB 2.0 Camera)") == "Mikrofon (USB 2.0 Camera)", "mic shown by name")


func test_stuck_connect() -> void:
	check(not LinkScript.connect_stuck(1.0), "a fresh connect attempt is left alone")
	check(LinkScript.connect_stuck(LinkScript.CONNECT_TIMEOUT), "a connect hanging this long is dropped")


func test_small_polish() -> void:
	check(Bubble.show_seconds("Which color?") >= 6.0, "short question still stays readable")
	check(Bubble.show_seconds("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen") > 10.0, "long question stays longer")
	var a = new_apprentice()
	check(a.ANIMS[a.State.NODDING][1] <= 4.0, "nod slow enough to be seen")
	a._on_loop()
	check(a.sprite.speed_scale >= 0.9 and a.sprite.speed_scale <= 1.1, "stirring tempo wobbles a little")
	a.handle({"type": "speech_start"})
	check(a.sprite.speed_scale == 1.0, "other poses at normal speed")


func test_say() -> void:
	var a = new_apprentice()
	a.handle({"type": "say", "text": "Sonraki şarkı"})
	check(a.state == a.State.NODDING, "a done command nods, no question pose")
	check(a.bubble.visible, "and shows what it did")


func test_command_menu() -> void:
	var m = MainScript.new()
	check(MainScript.ui("tr", "apps").begins_with("Açabileceğim"), "app list menu text")
	check(MainScript.ptt_label("en", "").contains("Right Ctrl"), "command key defaults to Right Ctrl")
	check(MainScript.ptt_label("tr", "F8").contains("F8"), "command key line names the picked key")
	check(MainScript.brain_text("tr", "no_ollama", "").contains("Ollama"), "menu offers Ollama when it is missing")
	check(MainScript.brain_text("en", "no_model", "qwen2.5:3b").contains("2 GB"), "menu offers the chosen model's download with its size")
	check(MainScript.brain_text("en", "ok", "qwen2.5:3b") == "", "no line when questions come from the model")
	check(MainScript.MODELS == ["qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b"], "the listener's model choices")
	for l in ["en", "tr"]:
		for i in MainScript.MODELS.size():
			var t: String = MainScript.model_label(l, i)
			check(t.begins_with(MainScript.MODELS[i]) and t.contains("GB"), "%s model line %d names it, its size and a note" % [l, i])
	check(MainScript.ui("tr", "mic_blocked").contains("Ayarlar"), "blocked mic line says where to fix it")
	check(MainScript.ui("en", "first_hint").contains("Right-click"), "first start tells where the menu is")
	m.free()


func test_skins() -> void:
	for s in MainScript.SKINS:
		var a = new_apprentice()
		a.set_skin(s)
		for spec in a.ANIMS.values() + [a.TOSS]:
			check(a.sprite.sprite_frames.get_frame_count(spec[0]) >= 2, "%s has %s frames" % [s, spec[0]])
	check(MainScript.SKIN_NAMES["tr"].size() == MainScript.SKINS.size(), "every look has a Turkish name")
	for s in MainScript.SKINS:
		var icon: Texture2D = Apprentice.preview(s)
		check(icon != null and icon.get_width() == Apprentice.FRAME, "look %s has a menu icon" % s)
	check(Apprentice.preview("missing") != null, "a missing look falls back to the wizard's icon")
	var a3 = new_apprentice()
	a3.set_skin("missing")
	check(a3.skin == "" and a3.sprite.sprite_frames.get_frame_count("working") >= 2, "a missing look is the wizard, never invisible")
	check(MainScript.SKIN_NAMES["en"].size() == MainScript.SKINS.size(), "every look has an English name")
	var a2 = new_apprentice()
	a2.handle({"type": "speech_start"})
	a2.set_skin("okcu")
	check(a2.state == a2.State.LISTENING and a2.sprite.animation == "listening", "pose survives a change of clothes")
