# Printing and building the 1:6 model

The model is a working miniature. The back flexes, the desktop slides toward and away from the seat, and the post changes height. It prints in plain PLA on any normal FDM printer with a 0.4 mm nozzle and a 200 x 200 mm bed. No slicer supports, no screws, and no glue unless you want the chair permanent.

Finished size is about 15 x 10 x 14.5 cm (6 x 4 x 5.7 in), which fits in one hand.

## What to print

Open one of these in your slicer (Bambu Studio, OrcaSlicer, PrusaSlicer and Cura all read 3MF):

| file | filament | parts |
|---|---|---|
| `print/DELTA_1-6_BLACK_plate.3mf` | black PLA | seat shell, left frame, right frame |
| `print/DELTA_1-6_WHITE_plate.3mf` | white PLA | floor base, lower post sleeve, upper post + head, desktop, track end plug |

Every part is already turned the right way up and placed inside the bed with room for brims. If your slicer asks whether to keep the parts' orientation, say yes. The single parts are also in `print/stl/`, numbered in assembly order.

`print/DELTA_1-6_assembled_preview.3mf` is the finished model put together, for looking at, not printing.

If you have grey filament, the floor base, post sleeve and post head are the parts that are grey on the real desk.

## Slicer settings

These are ordinary PLA settings; only the items marked "important" matter much.

- Layer height 0.16 mm for the black plate (the grip ribs on the back come out crisper); 0.2 mm is fine for the white plate.
- Walls: 3. Top and bottom layers: 4.
- Infill 15-20 %, any pattern.
- Supports: **off** (important). The one place that needs holding up has its own snap-off fin built into the seat's file.
- Brim: 5 mm on the **seat shell** and on the **lower post sleeve** (important). The shell prints standing on its side and only touches the bed along thin edges. The sleeve prints standing up, 93 mm tall on a tiny footprint. Frames, base, head and desktop don't need one.
- Elephant-foot compensation 0.15-0.2 mm if your slicer has it. The press-fit joints are sized for it.
- Print the seat shell and the sleeve a little slower than usual (outer walls around 40-60 mm/s), because they're tall and thin while printing.

Your slicer will give the real print time. As a rough guide, the whole kit is under 130 g of PLA and takes somewhere around 6-9 hours in total.

The end plug is tiny (about 2 x 8 x 2 mm). Print a spare or two if you can; it's the part that disappears into the carpet.

## After printing

- **Seat shell:** a thin fin hangs down from the lower edge of the backrest, where the back curves in at the waist. It's there so that edge doesn't print in mid-air. Snap it off with pliers and clean the edge with a craft knife or a bit of sandpaper.
- Peel the brims off the shell and sleeve.

## Pins

The two pins are short pieces of ordinary 1.75 mm filament, which is why there's no pin STL:

- **Height pin:** about 15 mm long. Goes front to back through the lower sleeve and the upper post, with a little sticking out on each side.
- **Reach pin:** about 8 mm long. Goes up from underneath through the round boss on the head and into the desktop.

Cut the ends at a slight angle with flush cutters so they start into the holes easily. Cut a spare of each. Both holes are slightly tight on purpose so the pins stay put: if a pin won't go in, twist it in rather than pushing, or open the hole with a 2 mm drill bit turned by hand.

## Assembly

Do it on a flat table.

1. **Base.** Put the white floor base down flat, with the T-foot (the end with the square socket) away from you.
2. **Frames.** Each black triangle has a small notch at the bottom of its inner face, near the front foot. Lower each frame straight down so the notch drops over the tab on the end of the base's cross bar. The flat, smooth face goes outward. The frames now stand on their own but can still lift off.
3. **Seat.** The seat shell has a socket under each side. Line them up with the little tabs on top of the triangles and press the seat straight down until it seats. Now the frames are locked: they can't spread apart or fall inward. If it's too tight, sand the tab faces lightly rather than forcing it.
4. **Sleeve.** Press the lower post sleeve into the square socket on the T-foot. The end with the pin hole goes **up**.
5. **Desktop onto the head.** Hold the head (the white L-shaped part) and the desktop upside down. The dovetail slot under the desktop is open at the far edge. Slide the long end of the head's dovetail into that opening and push it along the slot until the round boss sits under one of the four holes.
6. **End plug.** Press the end plug into the open end of the slot, flush with the desktop's far edge. It stops the desktop sliding off the head. A drop of glue here is fine; you won't need to take the desktop off again.
7. **Reach pin.** Push the 8 mm pin up through the round boss into the desktop hole above it.
8. **Post into sleeve.** Lower the head's post into the sleeve. Line up one of its five holes with the sleeve's hole and push the 15 mm pin through, front to back.

Steps 2 and 3 hold without glue. If you want the chair part permanent, a drop of CA glue on the frame tabs in step 3 does it.

## Using it

- **Desk height:** pull the height pin, move the desktop up or down a hole (each hole is 1 inch on the real desk), put the pin back. With the pin out, the post can't drop below the lowest setting.
- **Desk reach:** pull the reach pin from underneath, slide the desktop toward or away from the seat to the next hole, put the pin back. The four holes are the four reach settings.
- **Flexing back:** push the top of the backrest with a fingertip. It gives a few degrees and springs back, like the real chair. A firm push is fine; don't try to fold it flat. PLA is much stiffer and more brittle than the polypropylene the real chair would use, so treat the flex as a demonstration.

## If something doesn't fit

Printers differ by a tenth of a millimetre or two, and that matters at this size.

- **Joint too tight:** sand the tab, not the socket. For the post, sand its flat faces lightly or run a file down the inside of the sleeve.
- **Joint too loose:** a layer of tape or a dab of glue on the tab.
- **Desktop won't slide:** the dovetail slot's first layers can squash slightly. Run a craft knife along the inside edges of the slot and turn on elephant-foot compensation next time.
- **End plug won't go in:** sand its sides; it's meant to be a firm push.
- **Seat shell came loose from the bed:** use a wider brim (8 mm) and a clean bed. The shell only touches the bed along its side edge by design, because printing it on its side is what lets the back flex without cracking.
- **Rough underside along the seat's lower edge:** the edge that curls toward the bed is a steep overhang for its first few millimetres. A light sanding cleans it up.

## Why the parts print the way they do

- The **seat shell prints on its side** so that bending the backrest bends along the printed lines. Printed upright, the back would snap between layers the first time you pushed it.
- The **frames print flat with the inner face down**, so the outer faces, the ones you see, get the smooth top finish.
- The **lower post sleeve prints standing up**, so its bore is a clean vertical tube with no bridged ceiling for the post to catch on.
- The **post head prints on its side** so the post's layers run along its length. That makes it strong against the desktop pushing on it, and the 45 degree dovetail prints cleanly that way.
- The **desktop prints upside down** so the writing surface gets the smooth bed finish, and the dovetail slot opens upward, where it prints without support.

A few details differ from the full-size design so the model prints cleanly. The seat's side edges curl down 45 degrees instead of all the way to vertical (a vertical curl would overhang when the shell prints on its side). The back's wrap is gentler, so the small PLA back visibly flexes. The under-seat ribs and the hidden seat beam of the real chair are left off, because the model doesn't need them. The model's frames lock into the base and seat with tabs; the real ones bolt together.
