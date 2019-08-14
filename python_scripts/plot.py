import matplotlib
matplotlib.use("Agg")
import nb_encode as nbe
import argparse
import os
import glob
import sys

# expression = pd.concat(
#     [
#         pd.read_csv(glob.glob(sample+'/*gene_tpm.gct')[0], sep='\t', header=2, index_col=0)[['TPM']].rename({'TPM':sample}, axis='columns')
#         for sample in samples.index
#     ],
#     axis=1
# )
# stats_df = pd.concat([
#         pd.read_csv(path, sep='\t', index_col=0).T.assign(sample_id=[os.path.basename(os.path.dirname(path))]) for path in glob('./*/*.metrics.tsv')
# ]).reset_index().set_index('sample_id')

#
# metrics = pd.concat([
#     pd.read_csv(path+'.metrics.tsv', sep='\t', index_col=0).T.assign(
#         sample_id=sample
#     )
#     for sample, path in samples.items()
# ]).reset_index().set_index('sample_id')
# metrics.columns.name = None


def main(args):
    samples = []
    # TODO: Detect output settings
    # 1) Check RPKM vs TPM in filenames
    # 2) Check for presence of coverage file
    # 3) Check for presence of fragmentSizes file
    for sample in args.samples:
        if not os.path.isdir(sample):
            sys.exit("'%s' is not a valid directory" % sample)
        if not len(glob.glob(sample+"/*.metrics.tsv")):
            sys.exit("'%s' does not contain valid RNA-SeQC output files" % sample)
        samples.append(os.path.join(
            os.path.abspath(sample),
            '.metrics.tsv'.join(
                os.path.basename(glob.glob(sample+"/*.metrics.tsv")[0]).split('.metrics.tsv')[:-1]
            )
        ))
    samples = {os.path.basename(sample):sample for sample in samples}
    print("Detected", len(samples), "samples")
    if len(samples) < 2:
        sys.exit("At least 2 samples required for comparison")

    nb = nbe.Notebook()
    nb.add_markdown_cell(
        '# RNA-SeQC Output',
        '---',
        'Created automatically by RNA-SeQC using the nb_encode api'
    )
    # --- from here, each cell will be run in the script and encoded to the notebook
    import matplotlib.pyplot as plt
    import seaborn as sea
    import pandas as pd
    import numpy as np
    import metrics as met
    nb.add_code_cell([
        'import matplotlib.pyplot as plt',
        'import seaborn as sea',
        'import pandas as pd',
        'import numpy as np',
        'import sys',
        'sys.path.append("%s")' % os.path.dirname(os.path.abspath(__file__)),
        'import metrics as met',
        'import os'
    ])
    # ---
    print("Loading metrics")
    metrics = pd.concat([
        pd.read_csv(path+'.metrics.tsv', sep='\t', index_col=0).T
        for sample, path in samples.items()
    ])
    metrics.columns.name = None
    metrics.index.name = 'sample_id'
    nb.add_code_cell([
        'samples = %s' % repr(samples),
        nbe.trim("""metrics = pd.concat([
            pd.read_csv(path+'.metrics.tsv', sep='\\t', index_col=0).T
            for sample, path in samples.items()
        ])"""),
        'metrics.columns.name = None',
        'metrics.index.name = "sample_id"',
        'metrics'
    ], nbe.encode_dataframe(metrics, nb.exec_count))
    metrics.to_csv('project_metrics.csv')
    # ---
    print("Generating Fragment Size KDE")
    fig = plt.figure(figsize=(15,10))
    ax = fig.add_subplot(111)
    for sample, path in samples.items():
        path = path+'.fragmentSizes.txt'
        if os.path.isfile(path):
            with open(path) as r:
                line = r.readline().strip()
                if 'Count' in line:
                    # V2
                    fragments = [
                        int(line.strip().split()[0])
                        for line in r
                        for _ in range(int(line.strip().split()[1]))
                    ]
                else:
                    r.seek(0,0)
                    fragments = [int(line.strip()) for line in r]
                if len(np.unique(fragments)) > 1:
                    lim = np.percentile(fragments, 99)
                    sea.kdeplot([x for x in fragments if x <= lim], label=sample, ax=ax)
    ax.set_xlabel("Fragment Length")
    ax.set_ylabel("Density")
    nb.add_code_cell(
        nbe.trim("""
        fig = plt.figure(figsize=(15,10))
        ax = fig.add_subplot(111)
        for sample, path in samples.items():
            path = path+'.fragmentSizes.txt'
            if os.path.isfile(path):
                with open(path) as r:
                    line = r.readline().strip()
                    if 'Count' in line:
                        # V2
                        fragments = [
                            int(line.strip().split()[0])
                            for line in r
                            for _ in range(int(line.strip().split()[1]))
                        ]
                    else:
                        r.seek(0,0)
                        fragments = [int(line.strip()) for line in r]
                    if len(np.unique(fragments)) > 1:
                        lim = np.percentile(fragments, 99)
                        sea.kdeplot([x for x in fragments if x <= lim], label=sample, ax=ax)
        ax.set_xlabel("Fragment Length")
        ax.set_ylabel("Density")
        """),
        ax,
        nbe.encode_figure(fig)
    )
    # ---
    print("Generating QC figures")
    cohorts = pd.read_csv(args.cohorts, sep='\t', index_col=0, header=None, squeeze=True) if args.cohorts is not None else None
    dates = pd.to_datetime(pd.read_csv(args.dates, sep='\t', index_col=0, header=None, squeeze=True)) if args.dates is not None else None
    figures = met.plot_qc_figures(
        metrics,
        mapping_rate=0.95,
        million_mapped_reads=50,
        million_mapped_reads_qc=45,
        rrna_rate=0.15,
        end1_mismatch_rate=0.005,
        end2_mismatch_rate=0.02,
        intergenic_rate=0.05,
        exonic_rate=0.7,
        alpha=0.5,
        ms=16,
        cohort_s=cohorts,
        date_s=dates,
        show_legend=cohorts is not None
    )
    nb.add_code_cell(
        nbe.trim("""
        cohorts = pd.read_csv({0}, sep='\\t', index_col=0, header=None, squeeze=True) if os.path.isfile({0}) else None
        dates = pd.to_datetime(pd.read_csv({1}, sep='\\t', index_col=0, header=None, squeeze=True) if os.path.isfile({1}) else None
        figures = met.plot_qc_figures(
            metrics,
            mapping_rate=0.95,
            million_mapped_reads=50,
            million_mapped_reads_qc=45,
            rrna_rate=0.15,
            end1_mismatch_rate=0.005,
            end2_mismatch_rate=0.02,
            intergenic_rate=0.05,
            exonic_rate=0.7,
            alpha=0.5,
            ms=16,
            cohort_s=cohorts,
            date_s=dates,
            show_legend=cohorts is not None
        )
        """.format(
            repr(args.cohorts),
            repr(args.dates)
        )),
        *[
            nbe.encode_figure(fig)
            for fig, ax in figures
        ],
        metadata={'scrolled': False}
    )
    # ---
    def remap_columns(df, sample):
        if sample in df.columns:
            return df[[sample]]
        if sample.replace('.bam','') in df.columns:
            return df[[sample.replace('.bam', '')]]
        if 'Counts' in df.columns:
            return df[['Counts']].rename({'Counts':sample}, axis='columns')
    nb.add_code_cell(
        nbe.trim("""
        def remap_columns(df, sample):
            if sample in df.columns:
                return df[[sample]]
            if sample.replace('.bam','') in df.columns:
                return df[[sample.replace('.bam', '')]]
            if 'Counts' in df.columns:
                return df[['Counts']].rename({'Counts':sample}, axis='columns')
        """)
    )
    # ---
    print("Generating expression PCA")
    expression_df = pd.concat(
        [
            remap_columns(pd.read_csv(path+'.gene_reads.gct', sep='\t', header=2, index_col=0), sample)
            for sample, path in samples.items()
        ],
        axis=1
    )
    nb.add_code_cell(
        nbe.trim("""
        expression_df = pd.concat(
            [
                remap_columns(pd.read_csv(path+'.gene_reads.gct', sep='\\t', header=2, index_col=0), sample)
                for sample, path in samples.items()
            ],
            axis=1
        )
        expression_df.head()
        """),
        nbe.encode_dataframe(
            expression_df.head(),
            nb.exec_count
        )
    )
    expression_df.to_csv('project_expression_df.csv')
    # ---
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.colorbar(ax.scatter(metrics['Duplicate Rate of Mapped'], metrics['Genes Detected'], c=np.log(metrics['Unique Mapping, Vendor QC Passed Reads']))).set_label("log Unique Mapping, Vendor QC Passed Reads")
    ax.set_xlabel("Duplication Rate")
    ax.set_ylabel("Genes Detected")
    nb.add_code_cell(
        nbe.trim("""
        fig = plt.figure()
        ax = fig.add_subplot(111)
        plt.colorbar(ax.scatter(metrics['Duplicate Rate of Mapped'], metrics['Genes Detected'], c=np.log(metrics['Unique Mapping, Vendor QC Passed Reads']))).set_label("log Unique Mapping, Vendor QC Passed Reads")
        ax.set_xlabel("Duplication Rate")
        ax.set_ylabel("Genes Detected")
        """),
        nbe.encode_figure(fig),
        metadata={'scrolled':False}
    )
    # ---
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(metrics['Median Exon CV'], metrics['Genes Detected'])
    ax.set_xlabel("Median Exon CV")
    ax.set_ylabel("Genes Detected")
    nb.add_code_cell(
        nbe.trim("""
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.scatter(metrics['Median Exon CV'], metrics['Genes Detected'])
        ax.set_xlabel("Median Exon CV")
        ax.set_ylabel("Genes Detected")
        """),
        nbe.encode_figure(fig),
        metadata={'scrolled':False}
    )
    # ---
    p_df, pca = met.get_pcs(expression_df)
    fig = met.plot_pca(p_df, pca, cohort_s=cohorts)
    nb.add_code_cell(
        [
            'p_df, pca = met.get_pcs(expression_df)',
            'fig = met.plot_pca(p_df, pca, cohort_s=cohorts)'
        ],
        nbe.encode_figure(fig),
        metadata={'scrolled': False}
    )
    # ===
    nb.add_code_cell('')
    nb.write(args.output)



if __name__ == '__main__':
    parser = argparse.ArgumentParser('rnaseqc-plot')
    parser.add_argument(
        'samples',
        nargs='+',
        help="Directory path(s) to RNA-SeQC output. Each directory should"
        " contain the output files from RNA-SeQC for a single sample"
    )
    parser.add_argument(
        'output',
        type=argparse.FileType('w'),
        help="Output python notebook"
    )
    parser.add_argument(
        '-c', '--cohorts',
        help="Path to a tsv file. First column should be sample names"
        ", second column should be cohort names",
        default=None
    )
    parser.add_argument(
        '-d', '--dates',
        help="Path to a tsv file. First column should be sample names"
        ", second column should be sequencing dates",
        default=None
    )
    main(parser.parse_args())
