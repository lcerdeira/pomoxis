import argparse
from concurrent.futures import ProcessPoolExecutor
import functools
import logging
import os

from Bio import SeqIO
from intervaltree import IntervalTree, Interval
import numpy as np
import pysam


from pomoxis.common.util import parse_regions, Region


def main():
    logging.basicConfig(format='[%(asctime)s - %(name)s] %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
    parser = argparse.ArgumentParser('subsample bam and fastx to create fastx with uniform depth')
    parser.add_argument('bam',
        help='input bam file.')
    parser.add_argument('depth', nargs='+', type=int,
        help='Target depth.')
    parser.add_argument('-o', '--output_prefix', default='sub_sampled',
        help='Output prefix')
    parser.add_argument('-x', '--patience', default=5, type=int,
        help='Maximum iterations with no change in median coverage before aborting.')
    parser.add_argument('-r', '--regions', nargs='+',
        help='Only process given regions.')
    parser.add_argument('-s', '--stride', type=int, default=1000,
        help='Stride in genomic coordinates when searching for new reads. Smaller can lead to more compact pileup.')
    parser.add_argument('-p', '--profile', type=int, default=1000,
        help='Stride in genomic coordinates for depth profile.')
    parser.add_argument('-O', '--orientation', choices=['fwd', 'rev'],
        help='Sample only forward or reverse reads.')

    args = parser.parse_args()

    with pysam.AlignmentFile(args.bam) as bam:
        ref_lengths = dict(zip(bam.references, bam.lengths))
  
        if args.regions is not None:
            regions = parse_regions(args.regions, ref_lengths=ref_lengths)
        else:
            regions = [Region(ref_name=r, start=0, end=ref_lengths[r]) for r in bam.references]

    worker = functools.partial(process_region, args=args)
    with ProcessPoolExecutor() as executor:
        executor.map(worker, regions)


def process_region(region, args):
    logger = logging.getLogger(region.ref_name)
    logger.info("Building interval tree.")
    tree = IntervalTree()
    with pysam.AlignmentFile(args.bam) as bam:
        ref_lengths = dict(zip(bam.references, bam.lengths))
        for r in bam.fetch(region.ref_name, region.start, region.end):
            if (r.is_reverse and args.orientation == 'fwd') or \
               (not r.is_reverse and args.orientation == 'rev'):
                continue
            # trim reads to region
            tree.add(Interval(
                max(r.reference_start, region.start), min(r.reference_end, region.end),
                r.query_name))

    logger.info('Starting pileup.')
    coverage = np.zeros(region.end - region.start, dtype=np.uint16)
    reads = set()
    n_reads = 0
    iteration = 0
    it_no_change = 0
    last_depth = 0
    targets = iter(sorted(args.depth))
    target = next(targets)
    while True:
        cursor = 0
        while cursor < ref_lengths[region.ref_name]:
            hits = _nearest_overlapping_point(tree, cursor)
            if hits is None:
                cursor += args.stride
            else:
                found = False
                for read in hits:
                    # one would like to simply remove read from the tree
                    #   but there seems to be a bug in the removal
                    if read.data in reads:
                        continue
                    reads.add(read.data)
                    cursor = read.end
                    found = True
                    coverage[read.begin - region.start:read.end - region.start] += 1
                    break
                if not found:
                    cursor += args.stride
        iteration += 1
        median_depth = np.median(coverage)
        stdv_depth = np.std(coverage)
        logger.debug(u'Iteration {}. reads: {}, depth: {:.0f}X (\u00B1{:.1f}).'.format(
            iteration, len(reads), median_depth, stdv_depth))
        # output when we hit a target
        if median_depth >= target:
            logger.info("Hit target depth {}.".format(target))
            _write_pileup(
                args.bam, '{}_{}X'.format(args.output_prefix, target),
                region, reads, coverage, args.profile)
            try:
                target = next(targets)
            except StopIteration:
                break
        # exit if nothing happened this iteration
        if n_reads == len(reads):
            logger.warn("No reads added, finishing pileup.")
            break
        n_reads = len(reads)
        # or if no change in depth
        if median_depth == last_depth:
            it_no_change += 1
            if it_no_change == args.patience:
                logging.warn("Coverage not increased for {} iterations, finishing pileup.".format(
                    args.patience
                ))
                break
        else:
            it_no_change == 0
        last_depth = median_depth


def _nearest_overlapping_point(src, point):
    """Find the interval with the closest start point to a given point.

    :param src: IntervalTree instance.
    :param point: query point.

    :returns: Interval instance of interval with closest start.

    """
    items = src.search(point)
    if len(items) == 0:
        return None 
    items = sorted(items, key=lambda x: x.end - x.begin, reverse=True)
    items.sort(key=lambda x: abs(x.begin - point))
    return items


def _write_pileup(bam, prefix, region, sequences, coverage, profile):
    sequences = set(sequences)

    # filtered bam
    output = '{}_{}.{}'.format(prefix, region.ref_name, os.path.basename(bam))
    src_bam = pysam.AlignmentFile(bam, "rb")
    out_bam = pysam.AlignmentFile(output, "wb", template=src_bam)
    for read in src_bam.fetch(region.ref_name, region.start, region.end):
        if read.query_name in sequences:
            out_bam.write(read)
    src_bam.close()
    out_bam.close()
    pysam.index(output)

    # depth profile
    output = '{}_{}.depth'.format(prefix, region.ref_name)
    end = profile * (len(coverage) // profile)
    cov_blocks = coverage[0:end].reshape(-1, profile)
    depth_profile = np.mean(cov_blocks, axis=1, dtype=np.uint32)
    start = region.start + profile // 2
    positions = (start + profile * x for x in range(len(depth_profile)))
    with open(output, 'w') as fh:
        fh.write("position\tdepth\n")
        for pos, depth in zip(positions, depth_profile):
            fh.write("{}\t{}\n".format(pos, depth))


if __name__ == '__main__':
    main()
