class_name Jars
extends Node2D
## Slow progress that can't be lost: talking fills a little jar; a full one goes on the shelf in a new
## colour and the next starts. No numbers, no streaks, never emptied.

signal filled  ## a jar just went on the shelf
signal stepped  ## the picture changed (worth saving)

const MINUTES := [10, 20, 30, 45, 60, 90]  ## talk per jar; every later jar takes the last
const SHELF := 6  ## jars shown on the shelf (2 rows of 3)
const PX := 3  ## one art pixel on screen, like the apprentice
const JAR := [".kkk.", "ogggo", "ohggo", "ogggo", "ogggo", "ogggo", ".ooo."]  ## 5x7, rows 1-5 hold liquid
const BREWS := [Color("7ad13a"), Color("3ac0b0"), Color("4a7be0"), Color("a35ce0"), Color("e05c9e"), Color("e0b030")]
const INK := {"k": Color("8a5a2b"), "o": Color("2a2230"), "g": Color(0.85, 0.93, 0.97, 0.45), "h": Color(1, 1, 1, 0.8)}
const PLANK := Color("6b4423")

var seconds := 0.0
var jar_at := Vector2.ZERO  ## bottom-left of the filling jar
var shelf_at := Vector2.ZERO  ## bottom-left of the shelf


## [full jars, how full the current one is (0..1)].
static func fill(s: float) -> Array:
	var full := 0
	while true:
		var need: float = MINUTES[mini(full, MINUTES.size() - 1)] * 60.0
		if s < need:
			return [full, s / need]
		s -= need
		full += 1
	return []


## Which jar numbers stand on the shelf: the last SHELF full ones.
static func shown(full: int) -> Array:
	return range(maxi(0, full - SHELF), full)


## Where the jars and shelf are drawn. The window's click region must cover it: on Windows that
## region also clips what is shown.
func area() -> Rect2:
	var top := shelf_at.y - 2 * (7 * PX + 2 * PX)
	return Rect2(jar_at.x, top, shelf_at.x + 3 * 5 * PX + 2 * PX - jar_at.x, shelf_at.y - top)


## Liquid rows (0..5) for a fraction.
static func rows(frac: float) -> int:
	return int(frac * 5.0)


func add(s: float) -> void:
	var was := fill(seconds)
	seconds += maxf(s, 0.0)
	var now := fill(seconds)
	if now[0] > was[0]:
		filled.emit()
	if now[0] != was[0] or rows(now[1]) != rows(was[1]):
		stepped.emit()
		queue_redraw()


func _draw() -> void:
	var f := fill(seconds)
	_jar(jar_at, BREWS[f[0] % BREWS.size()], rows(f[1]))
	var w := 5 * PX
	for i in 2:  # two planks, bottom row fills first
		draw_rect(Rect2(shelf_at + Vector2(0, -i * (7 * PX + 2 * PX) - PX), Vector2(3 * w + 2 * PX, PX)), PLANK)
	var jars := shown(f[0])
	for k in jars.size():
		var at := shelf_at + Vector2((k % 3) * (w + PX), -(k / 3) * (7 * PX + 2 * PX) - PX)
		_jar(at, BREWS[jars[k] % BREWS.size()], 5)


func _jar(bottom_left: Vector2, brew: Color, liquid: int) -> void:
	for y in JAR.size():
		for x in 5:
			var c: String = JAR[y][x]
			if c == ".":
				continue
			var col: Color = INK[c]
			if (c == "g" or c == "h") and y >= 6 - liquid:
				col = brew.lightened(0.45) if c == "h" else brew
			draw_rect(Rect2(bottom_left + Vector2(x * PX, (y - JAR.size()) * PX), Vector2(PX, PX)), col)
