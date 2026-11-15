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
	for t in ["test_states", "test_blank_typed_ignored", "test_clamp_to_screen", "test_parse", "test_restore_on_second_monitor", "test_click_polygon", "test_relaunch", "test_ui_text", "test_toss", "test_pause_text", "test_mic_label", "test_stuck_connect"]:
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
