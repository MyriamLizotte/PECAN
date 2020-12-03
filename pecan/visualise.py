"""Visualise output of condensation process."""

import argparse

import matplotlib.collections
import matplotlib.lines
import matplotlib.animation as animation
import matplotlib.pyplot as plt

import numpy as np

from utilities import parse_keys
from utilities import make_tensor


def get_limits(X):
    """Calculate plotting limits of input tensor."""
    x = np.asarray(X[:, 0, ...]).flatten()
    y = np.asarray(X[:, 1, ...]).flatten()

    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)

    return x_min, x_max, y_min, y_max


def update(i):
    scatter.set_offsets(X[..., i])

    # Figure out all intervals to draw here
    values = [destruction for _, destruction in pd if destruction <= i]

    segments = [
        [(0, i), (destruction, i)] for i, destruction in enumerate(values)
    ]

    barcode.set_segments(segments)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('INPUT')
    parser.add_argument('-r', '--repeat', action='store_true')

    args = parser.parse_args()

    # Load data and check whether all keys are available. We require
    # only the diffusion homology pairs and the data set here.
    data = np.load(args.INPUT)
    parsed_keys = parse_keys(data)

    assert 'data' in parsed_keys, 'Require "data" key'

    assert 'diffusion_homology_persistence_pairs' in parsed_keys, \
        'Require "diffusion_homology_persistence_pairs" key'

    X = make_tensor(data, parsed_keys['data'])
    T = X.shape[-1]

    # Plot dynamic point cloud first. This assumes that only two
    # dimensions are available; higher-dimensional data may need
    # an additional dimensionality reduction step before-hand.
    fig, ax = plt.subplots(ncols=2)

    x_min, x_max, y_min, y_max = get_limits(X)

    ax[0].set_xlim((x_min, x_max))
    ax[0].set_ylim((y_min, y_max))

    # Render first time step before the animation starts.
    scatter = ax[0].scatter(X[:, 0, 0], X[:, 1, 0])

    # Set up the diffusion homology pairing. This just amounts to
    # accessing the distribution of pairs and turning them into a
    # barcode visualisation.

    # List of persistence pairs of the form (creation, destruction). An
    # optional third dimension is ignored.
    pd = data['diffusion_homology_persistence_pairs']

    ax[1].set_xlim(0, np.max(pd[:, 1]))     # Length of longest bar
    ax[1].set_ylim(0, len(pd[:, 1]))        # How many bars?

    barcode = matplotlib.collections.LineCollection(segments=[])
    ax[1].add_collection(barcode)

    # Basic animation setup; it will loop over all the frames in the
    # data set and depict the corresponding topological features in
    # a barcode plot.

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=T,
        repeat=args.repeat,
    )

    plt.show()
