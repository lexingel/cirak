class_name Link
extends Node
## Starts the Python listener and talks to it over a local websocket. Fails quietly.

signal message(msg: Dictionary)
signal connected

const URL := "ws://127.0.0.1:47613"
const RETRY_SECONDS := 2.0
const RELAUNCH_SECONDS := 10.0  ## backoff, so a listener that keeps dying (no mic) is not hammered

var _ws := WebSocketPeer.new()
var _pid := -1
var _retry := 0.0
var _was_open := false
var _since_launch := 0.0


static func parse(text: String) -> Dictionary:
	var j := JSON.new()
	if j.parse(text) != OK or typeof(j.data) != TYPE_DICTIONARY or not j.data.has("type"):
		return {}
	return j.data


static func needs_relaunch(running: bool, seconds_since_launch: float) -> bool:
	return not running and seconds_since_launch >= RELAUNCH_SECONDS


func _ready() -> void:
	_launch()


func _launch() -> void:
	_since_launch = 0.0
	var listener := ProjectSettings.globalize_path("res://").path_join("../listener").simplify_path()
	var py := listener.path_join(".venv/Scripts/pythonw.exe")
	if not FileAccess.file_exists(py):
		py = "pythonw"
	_pid = OS.create_process(py, [listener.path_join("main.py")])


func _process(delta: float) -> void:
	_ws.poll()
	var st := _ws.get_ready_state()
	if st == WebSocketPeer.STATE_OPEN:
		if not _was_open:
			_was_open = true
			connected.emit()
		while _ws.get_available_packet_count() > 0:
			var msg := parse(_ws.get_packet().get_string_from_utf8())
			if not msg.is_empty():
				message.emit(msg)
	elif st == WebSocketPeer.STATE_CLOSED:
		_was_open = false
		_since_launch += delta
		if needs_relaunch(_pid > 0 and OS.is_process_running(_pid), _since_launch):
			_launch()
		_retry -= delta
		if _retry <= 0.0:
			_retry = RETRY_SECONDS
			_ws = WebSocketPeer.new()
			_ws.connect_to_url(URL)


func send(msg: Dictionary) -> void:
	if _ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		_ws.send_text(JSON.stringify(msg))


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_PREDELETE:
		if _pid > 0:
			OS.kill(_pid)
			_pid = -1
