from math import ceil
from pathlib import Path
import re
import time

from IPython.display import display
import matplotlib.pyplot as plt
import numpy as np
import tifffile as tiff


# Change the colormap here if needed, for example: "gray", "viridis", "turbo", "inferno".
WATCH_COLORMAP = "viridis"

# Folder for saved PNG figures.
WATCH_PNG_OUTPUT_FOLDER = Path("./pngs")
WATCH_PNG_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


def pick_display_plane_for_watch(array, band=0):
    """Select a displayable 2D plane from a 2D, 3D, or higher-dimensional TIF."""
    arr = np.asarray(array)

    if arr.ndim == 2:
        return arr

    if arr.ndim == 3:
        if arr.shape[-1] in (3, 4):
            return arr

        band = int(np.clip(band, 0, arr.shape[0] - 1))
        return arr[band]

    while arr.ndim > 3:
        arr = arr[0]

    return pick_display_plane_for_watch(arr, band=band)


def robust_limits_for_watch(array, lower=2, upper=98):
    """Use percentiles to improve contrast and reduce the effect of extreme values."""
    arr = np.asarray(array)

    if arr.ndim == 3 and arr.shape[-1] in (3, 4):
        return None, None

    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None, None

    vmin, vmax = np.percentile(finite, [lower, upper])
    if vmin == vmax:
        return None, None

    return vmin, vmax


def plot_tif_folder_for_watch(folder, colormap=WATCH_COLORMAP, output_folder=WATCH_PNG_OUTPUT_FOLDER):
    """Plot all TIF files in one folder, save the figure as PNG, and return the figure."""
    folder = Path(folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    tif_files = sorted(list(folder.glob("*.tif")) + list(folder.glob("*.tiff")))

    if not tif_files:
        print(f"No .tif or .tiff files found in: {folder.resolve()}")
        return None

    n_files = len(tif_files)
    n_cols = min(4, n_files)
    n_rows = ceil(n_files / n_cols)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(4 * n_cols, 4 * n_rows),
        squeeze=False,
    )

    for ax, tif_path in zip(axes.ravel(), tif_files):
        tif_img = tiff.imread(tif_path)
        tif_display = pick_display_plane_for_watch(tif_img, band=0)

        if tif_display.ndim == 3 and tif_display.shape[-1] in (3, 4):
            ax.imshow(tif_display)
        else:
            vmin, vmax = robust_limits_for_watch(tif_display)
            image = ax.imshow(tif_display, cmap=colormap, vmin=vmin, vmax=vmax)
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

        ax.set_title(tif_path.name, fontsize=9)
        ax.axis("off")

    for ax in axes.ravel()[n_files:]:
        ax.axis("off")

    fig.suptitle(f"TIF files in {folder}", fontsize=14)
    plt.tight_layout()
    png_output_path = output_folder / f"{folder.name}.png"
    fig.savefig(png_output_path, dpi=200, bbox_inches="tight")
    print(f"Saved PNG figure to: {png_output_path}")
    return fig


def r_folder_number(folder):
    """Return the numeric part of an r-folder name such as r0009, or None."""
    match = re.fullmatch(r"r(\d{4,})", folder.name)
    if match is None:
        return None
    return int(match.group(1))


def watch_new_r_folders(
    parent_folder=Path("../extra_mmm_cache"),
    start_after="r0008",
    poll_seconds=5,
    settle_seconds=30,
    colormap=WATCH_COLORMAP,
):
    """Monitor for new r-folders and plot all TIF files inside each new folder."""
    parent_folder = Path(parent_folder)
    start_number = r_folder_number(Path(start_after))
    plotted = set()
    reported_waiting = set()

    if start_number is None:
        raise ValueError("start_after must look like 'r0008'.")

    print(f"Watching for new folders after {start_after} in: {parent_folder.resolve()}")
    print("Stop monitoring with Kernel > Interrupt, or press the stop button in JupyterLab.")

    try:
        while True:
            if not parent_folder.exists():
                print(f"Parent folder does not exist yet: {parent_folder.resolve()}")
                time.sleep(poll_seconds)
                continue

            candidates = []
            for folder in parent_folder.iterdir():
                if not folder.is_dir() or folder in plotted:
                    continue

                number = r_folder_number(folder)
                if number is not None and number > start_number:
                    candidates.append((number, folder))

            for _, folder in sorted(candidates):
                tif_files = sorted(list(folder.glob("*.tif")) + list(folder.glob("*.tiff")))
                if not tif_files:
                    if folder not in reported_waiting:
                        print(f"\nNew folder detected, waiting for TIF files: {folder}")
                        reported_waiting.add(folder)
                    continue

                print(f"\nNew TIF files detected in: {folder}")
                print(f"Waiting {settle_seconds} seconds before plotting, so late files can arrive...")
                time.sleep(settle_seconds)

                print(f"Plotting new folder: {folder}")
                fig = plot_tif_folder_for_watch(folder, colormap=colormap)
                if fig is not None:
                    display(fig)
                    plt.close(fig)
                    plotted.add(folder)

            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        print("Monitoring stopped.")


# Run this cell to start monitoring.
watch_new_r_folders(
    parent_folder=Path("../extra_mmm_cache"),
    start_after="r0030",
    poll_seconds=5,
    settle_seconds=10,
    colormap=WATCH_COLORMAP,
)
