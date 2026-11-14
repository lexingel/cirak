extends SceneTree

const ApprenticeScene = preload("res://apprentice.tscn")
const MainScript = preload("res://main.gd")

var failures := 0


func check(cond: bool, what: String) -> void:
	if not cond:
		failures += 1
		printerr("FAIL: ", what)


func _initialize() -> void:
	_run.call_deferred()  # nodes added inside _initialize don't get _ready yet


func _run() -> void:
	for t in ["test_states", "test_blank_typed_ignored", "test_clamp_to_screen"]:
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
