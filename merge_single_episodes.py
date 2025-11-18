#!/usr/bin/env python

"""
Merge multiple single-episode datasets into one consolidated dataset.

This script finds all single-episode datasets in the specified directory
and merges them into a single multi-episode dataset using LeRobot's
dataset editing tools.

The merge process:
- Automatically discovers all episode datasets in the single_episodes folder
- Validates that each dataset contains exactly one episode
- Merges them sequentially while preserving episode order
- Creates a new consolidated dataset with all episodes

Usage:
    # Merge all episodes in the default directory
    python merge_single_episodes.py

    # Merge specific episodes
    python merge_single_episodes.py --episode_dirs "datasets/single_episodes/episode_20231115_120000" "datasets/single_episodes/episode_20231115_130000"

    # Specify custom output
    python merge_single_episodes.py --output_repo_id "your_username/merged_dataset" --output_root "./datasets/merged"

    # Push to HuggingFace Hub after merging
    python merge_single_episodes.py --push_to_hub
"""

import argparse
import logging
from pathlib import Path
from typing import List

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.dataset_tools import merge_datasets
from lerobot.utils.utils import init_logging


def find_single_episode_datasets(base_dir: Path) -> List[Path]:
    """
    Find all single-episode datasets in the specified directory.
    
    Args:
        base_dir: Base directory to search for episode datasets
        
    Returns:
        List of paths to episode dataset directories, sorted by name
    """
    if not base_dir.exists():
        logging.warning(f"Directory {base_dir} does not exist")
        return []
    
    episode_dirs = []
    for path in sorted(base_dir.iterdir()):
        if path.is_dir() and path.name.startswith("episode_"):
            # Check if it looks like a valid dataset (has meta/info.json)
            meta_file = path / "meta" / "info.json"
            if meta_file.exists():
                episode_dirs.append(path)
                logging.info(f"Found episode dataset: {path.name}")
            else:
                logging.warning(f"Skipping {path.name} - missing meta/info.json")
    
    return episode_dirs


def validate_single_episode_datasets(dataset_paths: List[Path]) -> List[LeRobotDataset]:
    """
    Load and validate that datasets contain single episodes.
    
    Args:
        dataset_paths: List of paths to dataset directories
        
    Returns:
        List of validated LeRobotDataset objects
    """
    datasets = []
    
    for path in dataset_paths:
        try:
            # Load dataset from local directory
            dataset = LeRobotDataset(
                repo_id=path.name,  # Use directory name as temp repo_id
                root=str(path.parent.absolute()),   # Absolute path to parent directory
            )
            
            # Validate it's a single episode
            if dataset.meta.total_episodes != 1:
                logging.warning(
                    f"Skipping {path.name} - contains {dataset.meta.total_episodes} episodes (expected 1)"
                )
                continue
            
            datasets.append(dataset)
            logging.info(
                f"Loaded {path.name}: {dataset.meta.total_frames} frames, "
                f"robot: {dataset.meta.robot_type}"
            )
            
        except Exception as e:
            logging.error(f"Failed to load dataset from {path}: {e}")
            continue
    
    return datasets


def merge_single_episodes(
    episode_dirs: List[Path],
    output_repo_id: str,
    output_root: Path,
    push_to_hub: bool = False,
) -> None:
    """
    Merge single-episode datasets into one consolidated dataset.
    
    Args:
        episode_dirs: List of paths to episode dataset directories
        output_repo_id: Repository ID for the merged dataset
        output_root: Root directory for the merged dataset
        push_to_hub: Whether to push the merged dataset to HuggingFace Hub
    """
    if not episode_dirs:
        logging.error("No episode datasets found to merge")
        return
    
    logging.info(f"Found {len(episode_dirs)} episode dataset(s) to merge")
    
    # Load and validate datasets
    datasets = validate_single_episode_datasets(episode_dirs)
    
    if not datasets:
        logging.error("No valid single-episode datasets found")
        return
    
    if len(datasets) == 1:
        logging.warning("Only one valid dataset found - nothing to merge")
        return
    
    logging.info(f"Merging {len(datasets)} episode(s) into {output_repo_id}")
    
    # Ensure output directory exists and use absolute path
    output_root = output_root.absolute()
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Merge datasets
    try:
        merged_dataset = merge_datasets(
            datasets=datasets,
            output_repo_id=output_repo_id,
            output_dir=str(output_root),
        )
        
        logging.info(f"✓ Successfully merged {len(datasets)} episodes")
        logging.info(f"  Total episodes: {merged_dataset.meta.total_episodes}")
        logging.info(f"  Total frames: {merged_dataset.meta.total_frames}")
        logging.info(f"  Dataset saved to: {output_root}")
        
        # Push to hub if requested
        if push_to_hub:
            logging.info(f"Pushing merged dataset to HuggingFace Hub as {output_repo_id}")
            LeRobotDataset(output_repo_id, root=str(output_root)).push_to_hub()
            logging.info("✓ Successfully pushed to Hub")
        
    except Exception as e:
        logging.error(f"Failed to merge datasets: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Merge single-episode datasets into one consolidated dataset"
    )
    parser.add_argument(
        "--episodes_dir",
        type=str,
        default="./datasets/single_episodes",
        help="Directory containing single-episode datasets (default: ./datasets/single_episodes)",
    )
    parser.add_argument(
        "--episode_dirs",
        type=str,
        nargs="+",
        help="Specific episode directories to merge (overrides auto-discovery)",
    )
    parser.add_argument(
        "--output_repo_id",
        type=str,
        default="your_username/merged_multi_arm_dataset",
        help="Repository ID for the merged dataset",
    )
    parser.add_argument(
        "--output_root",
        type=str,
        default="./datasets/merged",
        help="Root directory for the merged dataset (default: ./datasets/merged)",
    )
    parser.add_argument(
        "--push_to_hub",
        action="store_true",
        help="Push the merged dataset to HuggingFace Hub after merging",
    )
    
    args = parser.parse_args()
    
    # Initialize logging
    init_logging()
    
    # Determine which episode directories to use
    if args.episode_dirs:
        # Use specified directories
        episode_dirs = [Path(d) for d in args.episode_dirs]
        logging.info(f"Using {len(episode_dirs)} specified episode directories")
    else:
        # Auto-discover from episodes_dir
        base_dir = Path(args.episodes_dir)
        logging.info(f"Searching for episode datasets in: {base_dir}")
        episode_dirs = find_single_episode_datasets(base_dir)
    
    # Merge the datasets
    merge_single_episodes(
        episode_dirs=episode_dirs,
        output_repo_id=args.output_repo_id,
        output_root=Path(args.output_root),
        push_to_hub=args.push_to_hub,
    )


if __name__ == "__main__":
    main()
