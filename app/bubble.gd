class_name Bubble
extends PanelContainer
## Speech bubble: shows a question for a while, then fades out. A note ("say") that arrives while a
## question is up waits its turn instead of wiping the question away.

signal closed

const FADE_SECONDS := 0.5

var _label := Label.new()
var _tween: Tween
var _question := false
var _queue: Array = []


func _ready() -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = Color("f6eedb")  # warm paper: no white glare over a dark game
	box.border_color = Color("2a2230")
	box.set_border_width_all(2)
	box.set_corner_radius_all(8)
	box.set_content_margin_all(9)
	box.shadow_color = Color(0, 0, 0, 0.25)
	box.shadow_size = 2
	add_theme_stylebox_override("panel", box)
	_label.add_theme_color_override("font_color", Color("2a2230"))
	_label.add_theme_font_size_override("font_size", 15)
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.custom_minimum_size.x = 220
	add_child(_label)
	visible = false


## Long questions stay up longer: 6 s plus time to read each word.
static func show_seconds(t: String) -> float:
	return 6.0 + 0.4 * t.split(" ", false).size()


func text() -> String:
	return _label.text


func show_text(t: String, question := false) -> void:
	_question = question
	_label.text = t
	modulate.a = 1.0
	visible = true
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_interval(show_seconds(t))
	_tween.tween_property(self, "modulate:a", 0.0, FADE_SECONDS)
	_tween.tween_callback(close)


## A note: shown now, or after the question on screen is gone.
func say(t: String) -> void:
	if visible and _question:
		_queue.append(t)
	else:
		show_text(t)


## keep: the user opened the text box; waiting notes show after it (flush), not on top of it.
func close(keep := false) -> void:
	if _tween:
		_tween.kill()
	visible = false
	closed.emit()
	if not keep:
		flush()


## The user spoke after the question: what comes next answers them, so it may replace it.
func release() -> void:
	_question = false


func flush() -> void:
	if not visible and not _queue.is_empty():
		show_text(_queue.pop_front())
