from math import ceil
from pathlib import Path
import argparse
import re
import time

import matplotlib.pyplot as plt
import numpy as np
import tifffile as tiff


def pick_display_plane(array, band=0):
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

    return pick_display_plane(arr, band=band)


def robust_limits(array, lower=2, upper=98):
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


def plot_tif_folder(
    tif_folder=Path("../extra_mmm_cache/r0034"),
    colormap="viridis",
    png_output_folder=Path("./pngs"),
    flip_up_down=True,
    show_figure=False,
):
    """Plot all TIF files in a folder and save the figure as a PNG."""
    tif_folder = Path(tif_folder)
    png_output_folder = Path(png_output_folder)
    png_output_folder.mkdir(parents=True, exist_ok=True)

    tif_files = sorted(
        list(tif_folder.glob("*.tif")) + list(tif_folder.glob("*.tiff"))
    )

    if not tif_folder.exists():
        raise FileNotFoundError(f"Folder not found: {tif_folder.resolve()}")

    if not tif_files:
        raise FileNotFoundError(f"No .tif or .tiff files found in: {tif_folder.resolve()}")

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
        tif_display = pick_display_plane(tif_img, band=0)

        if flip_up_down:
            tif_display = np.flipud(tif_display)

        if tif_display.ndim == 3 and tif_display.shape[-1] in (3, 4):
            ax.imshow(tif_display)
        else:
            vmin, vmax = robust_limits(tif_display)
            image = ax.imshow(
                tif_display,
                cmap=colormap,
                vmin=vmin,
                vmax=vmax,
            )
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

        ax.set_title(tif_path.name, fontsize=9)
        ax.set_xlabel("X pixel")
        ax.set_ylabel("Y pixel")
        ax.tick_params(axis="both", which="both", labelsize=8)

    for ax in axes.ravel()[n_files:]:
        ax.axis("off")

    fig.suptitle(f"TIF files in {tif_folder}", fontsize=14)
    plt.tight_layout()

    png_output_path = png_output_folder / f"{tif_folder.name}.png"
    fig.savefig(png_output_path, dpi=200, bbox_inches="tight")
    if show_figure:
        plt.show()
    else:
        plt.close(fig)

    print(f"Displayed {n_files} TIF file(s).")
    print(f"Saved PNG figure to: {png_output_path}")

    return png_output_path


def r_folder_number(folder):
    """Return the numeric part of an r-folder name such as r0001, or None."""
    match = re.fullmatch(r"r(\d{4,})", folder.name)
    if match is None:
        return None
    return int(match.group(1))


def watch_new_r_folders(
    parent_folder=Path("../extra_mmm_cache"),
    start_after="r0000",
    poll_seconds=5,
    settle_seconds=30,
    colormap="viridis",
    png_output_folder=Path("./pngs"),
    flip_up_down=True,
):
    """Monitor for r-folders and plot all TIF files inside each detected folder."""
    parent_folder = Path(parent_folder)
    start_number = r_folder_number(Path(start_after))
    plotted = set()
    reported_waiting = set()

    if start_number is None:
        raise ValueError("start_after must look like 'r0000', 'r0008', or 'r0034'.")

    print(f"Watching for r-folders after {start_after} in: {parent_folder.resolve()}")
    print("Stop monitoring with Ctrl+C.")

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

                print(f"Plotting folder: {folder}")
                plot_tif_folder(
                    tif_folder=folder,
                    colormap=colormap,
                    png_output_folder=png_output_folder,
                    flip_up_down=flip_up_down,
                    show_figure=False,
                )
                plotted.add(folder)

            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        print("Monitoring stopped.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Monitor r-folders and save PNG summary figures for TIF files."
    )
    parser.add_argument(
        "--parent-folder",
        default="../extra_mmm_cache",
        help="Parent folder containing r0001, r0002, ... folders.",
    )
    parser.add_argument(
        "--start-after",
        default="r0000",
        help="Only process folders with a number greater than this value.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=5,
        help="Seconds between checks for new folders.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=30,
        help="Seconds to wait after TIF files first appear before plotting.",
    )
    parser.add_argument(
        "--colormap",
        default="viridis",
        help='Matplotlib colormap, for example "gray", "viridis", "turbo", or "inferno".',
    )
    parser.add_argument(
        "--png-output-folder",
        default="./pngs",
        help="Folder where PNG summary figures will be saved.",
    )
    parser.add_argument(
        "--no-flip-up-down",
        action="store_true",
        help="Disable upside-down flipping of each image.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    watch_new_r_folders(
        parent_folder=Path(args.parent_folder),
        start_after=args.start_after,
        poll_seconds=args.poll_seconds,
        settle_seconds=args.settle_seconds,
        colormap=args.colormap,
        png_output_folder=Path(args.png_output_folder),
        flip_up_down=not args.no_flip_up_down,
    )
