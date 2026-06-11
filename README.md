# TIF Folder Watchdog

Monitor numbered folders such as `r0009`, `r0010`, and later folders, then plot all `.tif` / `.tiff` files inside each folder as a single PNG summary figure.

## Install

```bash
pip install -r requirements.txt
```

## Run

Run with the default settings:

```bash
python watchdog.py
```

Common options:

```bash
python watchdog.py \
  --parent-folder ../extra_mmm_cache \
  --start-after r0034 \
  --poll-seconds 5 \
  --settle-seconds 30 \
  --colormap viridis \
  --png-output-folder ./pngs
```

For background execution:

```bash
nohup python watchdog.py --start-after r0034 --settle-seconds 30 > watch.log 2>&1 &
```

Stop it with:

```bash
ps aux | grep watchdog.py
kill <PID>
```

## Output

PNG summary figures are saved to:

```text
./pngs/
```
