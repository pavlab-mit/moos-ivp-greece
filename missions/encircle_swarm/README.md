# encircle_swarm

Single-circle **swarm encircle** mission for the Hellenic Naval Academy basin,
Athens. Structure/geography cloned from `moos-ivp-greece/missions/alpha_greece`;
the spacing logic is `pEncircle` (`moos-ivp-swarm`).

Every vehicle loiters **one common circle**. `pEncircle` on each vehicle reads
the whole swarm's `NODE_REPORT`s and nudges each vehicle's loiter speed
(`LOITER_UPDATE = speed_alt`) so the ring spaces itself evenly. Because of that,
**as each vehicle is deployed it slots seamlessly into the ring and everyone
re-spaces** — no fixed slots, works for any number of vehicles.

A left-click posts a **goto task that the vehicles auction**: every vehicle bids
its distance to the clicked point (`BHV_TaskWaypoint` + `pTaskManager`), the
closest wins, leaves the ring to reach the point, and then rejoins the encircle.
The rest keep circling. `uFldTaskMonitor` shows the bidding in the appcast.

## Geography
- **Charts:** `moos_georef_20260616_081356.tif` (+ `.tfw`/`.info`/`.tif.moos`)
- **Encircle circle:** center `(-150, -30)`, radius `22` m — set in
  `launch_vehicle.sh` (Part 4c) and flowed to `meta_vehicle.{moos,bhv}` + the
  shoreside circle visual via nsplug. Clear of the three basin buoys.
- **Op-region:** box `pts={-205,12:-205,-80:-8,-80:-8,12}` (launch line + circle)

## Launch (SIM)
```bash
./launch.sh                  # 4 vehicles, warp 1
./launch.sh --amt=6 8        # 6 vehicles, warp 8
./launch.sh --amt=6 --stagger=15 8   # bring boats online 15s apart
./launch.sh --just_make      # build targ files only
```
Shoreside launches first, then the vehicles (MOOSDB 9001.. / pShare 9201..).
`--stagger=SECS` spaces the vehicle launches so you can watch each one join.

**BlueBoat (on the vehicle, identity auto-detected):** `./launch_vehicle.sh`

## Operating it (pMarineViewer)
- **DEPLOY** — deploy all online vehicles straight into the encircle (they join
  the ring). Press again after launching more vehicles to deploy the new ones.
- **ENCIRCLE** — (re)engage the encircle / `ENCIRCLE_ACTIVE`.
- **Left-click** — post a goto task; the closest vehicle is auctioned to it and
  then rejoins the ring.
- **RAD++ / RAD--** — grow/shrink the ring radius.
- **SPD_1.0 / SPD_1.8** — set the encircle group speed (`ENCIRCLE_GRP_SPEED`).
- **STATION / RETURN / ALLSTOP / TIMESTAMP**.

## How the seamless join works
On DEPLOY a vehicle enters `ENCIRCLE_MODE`; its `BHV_Loiter` acquires the common
circle and `pEncircle` (running on every vehicle) immediately accounts for the
new contact and re-computes everyone's spacing speed. Newly deployed vehicles
therefore fold into the ring with no per-vehicle slot assignment. Inter-vehicle
collisions during the join are handled by `BHV_AvdColregsV22`.

> Requires `pEncircle` (moos-ivp-swarm) on PATH.

## Structure
- `meta_vehicle.moos` / `meta_vehicle.bhv` — process list (incl. `pEncircle`) +
  behaviors (encircle / goto / station / return / avoidance / op-region)
- `meta_shoreside.moos` — pMarineViewer, brokers, circle-draw `uTimerScript`
- `plugs/shared|blueboat|shoreside/` — plug includes (incl. `plug_pEncircle.moos`)
- `targs/` — generated `targ_*.moos/.bhv` (nsplug output)
