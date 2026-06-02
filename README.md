# moos-ivp-greece

Code and missions for the 2026 Summer Course.

## Directory Structure

| Directory | Description |
|:-- |:-- |
| `bin` | Generated executable files |
| `build` | Build object files |
| `lib` | Generated behavior libraries |
| `missions` | Mission files |
| `scripts` | Project scripts |
| `src` | Source code |

## Build

This repository uses the default MOOS-IvP extension layout and expects a
`moos-ivp` checkout in a nearby sibling or parent directory.

Build from the repository root:

```bash
./build.sh
```

## Environment

Add this repository's `bin` and `scripts` directories to `PATH`, and add its
`lib` directory to `IVP_BEHAVIOR_DIRS` so pAntler and the IvP Helm can find
project binaries and behaviors.
