params.str = 'Hello world!'

process splitLetters {
    output:
    path 'chunk_*'

    """
    printf '${params.str}' | split -b ${params.chunk_size} - chunk_
    """
}

process convertToUpper {
    input:
    path x

    output:
    stdout

    """
    rev $x
    """
}

workflow {
    splitLetters | convertToUpper | view { it.trim() }
}