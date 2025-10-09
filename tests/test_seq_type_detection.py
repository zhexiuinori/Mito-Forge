from mito_forge.cli.commands.pipeline import detect_seq_type

def test_detect_illumina_by_filename():
    paths = ["sample_R1.fastq", "sample_R2.fastq"]
    assert detect_seq_type(paths) == "illumina"

def test_detect_ont_by_filename():
    paths = ["run_nanopore_ont_reads.fastq"]
    assert detect_seq_type(paths) == "ont"

def test_detect_pacbio_hifi_by_filename():
    paths = ["pb_ccs_hifi_reads.fastq"]
    assert detect_seq_type(paths) == "pacbio-hifi"

def test_detect_pacbio_clr_by_filename():
    paths = ["pb_clr_raw.fastq"]
    assert detect_seq_type(paths) == "pacbio-clr"

def test_detect_hybrid_when_mixed_signals():
    paths = ["R1.fastq", "nanopore.fastq"]
    assert detect_seq_type(paths) == "hybrid"