import numpy as np
import numba as nb

@nb.njit
def get_tou_info(month: int, hour: int, schedule: np.array, struct: np.array):
    """Returns the rate information for the supplied TOU.

    :param month: Integer in the range [1,12] representing the month.
    :param hour: Integer in the range [0,23] representing the hour of the day.
    :param schedule: A Numpy array containing the time of use period indexes.
    :param struct: A Numpy array containing the associated rate information.
    :returns: A Numpy array of the are information for the current month and hour.
            The array will have a minimum length of 1.
            Returns *None* if either **struct** or **schedule** are *None*.
    :raises IndexError: If either **month** or **hour** are out of range.
    """
    if month < 1 or month > 12 or hour < 0 or hour > 23:
        raise IndexError

    if not schedule or not struct:
        return None
        
    return struct[schedule[month - 1:hour]]

@nb.njit
def get_flat_month(month: int, schedule: np.array, struct: np.array):
    """Returns rate information for a flat month.

    :param month: Integer in the range [1,12] representing the month.
    :param schedule: A Numpy array containing the time of use period indexes.
    :param struct: A Numpy array containing the associated rate information.
    :returns: A Numpy array of the are information for the current month and hour.
            The array will have a minimum length of 1.
            Returns *None* if either **struct** or **schedule** are *None*.
    :raises IndexError: If **month** is out of range.
    """

    if month < 1 or month > 12:
        raise IndexError

    if not schedule or not struct:
        return None

    return struct[schedule[month - 1]]