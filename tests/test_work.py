from crystalia_collector.work import list_s3_dir, compute_annotations


def test_list_s3_dir(s3_bucket, s3_prefix, work_dir):


    n_files, total_size = list_s3_dir(
      f"{s3_bucket}/{s3_prefix}202-samples-cohort/3202_samples_cohort_gg_chr2",
      "md5-8gb",
      work_dir)

    assert n_files == 8
    assert total_size == 328226892212

def test_annotate(data_dir, work_dir):

    task_file = data_dir / "chr22_small.txt"
    output_file = work_dir / "out.rdf"

    compute_annotations(output_file, task_file)
