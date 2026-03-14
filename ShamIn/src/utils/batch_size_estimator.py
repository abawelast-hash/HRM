"""Batch size estimator — adapted from ACTION-main."""
import torch


def estimate_batch_size(
    model,
    sample_input: dict,
    max_batch_size: int = 512,
    min_batch_size: int = 4,
    target_memory_fraction: float = 0.7,
) -> int:
    """
    Estimate the largest batch size that fits in GPU memory.

    Uses binary search approach: try progressively larger sizes,
    catch OOM, and return the largest that works.
    """
    if not torch.cuda.is_available():
        return min_batch_size

    device = torch.device("cuda")
    model = model.to(device)
    model.eval()

    torch.cuda.empty_cache()
    total_memory = torch.cuda.get_device_properties(0).total_mem
    target_memory = int(total_memory * target_memory_fraction)

    best_batch = min_batch_size
    current = min_batch_size

    while current <= max_batch_size:
        try:
            torch.cuda.empty_cache()
            batch = {
                k: v.repeat(current, *([1] * (v.dim() - 1))).to(device)
                if isinstance(v, torch.Tensor) else v
                for k, v in sample_input.items()
            }
            with torch.no_grad():
                _ = model(batch)

            used = torch.cuda.memory_allocated()
            if used < target_memory:
                best_batch = current
                current *= 2
            else:
                break
        except RuntimeError:
            break

    torch.cuda.empty_cache()
    return best_batch
