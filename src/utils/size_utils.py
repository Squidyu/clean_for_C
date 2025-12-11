"""
Size Utilities

Utility functions for file size formatting, calculations, and conversions.
Provides consistent size handling throughout the application.
"""

from typing import Union, Tuple


def format_bytes(size_bytes: Union[int, float]) -> str:
    """
    Format byte size into human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.2 GB", "45.6 KB")
    """
    if size_bytes == 0:
        return "0 B"

    size = float(size_bytes)

    # Define units and their thresholds
    units = [
        ("B", 1),
        ("KB", 1024),
        ("MB", 1024**2),
        ("GB", 1024**3),
        ("TB", 1024**4),
        ("PB", 1024**5)
    ]

    # Find appropriate unit
    for unit, threshold in reversed(units):
        if size >= threshold:
            value = size / threshold
            if value >= 100:
                return f"{value:.0f} {unit}"
            elif value >= 10:
                return f"{value:.1f} {unit}"
            else:
                return f"{value:.2f} {unit}"

    # Fallback (should not reach here)
    return f"{size:.2f} B"


def parse_size_string(size_str: str) -> int:
    """
    Parse human-readable size string back to bytes.

    Args:
        size_str: Size string (e.g., "1.5 GB", "256 MB")

    Returns:
        Size in bytes

    Raises:
        ValueError: If string cannot be parsed
    """
    if not size_str or not size_str.strip():
        raise ValueError("Empty size string")

    # Normalize string
    size_str = size_str.strip().upper()

    # Handle plain numbers (assume bytes)
    if size_str.isdigit():
        return int(size_str)

    # Unit multipliers
    unit_multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5
    }

    # Extract number and unit
    import re
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]?B?)$', size_str)

    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    number_str, unit = match.groups()

    try:
        number = float(number_str)
    except ValueError:
        raise ValueError(f"Invalid number: {number_str}")

    # Handle abbreviated units (e.g., "K" -> "KB")
    if unit and not unit.endswith('B'):
        unit += 'B'

    multiplier = unit_multipliers.get(unit, 1)

    return int(number * multiplier)


def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """
    Calculate percentage safely.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage (0-100), or 0 if total is 0
    """
    try:
        if total == 0:
            return 0.0
        return min(100.0, max(0.0, (part / total) * 100.0))
    except (ZeroDivisionError, TypeError):
        return 0.0


def sum_sizes(*sizes: Union[int, float]) -> int:
    """
    Sum multiple sizes safely.

    Args:
        *sizes: Size values to sum

    Returns:
        Total size in bytes
    """
    total = 0
    for size in sizes:
        try:
            total += int(size)
        except (TypeError, ValueError):
            continue
    return total


def get_size_category(size_bytes: int) -> str:
    """
    Categorize file size.

    Args:
        size_bytes: File size in bytes

    Returns:
        Size category string
    """
    size_kb = size_bytes / 1024

    if size_kb < 100:  # < 100KB
        return "小文件"
    elif size_kb < 1024 * 10:  # < 10MB
        return "中等文件"
    elif size_kb < 1024 * 100:  # < 100MB
        return "大文件"
    elif size_kb < 1024 * 1000:  # < 1GB
        return "超大文件"
    else:  # >= 1GB
        return "巨型文件"


def format_size_with_category(size_bytes: int) -> str:
    """
    Format size with category information.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string with size and category
    """
    formatted_size = format_bytes(size_bytes)
    category = get_size_category(size_bytes)
    return f"{formatted_size} ({category})"


def compare_sizes(size1: Union[int, float], size2: Union[int, float]) -> int:
    """
    Compare two sizes.

    Args:
        size1: First size
        size2: Second size

    Returns:
        -1 if size1 < size2, 0 if equal, 1 if size1 > size2
    """
    try:
        s1 = float(size1)
        s2 = float(size2)

        if s1 < s2:
            return -1
        elif s1 > s2:
            return 1
        else:
            return 0
    except (TypeError, ValueError):
        return 0


def get_size_range_description(min_size: int, max_size: int) -> str:
    """
    Get description of a size range.

    Args:
        min_size: Minimum size in bytes
        max_size: Maximum size in bytes

    Returns:
        Human-readable range description
    """
    if min_size == max_size:
        return format_bytes(min_size)

    min_formatted = format_bytes(min_size)
    max_formatted = format_bytes(max_size)

    return f"{min_formatted} - {max_formatted}"


def estimate_cleanup_time(file_count: int, total_size: int) -> Tuple[float, str]:
    """
    Estimate time to clean up files.

    Rough estimation based on file count and size.

    Args:
        file_count: Number of files
        total_size: Total size in bytes

    Returns:
        Tuple of (estimated_seconds, description)
    """
    # Rough estimates:
    # - Small files (< 1MB): ~50ms per file
    # - Medium files (1MB-100MB): ~200ms per file
    # - Large files (>100MB): ~500ms per file
    # Plus overhead for directory operations

    avg_file_size = total_size / max(file_count, 1)

    if avg_file_size < 1024 * 1024:  # < 1MB
        time_per_file = 0.05
    elif avg_file_size < 100 * 1024 * 1024:  # < 100MB
        time_per_file = 0.2
    else:  # >= 100MB
        time_per_file = 0.5

    estimated_seconds = file_count * time_per_file + 1.0  # +1s overhead

    # Convert to readable format
    if estimated_seconds < 60:
        description = ".1f"
    elif estimated_seconds < 3600:
        description = ".1f"
    else:
        description = ".1f"
    return estimated_seconds, description


def validate_size(size: Union[int, float]) -> bool:
    """
    Validate that a size value is reasonable.

    Args:
        size: Size to validate

    Returns:
        True if size is valid and reasonable
    """
    try:
        size_float = float(size)
        # Reasonable limits: 0 to 10TB
        return 0 <= size_float <= 10 * 1024**4
    except (TypeError, ValueError):
        return False


def get_recommended_cleanup_threshold() -> int:
    """
    Get recommended cleanup threshold size.

    Returns:
        Size in bytes (default: 100MB)
    """
    # 100MB threshold for "large files" module
    return 100 * 1024 * 1024


def get_size_distribution_info(sizes: list) -> dict:
    """
    Analyze size distribution of a list of file sizes.

    Args:
        sizes: List of file sizes in bytes

    Returns:
        Dict with distribution statistics
    """
    if not sizes:
        return {
            'count': 0,
            'total': 0,
            'average': 0,
            'median': 0,
            'min': 0,
            'max': 0
        }

    sorted_sizes = sorted(sizes)
    count = len(sizes)
    total = sum(sizes)

    return {
        'count': count,
        'total': total,
        'average': total / count if count > 0 else 0,
        'median': sorted_sizes[count // 2] if count > 0 else 0,
        'min': sorted_sizes[0] if count > 0 else 0,
        'max': sorted_sizes[-1] if count > 0 else 0
    }