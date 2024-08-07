import numpy as np


def resize_array(array, target_shape=(64, 64)):
    """This is a util function to resize array to the target shape
    Args:
    array (NDArray): input array
    target_shape (tuple): output array's shape

    Returns:
    array (NDArray): output array with the target shape
    """
    target_height, target_width = target_shape
    input_height, input_width = array.shape

    # Crop if larger
    if input_height > target_height:
        start_h = (input_height - target_height) // 2
        array = array[start_h : start_h + target_height, :]
    if input_width > target_width:
        start_w = (input_width - target_width) // 2
        array = array[:, start_w : start_w + target_width]

    # Pad with zeros if smaller
    if input_height < target_height:
        pad_height = target_height - input_height
        pad_top = pad_height // 2
        pad_bottom = pad_height - pad_top
        array = np.pad(
            array,
            ((pad_bottom, pad_top), (0, 0)),
            mode="constant",
            constant_values=0.0,
        )

    if input_width < target_width:
        pad_width = target_width - input_width
        pad_right = pad_width // 2
        pad_left = pad_width - pad_right
        array = np.pad(
            array,
            ((0, 0), (pad_left, pad_right)),
            mode="constant",
        )
    return array


def make_anacal_peaks(x_center, y_center, is_peak=1, mask_value=0):
    """creates an AnaCal peak

    Args:
    x_center (int): center of the peak pixel in x
    y_center (int): center of the peak pixel in y
    is_peak (int): true peak (1) or artifact (0)
    mask_value (int): mask value quantifying whether the source is close to mask

    Returns:
    peaks (NDArray): AnaCal peak
    """
    data_type = [
        ("y", "i4"),
        ("x", "i4"),
        ("is_peak", "i4"),
        ("mask_value", "i4"),
    ]
    peaks = np.array(
        [(y_center, x_center, is_peak, mask_value)],
        dtype=data_type,
    )
    return peaks
