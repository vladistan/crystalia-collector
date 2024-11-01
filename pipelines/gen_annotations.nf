nextflow.enable.dsl=2

params.s3Uri = '1000genomes-dragen-v4.0.3/data/cohorts/gvcf-genotyper-dragen-4.0.3/hg38/3202-samples-cohort/3202_samples_cohort_gg_chr2'
params.s3OutUri = 's3://crystalia-data/annotations/10-24/out.rdf'


process listFiles {

    output:
    path 'bob/task_*'

    script:
    """
    crystalia-collector list $params.s3Uri --task-dir bob --use-offsets --block-size 8589934592
    """
}
process generateRDF {
    input:
    path infile

    output:
    path 'out.rdf'

    script:
    """
    crystalia-collector  annotate  $infile
    """
}

process uploadToBucket {
    input:
    path rdfObjects

    script:
    """
    aws s3 cp $rdfObjects $params.s3OutUri
    """
}

workflow {
    listFiles | flatten | generateRDF | collectFile()| uploadToBucket
}
