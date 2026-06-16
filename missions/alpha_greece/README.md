# survey_athens

Canonical BlueBoat baseline mission for the Hellenic Naval Academy basin, Athens.
Behaviorally derived from `moos-ivp-seascout/missions/sensor_spec_survey`; geography
(origin, charts, op-region, static obstacle) from `moos-ivp-greece/missions/rescue_athens`.

This is a **goto / loiter / station / return** mission with static-obstacle avoidance,
COLREGS contact avoidance, and op-region containment. It is **not** a lawnmower survey
and has no commander (`cmd=`) control menu.

## Geography
- **Origin:** LatOrigin `37.9325`, LongOrigin `23.6251`
- **Charts:** `plugs/shoreside/athens_hgoo_20.tif` (default) + `athens_thgoo_20.tif` (toggle with `` ` ``)
- **Op-region:** `pts={60,10:-75.54,-54.26:-36.99,-135.58:98.55,-71.32}`
- **Static obstacle:** heptagon centered near `(7, 71)`

## Launch

**SIM:**
```bash
./launch.sh                       # vname=asha, warp 1
./launch.sh 8                     # warp 8
```

**BlueBoat (on the vehicle, identity auto-detected from IP):**
```bash
./launch_vehicle.sh               # XMODE=BBOAT; get_robot_info_greece.sh sets vname/ip/fseat/color
```
Fleet (IP → name): `10.31.1.100 asha`, `10.32 bama`, `10.33 chip`, `10.34 dale`, `10.35 ewan`, `10.36 flex`.

> Requires the moos-ivp-seascout app stack (iBackSeatBroker, pBB_DGPS_EKF, iOmniScan450SS,
> iTracker650, iHBK_CV7, iNucleus1000, pAUV_EKF, ...) and `get_robot_info_greece.sh` on PATH.
>
> The backseat broker (`plug_iBackSeatBroker.moos`) forwards helm/state vars
> `IVPHELM_STATE, MODE, DEPLOY` (and `MISSION_COMPLETE`, `ALL_STOP`, thrust) to the front
> seat via `tx_vars`, so the front seat can mirror back-seat autonomy state.

## Shoreside controls (pMarineViewer buttons)
- **DEPLOY** — deploy and hold station at the launch position (default on deploy)
- **GOTO** — go to a left-clicked point
- **LOITER** — fly the loiter circle; **RAD++ / RAD--** grow/shrink its radius by 5 m
- **STATION** / **RETURN** / **ALLSTOP**
- **TIMESTAMP** — inert log marker; posts `TIMESTAMP_FLAG`, bridged to all vehicles and logged on
  both shoreside and vehicle (a manual timestamp you can grep for in the alogs)
- **SPD_0.8 / SPD_1.5** — set goto/loiter speed
- Left-click sets the active behavior's point (goto / station / loiter center)

## Fleet start positions
SIM/return positions for the a-f fleet are assigned in `launch_vehicle.sh`, evenly spaced
`(93,96)→(73,76)`: asha `93,96`, bama `89,92`, chip `85,88`, dale `81,84`, ewan `77,80`,
flex `73,76`. Override per-launch with `--start_pos=X,Y`.

## Modes
`AUTONOMY_MODE` (GOTO/LOITER) + `RETURN`/`STATION_KEEP` flags drive helm modes
GOTO_MODE / LOITER_MODE / STATION_MODE / RETURN_MODE. On DEPLOY, `STATION_KEEP`
initializes true → the vehicle holds station until commanded otherwise.

## Structure
- `meta_vehicle.moos` / `meta_vehicle.bhv` — vehicle process list + behaviors
- `meta_shoreside.moos` — shoreside (pMarineViewer, brokers, collision detect)
- `plugs/shared|blueboat|shoreside|bhvs/` — plug includes
- `targs/` — generated `targ_*.moos/.bhv` (nsplug output)
