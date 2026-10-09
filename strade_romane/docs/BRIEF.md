# Scene briefs (visual → what to draw). Narration: testo/copione.json

The previous scene's road and the next one's are listed so the road-line morph reads as intentional.
All characters are original designs (no likeness of real people, no existing franchise characters).

## Group 1 — file `scene/b_appia.py`
- **appio** (b03): the road is a straight horizon again. Rome on the left (a few line-art temples, a
  little hill with columns), the Samnite mountains far right (jagged peaks, small helmets/spears
  peeking = war). Appio Claudio (omino "toga", expr proud→talk) stands centre-left; a lightbulb-free
  "idea" moment: he unrolls a scroll with a plan; a straight dashed line draws from Rome toward
  Capua (small town label "Capua"). Handwritten "312 a.C." and "Via Appia" appear on cue. Joke at the
  end: on "il Cieco" his eyes close (expr squint) while he points confidently far away, and a tiny
  telescope-free gag: the line he points along goes exactly straight to the horizon. Road: straight
  horizon y≈790 from x=-60..1980.
- **regina** (b04): the road keeps going: camera feeling of travelling south; a long road snakes from
  left to right through hills to a little port (Brindisi: boats, waves) at the right; a handwritten
  "regina viarum" with a small crown drawn above the road; "Roma → Brindisi · oltre 500 km". At the end
  a tiny UNESCO-like laurel/badge doodle (no logo; just a laurel wreath and "2024"). Road: gently winding
  line ending at the port.
- **groma** (b05): close-ish shot: the agrimensore (omino "agrimensore", hold "groma", expr squint)
  sighting along the groma; plumb lines sway; a helper far away holds a pole (another small omino);
  sight-lines draw as dashed lines; then a straight road grows along them ("circa 60 km in rettilineo",
  "Paludi Pontine → Terracina"); on "sapevano anche curvare" a mountain appears and the line bends
  gracefully around it. Road: starts straight, ends with a curve around the mountain.

## Group 2 — file `scene/c_cantiere.py`
- **cantiere** (b06): THE cross-section. Start as a landscape; the ground "opens" (camera feeling of
  going underground): a trench outline, then layers fill in one by one from the bottom as hatched
  line textures: big stones (rounded outlines), gravel (small dots/circles), finer gravel, then the top:
  polygonal basalt blocks (basoli) fitted together, with a slight crown (camber) and side ditches;
  raindrops roll off to the sides on "la pioggia scivoli via". Labels handwritten: "pietre", "ghiaia",
  "pietrisco", "basoli". Two or three legionaries/workers (omino legionario / operaio with pick, shovel)
  work above the trench with nice loops of motion (digging cycle), one wipes his forehead.
  Road: the top surface of the road in section (crowned line across the screen).
- **tavole** (b07): a bronze-tablet-like rectangle drawn with hatched lines and "XII" at the top; text
  lines appear as squiggles; then a top view of the road: a straight section labelled "8 piedi" with a
  measuring arrow, and a curve labelled "16 piedi" wider; a little two-wheeled cart drives through the
  curve and fits (with a relieved mule face). Road: the centre line of the plan-view road (straight,
  then curved).
- **miliario** (b08): roadside, a tall cylindrical milestone draws on, with a carved inscription
  (line squiggles) and a big Roman numeral "MP XII" style; the traveller walks by counting paces
  ("mille passi" with a tally); a measuring chain "≈ 1,5 km". Then the Miliarium Aureum: a golden
  milestone in the Forum, drawn with extra glow lines (still white), with many roads converging on it
  from all directions. Road: horizon road, which at the end becomes several lines converging to a point.
- **posta** (b10): a relay station (small building with a sign "mutatio"), a courier (omino corriere)
  arrives at a gallop on a horse (draw a stylised line-art horse with a looping gallop), swaps horse,
  rides on; an inn ("mansio") with a sleepy guest; a counter "≈ 50 miglia al giorno". Then the Tiberius
  record: a fast carriage with speed lines crossing mountains (Alps) day→night (sun → moon arc), label
  "200 miglia · un giorno e una notte". Road: horizon road that rises over mountains at the end.

## Group 3 — file `scene/d_rete.py`
- **rete** (b09): MAP VIEW. The horizon road morphs into the Via Appia on a line-art map of Italy and
  the Mediterranean (coastlines). Use real coordinates: download Natural Earth 110m or 50m land/coastline
  GeoJSON (e.g. from github.com/nvkelso/natural-earth-vector, public domain) once into assets/ and project
  equirectangular around lon 2..30, lat 34..48. Roads draw on in order with handwritten labels: Appia
  (Roma–Capua–Benevento–Taranto–Brindisi), Flaminia (Roma–Rimini), Aurelia (Roma–Pisa–Genova along the
  Tyrrhenian), Emilia (Rimini–Bologna–Piacenza; label "Emilia" with a little arrow to the region),
  Domitia (from the Alps via Nîmes/Narbonne to the Pyrenees), Egnatia (Durrës–Thessaloniki–Byzantium).
  Cities as small dots with handwritten names. Road: the Appia polyline on the map.
- **tabula** (b11): travellers on the road (soldier, merchant with cart, pilgrim, the traveller and
  mule) flowing past; a scroll unrolls very long across the screen showing a stylised, stretched map
  with wavy roads and little town symbols (inspired by the Peutinger map's strip format, drawn
  originally); a medieval monk (omino monaco) copying it with a quill; label "Tabula Peutingeriana ·
  ~6,75 m · Vienna". Road: a long wavy line across the scroll.
- **ponti** (b12): a river with flowing ripple lines; a multi-arch stone bridge draws on (five arches,
  like Rimini's), people cross it today (a modern omino with a bicycle doodle is fine); label "Ponte di
  Tiberio · Rimini · 21 d.C.". Then a gorge with steep rock walls and a tunnel portal cut in the rock;
  a little modern car drives into the tunnel: label "Galleria del Furlo · 76 d.C." Road: crosses the bridge
  deck, then enters the tunnel.
- **mondo** (b13): zoom out: the road becomes part of a dense web of thin lines over the map of the
  empire (procedural network seeded from the main roads), counter "≈ 300.000 km"; then a globe (circle
  with a few meridians/parallels) and the line wraps around it more than seven times (a spiral that
  loops round), "> 7 volte il giro della Terra"; then most of the web fades to dotted/uncertain lines
  except a few solid ones: "tracciato esatto noto: ~3%". Road: the spiral/circle line around the globe.
