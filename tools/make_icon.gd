## Writes the exe icon frames (first "listening" frame, pixel-sharp) as PNGs; tools/make_icon.py packs the .ico.
##   Godot --headless --path app -s ../tools/make_icon.gd -- <out dir>
extends SceneTree


func _init() -> void:
	var out: String = OS.get_cmdline_user_args()[0]
	var strip := Image.load_from_file(ProjectSettings.globalize_path("res://art/apprentice_listening.png"))
	var frame := strip.get_region(Rect2i(0, 0, 48, 48))
	for size in [256, 48, 32, 16]:
		var img := frame.duplicate()
		img.resize(size, size, Image.INTERPOLATE_NEAREST if size >= 48 else Image.INTERPOLATE_LANCZOS)
		img.save_png(out.path_join("icon_%d.png" % size))
	quit()
