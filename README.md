# TIF Folder Watchdog

Monitor numbered folders such as `r0009`, `r0010`, and later folders, then plot all `.tif` / `.tiff` files inside each folder as a single PNG summary figure.

## Install

```bash
pip install -r requirements.txt
```

## Run

Edit the configuration at the bottom of `watchdog.py`:

```python
watch_new_r_folders(
    parent_folder=Path("../extra_mmm_cache"),
    start_after="r0030",
    poll_seconds=5,
    settle_seconds=10,
    colormap=WATCH_COLORMAP,
)
```

Then run:

```bash
python watchdog.py
```

For background execution:

```bash
nohup python watchdog.py > watch.log 2>&1 &
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

