class_name Bubble
extends PanelContainer
## Speech bubble: shows a question for a while, then fades out.

signal closed

const FADE_SECONDS := 0.5

var _label := Label.new()
var _tween: Tween


func _ready() -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = Color(1, 1, 1, 0.96)
	box.set_corner_radius_all(10)
	box.set_content_margin_all(8)
	box.shadow_color = Color(0, 0, 0, 0.3)
	box.shadow_size = 3
	add_theme_stylebox_override("panel", box)
	_label.add_theme_color_override("font_color", Color("2a2230"))
	_label.add_theme_font_size_override("font_size", 14)
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.custom_minimum_size.x = 220
	add_child(_label)
	visible = false


## Long questions stay up longer: 6 s plus time to read each word.
static func show_seconds(t: String) -> float:
	return 6.0 + 0.4 * t.split(" ", false).size()


func text() -> String:
	return _label.text


func show_text(t: String) -> void:
	_label.text = t
	modulate.a = 1.0
	visible = true
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_interval(show_seconds(t))
	_tween.tween_property(self, "modulate:a", 0.0, FADE_SECONDS)
	_tween.tween_callback(close)


func close() -> void:
	if _tween:
		_tween.kill()
	visible = false
	closed.emit()
