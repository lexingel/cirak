class_name Link
extends Node
## Starts the Python listener and talks to it over a local websocket. Fails quietly.

signal message(msg: Dictionary)
signal connected

const URL := "ws://127.0.0.1:47613"
const RETRY_SECONDS := 2.0
const CONNECT_TIMEOUT := 3.0  ## a connect to a dead port can hang in SYN_SENT forever on Windows
const BYE_WAIT_MS := 3000
const RELAUNCH_SECONDS := 10.0  ## backoff, so a listener that keeps dying (no mic) is not hammered

var _ws := WebSocketPeer.new()
var _pid := -1
var _retry := 0.0
var _was_open := false
var _since_launch := 0.0
var _connecting := 0.0


static func parse(text: String) -> Dictionary:
	var j := JSON.new()
	if j.parse(text) != OK or typeof(j.data) != TYPE_DICTIONARY or not j.data.has("type"):
		return {}
	return j.data


static func connect_stuck(seconds_connecting: float) -> bool:
	return seconds_connecting >= CONNECT_TIMEOUT


static func needs_relaunch(running: bool, seconds_since_launch: float) -> bool:
	return not running and seconds_since_launch >= RELAUNCH_SECONDS


func _ready() -> void:
	_launch()


func _launch() -> void:
	_since_launch = 0.0
	# editor run: app/ next to listener/; dev build: build/Cirak.exe next to listener/;
	# release zip: Cirak.exe with listener/ inside its own folder
	var base := ProjectSettings.globalize_path("res://") if OS.has_feature("editor") else OS.get_executable_path().get_base_dir()
	var listener := base.path_join("listener")
	if not FileAccess.file_exists(listener.path_join("main.py")):
		listener = base.path_join("../listener").simplify_path()
	# a release ships its own Python next to the code; a dev checkout uses the venv
	var py := listener.path_join("python/pythonw.exe")
	if not FileAccess.file_exists(py):
		py = listener.path_join(".venv/Scripts/pythonw.exe")
	if not FileAccess.file_exists(py):
		# no venv -> a bare system Python would crash on every relaunch; stay quiet instead
		push_warning("listener venv not found: " + py)
		_pid = -1
		return
	_pid = OS.create_process(py, [listener.path_join("main.py")])


func _process(delta: float) -> void:
	_ws.poll()
	var st := _ws.get_ready_state()
	if st == WebSocketPeer.STATE_CONNECTING:
		_connecting += delta
		_since_launch += delta
		if connect_stuck(_connecting):
			_ws = WebSocketPeer.new()  # drop it; the CLOSED branch retries and relaunches if needed
		return
	_connecting = 0.0
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
		_stop_listener()


## Ask the listener to close its mic and leave; a hard kill mid-stream once took a USB audio
## interface (and its USB controller) down. Kill only if it hangs.
func _stop_listener() -> void:
	if _pid <= 0:
		return
	if _ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		_ws.send_text(JSON.stringify({"type": "bye"}))
		var until := Time.get_ticks_msec() + BYE_WAIT_MS
		while OS.is_process_running(_pid) and Time.get_ticks_msec() < until:
			_ws.poll()
			OS.delay_msec(50)
		if OS.is_process_running(_pid):
			OS.kill(_pid)  # it got "bye" and still hangs
	# not connected: leave it; it quits on its own (cleanly) after 10 s without the app
	_pid = -1
