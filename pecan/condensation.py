"""Topology-based diffusion condensation scheme."""

import argparse
import datetime
import logging
import os
import sys

import numpy as np

import data

from callbacks import CalculateBifiltration
from callbacks import CalculateDiffusionHomology
from callbacks import CalculatePersistentHomology

from functor import DiffusionCondensation
from kernels import get_kernel_fn

from utilities import estimate_epsilon
from utilities import generate_output_filename


if __name__ == '__main__':

    # Set up logging to obtain some nice output information, runtime,
    # and much more.
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d  [%(levelname)-10s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--callbacks',
        default=None,
        nargs='+',
        help='Specifies names for callbacks to use. The full callback class '
             'name must be provided.'
    )

    parser.add_argument(
        '-d', '--data',
        default='hyperuniform_ellipse',
        type=str,
        help='Select data set generator routine or filename to load.'
    )

    parser.add_argument(
        '-n', '--num-samples',
        default=128,
        type=int
    )

    parser.add_argument(
        '-e', '--epsilon',
        # TODO: ensure that this makes sense and be adjusted more
        # easily, depending on the number of points etc.
        default=np.nan,
        type=float,
    )

    parser.add_argument(
        '-k', '--kernel',
        default='gaussian',
        type=str,
        choices=['alpha', 'gaussian', 'laplacian', 'constant', 'box'],
        help='Sets kernel to use for diffusion condensation process.'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='If set, overwrites existing output files.'
    )

    parser.add_argument(
        '-o', '--output',
        default='.',
        type=str,
        help='Output directory (meaning that the filename will be '
             'generated automatically) or output filename.'
    )

    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=None,
        help='Set random seed to ensure reproducibility.'
    )

    parser.add_argument(
        '--noise',
        type=float,
        default=0.0,
        help='Noise level to add to the data set'
    )

    parser.add_argument(
        '-b', '--beta',
        default=1.0,
        type=float,
        help='Beta parameter for distributions. Will be used whenever '
             'it is appropriate.'
    )

    parser.add_argument(
        '-r',
        default=0.5,
        type=float,
        help='Inner radius for annuli and related data sets. Will be used '
             'whenever it is appropriate.'
    )

    parser.add_argument(
        '-R',
        default=1.0,
        type=float,
        help='Outer radius for annuli and related data sets. Will be used '
             'whenever it is appropriate.'
    )

    parser.add_argument(
        '-K',
        default=0.0,
        type=float,
        help='Curvature for sampling points on disks of const. curvature. Will be used '
             'whenever it is appropriate.'
    )


    parser.add_argument(
        '-a', '--alpha',
        default=1.0,
        type=float,
        help='Alpha parameter for the weight given to the memory of previous operators. By default 1.'
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    if args.seed is None:
        # Not the best way to seed the random generator, but this
        # ensures that we obtain different results per run.
        seed = int(datetime.datetime.now().timestamp())
    else:
        seed = args.seed

    # Client specified a file instead of generator function. Let's use
    # this. The unfortunate issue with this is that generators must be
    # named differently than files...
    if os.path.isfile(args.data):
        X = np.loadtxt(args.data)
    else:
        # Search for a generator routine, as requested by the client. This
        # does not fail gracefully.
        generator = getattr(data, args.data)

        logging.info(f'Using generator routine {generator}')

        X, C = generator(
            args.num_samples,
            random_state=seed,
            r=args.r,
            R=args.R,
            K=args.K,
            beta=args.beta,
        )

    if np.isnan(args.epsilon):
        args.epsilon = estimate_epsilon(X)

        logging.info(
            f'Epsilon parameter has not been set. Estimating '
            f'it as {args.epsilon:.4f}.'
        )

    if args.noise > 0.0:
        X += args.noise * np.random.uniform(size=X.shape)

    logging.info(f'Data set: {args.data}')
    logging.info(f'Number of samples: {args.num_samples}')
    logging.info(f'Epsilon: {args.epsilon:.4f}')

    # User specified an existing directory, so we generate a filename
    # automatically and store everything in it.
    if os.path.isdir(args.output):
        # Store data set. The name of output file is generated automatically
        # to account for conditions of the environment.

        output_filename = generate_output_filename(args, seed)
        output_filename = os.path.join(args.output, output_filename)

    # Just use the user-provided output path.
    else:
        output_filename = args.output

        # Check whether we have to create a directory.
        if (dirname := os.path.dirname(output_filename)):
            os.makedirs(dirname, exist_ok=True)

    # Check early on whether we have to do something or not.
    if os.path.exists(output_filename) and not args.force:
        logging.info(
            'Refusing to overwrite existing file. Use `--force` to change '
            'this behaviour.'
        )

        sys.exit(-1)

    # Get default callbacks if user did not provide anything else. Feel
    # free to change this.
    if args.callbacks is None:
        callbacks = [
            CalculateDiffusionHomology(),
            CalculatePersistentHomology(),
        ]
    else:
        import callbacks as cb

        # Initialise callbacks with default parameters.
        callbacks = [
            getattr(cb, callback, None)() for callback in args.callbacks
        ]

        # Silently ignore all callbacks that were not found.
        callbacks = [
            callback for callback in callbacks if callback is not None
        ]

        logging.info(f'Running analysis with the following set of '
                     f'callbacks: {callbacks}')

    kernel_fn = get_kernel_fn(args.kernel)

    diffusion_condensation = DiffusionCondensation(
        callbacks=callbacks,
        kernel_fn=kernel_fn
    )
    data = diffusion_condensation(X, args.epsilon, args.alpha)

    logging.info(f'Storing results in {output_filename}')
    np.savez(output_filename, **data)
