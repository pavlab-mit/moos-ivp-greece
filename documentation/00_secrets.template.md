---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Credentials — Template

This file lists every credential placeholder referenced in the documentation.
Real values are **not** stored here.

To populate real values, copy this file to `00_secrets.md` (which is
gitignored) and fill in the `Value` column. Operators get the real values
from the project's secret-distribution mechanism (1Password, USB key, trusted
operator hand-off, etc.).

> **Critical.** `00_secrets.md` must never be committed. The repository's
> `.gitignore` excludes it; do not override that.

---

## 1. How Placeholders Work

Documents reference credentials by handlebar key — for example:

```bash
ssh pi@10.1.0.31
# password: {{PI_FIELD_PASSWORD}}
```

The operator resolves `{{PI_FIELD_PASSWORD}}` against `00_secrets.md` at
read-time. No real password ever appears in a committed file.

---

## 2. Frontseat (Raspberry Pi)

| Key | Used in | Description | Value |
|---|---|---|---|
| `PI_DEFAULT_PASSWORD` | `13_frontseat_first_boot.md` | Factory default for the `pi` user on a fresh Raspberry Pi OS image. Changed immediately after first boot. | _(populate in 00_secrets.md)_ |
| `PI_FIELD_PASSWORD` | `13_frontseat_first_boot.md`, `16_software_build.md`, `30_field_operations.md` | The `pi` user password set during first boot. Used for routine SSH access to a boat. | _(populate in 00_secrets.md)_ |
| `PI_WIFI_AP_PASSWORD` | `13_frontseat_first_boot.md` | WPA2-PSK for each boat's onboard Wi-Fi AP (`<vname>-bb` SSID). Currently open; populate if/when authentication is enabled. | _(populate in 00_secrets.md)_ |

## 3. DoodleLabs Radios

| Key | Used in | Description | Value |
|---|---|---|---|
| `RADIO_WEBGUI_PASSWORD` | `12_doodle_labs_radio.md` | MeshRider Web GUI login for both Wearable and Mini-OEM radios. Vendor default. | _(populate in 00_secrets.md)_ |
| `RADIO_SSH_PASSWORD` | `12_doodle_labs_radio.md` | Root SSH access to a DoodleLabs radio. Default empty; document target value if changed. | _(populate in 00_secrets.md)_ |
| `RADIO_MESH_ID` | `12_doodle_labs_radio.md`, `01_fleet_and_network_reference.md` | Identifier shared by every radio on the Greece mesh. Not strictly secret, but parameterized for clean rollover. | _(populate in 00_secrets.md)_ |
| `RADIO_MESH_PASSWORD` | `12_doodle_labs_radio.md` | WPA2-PSK securing the Greece radio mesh. | _(populate in 00_secrets.md)_ |
| `RADIO_WIFI_AP_PASSWORD` | `12_doodle_labs_radio.md` | Wearable's Wi-Fi AP password (for laptops/tablets joining the Wearable's 5 GHz AP). | _(populate in 00_secrets.md)_ |

## 4. Shoreside Infrastructure

| Key | Used in | Description | Value |
|---|---|---|---|
| `SHORE_RB5009_PASSWORD` | `02_shoreside_infrastructure.md` | Admin password for the Mikrotik RB5009 router (RouterOS, user `admin`). | _(populate in 00_secrets.md)_ |
| `SHORE_WAPAX_PASSWORD` | `02_shoreside_infrastructure.md` | Admin password for the Mikrotik wAP ax access point. | _(populate in 00_secrets.md)_ |
| `SHORESIDE_WIFI_PASSWORD` | `02_shoreside_infrastructure.md` | WPA2-PSK for the `Shoreside-5GHz` and `Shoreside-2GHz` field Wi-Fi networks. | _(populate in 00_secrets.md)_ |
| `SHORE_DOODLE_WEBGUI_PASSWORD` | `02_shoreside_infrastructure.md` | MeshRider Web GUI login for the shoreside DoodleLabs Wearable at 10.1.0.3. Usually identical to `RADIO_WEBGUI_PASSWORD`; tracked separately in case it diverges. | _(populate in 00_secrets.md)_ |

## 5. Repository / Deploy Keys

| Key | Used in | Description | Value |
|---|---|---|---|
| `MOOS_IVP_BLUEBOAT_DEPLOY_KEY` | `16_software_build.md` | Fleet-wide, read-only SSH deploy key for `moos-ivp-blueboat` (one per repo, shared across all boats — not per-boat). Stored as a private/public pair; the public half is added read-only to the repo's Deploy keys, the private half goes on every boat. | _(populate in 00_secrets.md)_ |
| `MOOS_IVP_GREECE_DEPLOY_KEY` | `16_software_build.md` | Fleet-wide, read-only SSH deploy key for `moos-ivp-greece` (one per repo, shared across all boats — not per-boat). | _(populate in 00_secrets.md)_ |

## 6. NTRIP / GPS Corrections (Future)

| Key | Used in | Description | Value |
|---|---|---|---|
| `NTRIP_USERNAME` | `14_um982_gps.md` | NTRIP caster username when RTK corrections are added. | _(populate in 00_secrets.md)_ |
| `NTRIP_PASSWORD` | `14_um982_gps.md` | NTRIP caster password. | _(populate in 00_secrets.md)_ |

---

## 7. Adding a New Placeholder

When you introduce a new credential into a doc:

1. Add a row to the appropriate section above.
2. Use the `UPPER_SNAKE_CASE` convention for the key.
3. Briefly describe what the credential protects and where it's used.
4. Leave the `Value` column as `_(populate in 00_secrets.md)_` in the
   template.
5. In your local `00_secrets.md`, fill in the real value.

If a credential rotates, only `00_secrets.md` needs to change — no doc edits
required.
