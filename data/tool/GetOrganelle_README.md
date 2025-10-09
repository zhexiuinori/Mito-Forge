# GetOrganelle

[comment]: <> ([![Anaconda-Server Badge]&#40;https://anaconda.org/bioconda/getorganelle/badges/installer/conda.svg&#41;]&#40;https://conda.anaconda.org/bioconda&#41;)
[![Anaconda-Server Badge](https://anaconda.org/bioconda/getorganelle/badges/version.svg)](https://anaconda.org/bioconda/getorganelle)
[![Anaconda-Server Badge](https://anaconda.org/bioconda/getorganelle/badges/latest_release_date.svg)](https://anaconda.org/bioconda/getorganelle)
[![Anaconda-Server Badge](https://anaconda.org/bioconda/getorganelle/badges/downloads.svg)](https://anaconda.org/bioconda/getorganelle)
[![GitHub release](https://img.shields.io/github/release/Kinggerm/GetOrganelle.svg)](https://GitHub.com/Kinggerm/GetOrganelle/releases/)
[![European Galaxy server](https://img.shields.io/badge/usegalaxy-.eu-brightgreen?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAASCAYAAABB7B6eAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAACXBIWXMAAAsTAAALEwEAmpwYAAACC2lUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS40LjAiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyI+CiAgICAgICAgIDx0aWZmOlJlc29sdXRpb25Vbml0PjI8L3RpZmY6UmVzb2x1dGlvblVuaXQ+CiAgICAgICAgIDx0aWZmOkNvbXByZXNzaW9uPjE8L3RpZmY6Q29tcHJlc3Npb24+CiAgICAgICAgIDx0aWZmOk9yaWVudGF0aW9uPjE8L3RpZmY6T3JpZW50YXRpb24+CiAgICAgICAgIDx0aWZmOlBob3RvbWV0cmljSW50ZXJwcmV0YXRpb24+MjwvdGlmZjpQaG90b21ldHJpY0ludGVycHJldGF0aW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KD0UqkwAAAn9JREFUOBGlVEuLE0EQruqZiftwDz4QYT1IYM8eFkHFw/4HYX+GB3/B4l/YP+CP8OBNTwpCwFMQXAQPKtnsg5nJZpKdni6/6kzHvAYDFtRUT71f3UwAEbkLch9ogQxcBwRKMfAnM1/CBwgrbxkgPAYqlBOy1jfovlaPsEiWPROZmqmZKKzOYCJb/AbdYLso9/9B6GppBRqCrjSYYaquZq20EUKAzVpjo1FzWRDVrNay6C/HDxT92wXrAVCH3ASqq5VqEtv1WZ13Mdwf8LFyyKECNbgHHAObWhScf4Wnj9CbQpPzWYU3UFoX3qkhlG8AY2BTQt5/EA7qaEPQsgGLWied0A8VKrHAsCC1eJ6EFoUd1v6GoPOaRAtDPViUr/wPzkIFV9AaAZGtYB568VyJfijV+ZBzlVZJ3W7XHB2RESGe4opXIGzRTdjcAupOK09RA6kzr1NTrTj7V1ugM4VgPGWEw+e39CxO6JUw5XhhKihmaDacU2GiR0Ohcc4cZ+Kq3AjlEnEeRSazLs6/9b/kh4eTC+hngE3QQD7Yyclxsrf3cpxsPXn+cFdenF9aqlBXMXaDiEyfyfawBz2RqC/O9WF1ysacOpytlUSoqNrtfbS642+4D4CS9V3xb4u8P/ACI4O810efRu6KsC0QnjHJGaq4IOGUjWTo/YDZDB3xSIxcGyNlWcTucb4T3in/3IaueNrZyX0lGOrWndstOr+w21UlVFokILjJLFhPukbVY8OmwNQ3nZgNJNmKDccusSb4UIe+gtkI+9/bSLJDjqn763f5CQ5TLApmICkqwR0QnUPKZFIUnoozWcQuRbC0Km02knj0tPYx63furGs3x/iPnz83zJDVNtdP3QAAAABJRU5ErkJggg==)](https://usegalaxy.eu/root?tool_id=get_organelle_from_reads)

[comment]: <> ([![GitHub version]&#40;https://img.shields.io/github/commits-since/Kinggerm/GetOrganelle/1.7.6.1.svg&#41;]&#40;https://github.com/Kinggerm/GetOrganelle/commit/master&#41;)

**notice: please update to 1.7.5+, which fixed the bug on the multiplicity estimation of self-loop vertices.**

This toolkit assemblies organelle genome from genomic skimming data. 

It achieved the best performance overall both on simulated and real data and was recommended as the default for chloroplast genome assembly in a third-party comparison paper ([Freudenthal et al. 2020. Genome Biology](https://doi.org/10.1186/s13059-020-02153-6)).

<div id="citation"></div>

Please denote the version of GetOrganelle as well as the dependencies in your manuscript for reproducible science.

<b>Citation:</b> Jian-Jun Jin*, Wen-Bin Yu*, Jun-Bo Yang, Yu Song, Claude W. dePamphilis, Ting-Shuang Yi, De-Zhu Li. <b>GetOrganelle: a fast and versatile toolkit for accurate de novo assembly of organelle genomes.</b> <i>Genome Biology</i> <b>21</b>, 241 (2020). [https://doi.org/10.1186/s13059-020-02154-5](https://doi.org/10.1186/s13059-020-02154-5)

<b>License:</b> GPL https://www.gnu.org/licenses/gpl-3.0.html

Please also cite the dependencies if used:

SPAdes: [Prjibelski, A., Antipov, D., Meleshko, D., Lapidus, A. and Korobeynikov, A. 2020. Using SPAdes de novo assembler. Current protocols in bioinformatics, 70(1), p.e102.](https://currentprotocols.onlinelibrary.wiley.com/doi/abs/10.1002/cpbi.102) 

Bowtie2: [Langmead, B. and S. L. Salzberg. 2012. Fast gapped-read alignment with Bowtie 2. Nature Methods 9: 357-359.](https://www.nature.com/articles/nmeth.1923)

BLAST+: [Camacho, C., G. Coulouris, V. Avagyan, N. Ma, J. Papadopoulos, K. Bealer and T. L. Madden. 2009. BLAST+: architecture and applications. BMC Bioinformatics 10: 421.](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-10-421)

Bandage: [Wick, R. R., M. B. Schultz, J. Zobel and K. E. Holt. 2015. Bandage: interactive visualization of de novo genome assemblies. Bioinformatics 31: 3350-3352.](https://academic.oup.com/bioinformatics/article/31/20/3350/196114)


## Installation & Initialization

GetOrganelle is currently maintained under Python 3.7.0, but designed to be compatible with versions higher than 3.5.1 and 2.7.11. 
It was built for Linux and macOS. Windows Subsystem Linux is currently not supported, we are working on this.

* The easiest way to install GetOrganelle and its [dependencies](https://github.com/Kinggerm/GetOrganelle/wiki/Installation#requirement--dependencies) is using conda:
       
       
      conda install -c bioconda getorganelle

  You have to install [Anaconda](https://docs.anaconda.com/anaconda/install/) or [Miniconda](https://docs.conda.io/projects/continuumio-conda/en/latest/user-guide/install/index.html) before using the above command. 
  If you don't like conda, or want to follow the latest updates, you can find [more installation options here](https://github.com/Kinggerm/GetOrganelle/wiki/Installation#installation) (my preference).

* After installation of GetOrganelle v1.7+, please download and initialize the database of your preferred organelle genome type (embplant_pt, embplant_mt, embplant_nr, fungus_mt, fungus_nr, animal_mt, and/or other_pt). 
Supposing you are assembling chloroplast genomes:

    
      get_organelle_config.py --add embplant_pt,embplant_mt
    
  If connection keeps failing, please manually download the latest database from [GetOrganelleDB](https://github.com/Kinggerm/GetOrganelleDB) and [initialization from local files](https://github.com/Kinggerm/GetOrganelle/wiki/Initialization#option-2-initialization-from-local-files).
  
  The database will be located at `~/.GetOrganelle` by default, which can be changed via the command line parameter `--config-dir`, or via the shell environment variable `GETORG_PATH` (see more [here](https://github.com/Kinggerm/GetOrganelle/wiki/Initialization)).
    

## Test

Download [a simulated _Arabidopsis thaliana_ WGS dataset](https://github.com/Kinggerm/GetOrganelleGallery/tree/master/Test/reads):

    wget https://github.com/Kinggerm/GetOrganelleGallery/raw/master/Test/reads/Arabidopsis_simulated.1.fq.gz
    wget https://github.com/Kinggerm/GetOrganelleGallery/raw/master/Test/reads/Arabidopsis_simulated.2.fq.gz

then verify the integrity of downloaded files using `md5sum`:

    md5sum Arabidopsis_simulated.*.fq.gz
    # 935589bc609397f1bfc9c40f571f0f19  Arabidopsis_simulated.1.fq.gz
    # d0f62eed78d2d2c6bed5f5aeaf4a2c11  Arabidopsis_simulated.2.fq.gz
    # Please re-download the reads if your md5 values unmatched above

then do the fast plastome assembly (memory: ~600MB, CPU time: ~60s):

    get_organelle_from_reads.py -1 Arabidopsis_simulated.1.fq.gz -2 Arabidopsis_simulated.2.fq.gz -t 1 -o Arabidopsis_simulated.plastome -F embplant_pt -R 10

You are going to get a similar running log as [here](https://github.com/Kinggerm/GetOrganelle/wiki/Example-1#running-log) and the same result as [here](https://github.com/Kinggerm/GetOrganelleGallery/tree/master/Test/results/Arabidopsis_simulated.plastome).

Find more real data examples at [GetOrganelle/wiki/Examples](https://github.com/Kinggerm/GetOrganelle/wiki/Examples), [GetOrganelleGallery](https://github.com/Kinggerm/GetOrganelleGallery) and [GetOrganelleComparison](https://github.com/Kinggerm/GetOrganelleComparison).


## Instruction

<b>Find more organelle genome assembly instruction at [GetOrganelle/wiki](https://github.com/Kinggerm/GetOrganelle/wiki). </b>

<b>In most cases, what you actually need to do is just typing in one simple command as suggested in <a href="#recipes">Recipes</a >. 
But you are still highly recommended reading the following minimal introductions</b>:

### Starting from Reads
  
  The green workflow in the flowchart below shows the processes of `get_organelle_from_reads.py`.

  * <b>Input data</b>

    Currently, `get_organelle_from_reads.py` was written for illumina pair-end/single-end data (fastq or fastq.gz). We recommend using adapter-trimmed raw reads without quality control.
    Usually, >1G per end is enough for plastome for most normal angiosperm samples, 
    and >5G per end is enough for mitochondria genome assembly. 
    Since v1.6.2, `get_organelle_from_reads.py` will automatically estimate the read data it needs, without user assignment nor data reducing (see flags `--reduce-reads-for-coverage` and `--max-reads`). 
  
  * <b>Main Options</b>
    
    * `-w` The value word size, like the kmer in assembly, is crucial to the feasibility and efficiency of this process. 
    The best word size changes upon data and will be affected by read length, read quality, base coverage, organ DNA percent and other factors. 
    By default, GetOrganelle would automatically estimate a proper word size based on the data characters. 
    Although the automatically-estimated word size value does not ensure the best performance nor the best result, 
    you do not need to adjust this value (`-w`) if a complete/circular organelle genome assembly is produced, 
    because the circular result generated by GetOrganelle is highly consistent under different options and seeds. 
    The automatically estimated word size may be screwy in some animal mitogenome data due to inaccurate coverage estimation, 
    for which you fine-tune it instead. 
    
    * `-k` The best kmer(s) depend on a wide variety of factors too. 
    Although more kmer values add the time consuming, you are recommended to use a wide range of kmers to benefit from the power of SPAdes. 
    Empirically, you should include at least including one small kmer (e.g. `21`) and one large kmer (`85`) for a successful organelle genome assembly. 
    The largest kmer in the gradient may be crucial to the success rate of achieving the complete circular organelle genome. 
    
    * `-s` GetOrganelle takes the seed (fasta format; if this was not provided, 
    the default is `GetOrganelleLib/SeedDatabase/*.fasta`) as probe, 
    the script would recruit target reads in successive rounds (extending process). 
    The default seed works for most samples, but using a complete organelle genome sequence of a related species as the seed would help the assembly in many cases 
    (e.g. degraded DNA samples, fastly-evolving in animal/fungal samples; see more [here](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#how-to-assemble-a-target-organelle-genome-using-my-own-reference)). 
  
  * <b>Key Results</b>
  
    The key output files include
  
    * `*.path_sequence.fasta`, each fasta file represents one type of genome structure
    * `*.selected_graph.gfa`, the [organelle-only assembly graph](https://github.com/Kinggerm/GetOrganelle/wiki/Terminology)
    * `get_org.log.txt`, the log file
    * `extended_K*.assembly_graph.fastg`, the raw assembly graph
    * `extended_K*.assembly_graph.fastg.extend_embplant_pt-embplant_mt.fastg`, a simplified assembly graph 
    * `extended_K*.assembly_graph.fastg.extend_embplant_pt-embplant_mt.csv`, a tab-format contig label file for bandage visualization
  
    You may delete the files other than above if the resulting genome is complete (indicated in the log file and the name of the `*.fasta`). 
    You are expected to obtain the complete organelle genome assembly for most animal/fungal mitogenomes and plant chloroplast genomes 
    (see [here for nuclear ribosomal DNAs](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#why-does-getorganelle-generate-a-circular-genome-for-embplant_nrfungus_nr)) with the recommended recipes. 
    
    If GetOrganelle failed to generate the complete circular genome (produce `*scaffolds*path_sequence.fasta`), 
    please follow [here](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#what-should-i-do-with-incomplete-resultbroken-assembly-graph) to adjust your parameters for a second run. 
    You could also use the incomplete sequence to conduct downstream analysis.

### Starting from Assembly

  The blue workflow in the chat below shows the processes of `get_organelle_from_assembly.py`.

  * <b>Input data & Main Options</b>
  
    * `-g` The input must be a FASTG or GFA formatted assembly graph file. 
    
    * If you input an assembly graph assembled from total DNA sequencing using third-party a de novo assembler (e.g. Velvet), 
    the assembly graph may includes a great amount of non-target contigs. 
    You may want to use `--min-depth` and `--max-depth` to greatly reduce the computational burden for target extraction.
    
    * If you input an [organelle-equivalent assembly graph](https://github.com/Kinggerm/GetOrganelle/wiki/Terminology) 
    (e.g. manually curated and exported using Bandage), you may use `--no-slim`.
  
  * <b>Key Results</b>
  
    The key output files include
    
    * `*.path_sequence.fasta`, one fasta file represents one type of genome structure
    * `*.fastg`, the organelle related assembly graph to report for improvement and debug
    * `*.selected_graph.gfa`, the [organelle-only assembly graph](https://github.com/Kinggerm/GetOrganelle/wiki/Terminology)
    * `get_org.log.txt`, the log file
  

### GetOrganelle flowchart

![flowchart](https://user-images.githubusercontent.com/8598031/83836465-85afa080-a6c1-11ea-8b08-b08623d974f4.png)

## Recipes

Please refer to the [GetOrganelle FAQ](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ) to fine-tune the arguments, especially concerning [word size](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#what-is-a-good-word-size-value), [memory](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#memoryerror), and [clock time](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#how-to-speed-up-getorganelle-runs).

### _From Reads_

* **Embryophyta**

    To assembly Embryophyta plant plastid genome (plastome), e.g. using 2G raw data of 150 bp paired reads, typically I use:

      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -o plastome_output -R 15 -k 21,45,65,85,105 -F embplant_pt

    or in a draft way:
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -o plastome_output --fast -k 21,65,105 -w 0.68 -F embplant_pt
    
    or in a slow and memory-economic way:
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -o plastome_output -R 30 -k 21,45,65,85,105  -F embplant_pt --memory-save
    
    To assembly Embryophyta plant mitochondria genome (mitogenome), usually you need more than 5G raw data:
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -o mitochondria_output -R 20 -k 21,45,65,85,105 -P 1000000 -F embplant_mt
      # 1. please use the FASTG file as the final output for downstream manual processing. until further updates, the FASTA output of plant mitochondria genome of numerous repeats may be error-prone
      # 2. embplant_mt mode was not tested in the GetOrganelle paper due to the complexity of plant mitogenomes and the defects of short reads. So there is room for improvement in the argument choices.
        
    To assembly Embryophyta plant nuclear ribosomal RNA (18S-ITS1-5.8S-ITS2-26S):
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -o nr_output -R 10 -k 35,85,115 -F embplant_nr
      # Please also take a look at this FAQ https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#why-does-getorganelle-generate-a-circular-genome-or-not-for-embplant_nrfungus_nr
      
* **Non-embryophyte**
    
    Non embryophyte plastomes and mitogenomes can be divergent from the embryophyte. We have not explored it very much. But many users have successfully assemble them using GetOrganelle using the default database or a [customized database](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#how-to-assemble-a-target-organelle-genome-using-my-own-reference).
    
    There is a built-in `other_pt` mode and prepared default database for the non embryophyte plastomes. I would start with `-F other_pt` and similar options as in the `embplant_pt` part. However, there is no such built-in mode for non embryophyte mitogenomes. Considering that the sequences may be highly divergent from embplant_mt, besides using similar options as in the `embplant_mt` part, I would make a pair of customized seed database and label database, then use them to run GetOrganelle following [the guidance here](https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#how-to-assemble-a-target-organelle-genome-using-my-own-reference).
    
* **Fungus**

    To assembly fungus mitochondria genome:
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -R 10 -k 21,45,65,85,105 -F fungus_mt -o fungus_mt_out
      # if you fail with the default database, use your own seed database and label database with "-s" and "--genes" 
    
    To assembly fungus nuclear ribosomal RNA (18S-ITS1-5.8S-ITS2-28S):
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -R 10 -k 21,45,65,85,105 -F fungus_nr -o fungus_nr_out  
      # if you fail with the default database, use your own seed database and label database with "-s" and "--genes" 
      # Please also take a look at this FAQ https://github.com/Kinggerm/GetOrganelle/wiki/FAQ#why-does-getorganelle-generate-a-circular-genome-or-not-for-embplant_nrfungus_nr
      
* **Animal**
    
    To assembly animal mitochondria:
    
      get_organelle_from_reads.py -1 forward.fq -2 reverse.fq -R 10 -k 21,45,65,85,105 -F animal_mt -o animal_mt_out   
      # if you fail with the default database, rerun it using your own seed database (or the output of a first GetOrganelle run) and label database with "-s" and "--genes"
      
    Animal nuclear ribosomal RNA will be available in the future. [Issue136](https://github.com/Kinggerm/GetOrganelle/issues/136) is the place to follow.
    
### _From Assembly Graph_

There are as many available organelle types as the `From Reads` section (see more by `get_organelle_from_assembly.py -h`), but the simplest usage is not that different. Here is an example to extract the plastid genome from an existing assembly graph (`*.fastg`/`*.gfa`; e.g. from long-read sequencing assemblies):
    
    get_organelle_from_assembly.py -F embplant_pt -g ONT_assembly_graph.gfa

### _Arguments_

See a brief illustrations of those arguments by typing in:
    
    get_organelle_from_reads.py -h
        
or see the detailed illustrations:
        
    get_organelle_from_reads.py --help
    
The same brief `-h` and verbose `--help` menu can be find for `get_organelle_from_assembly.py`.

You may also find a summary of above information [here at Usage](https://github.com/Kinggerm/GetOrganelle/wiki/Usage).


## Contact

Please check [GetOrganelle wiki page](https://github.com/Kinggerm/GetOrganelle/wiki) first. If your question is running specific, please attach the `get_org.log.txt` file and the post-slimming assembly graph (`assembly_graph.fastg.extend_*.fastg`, could be Bandage-visualized *.png format to protect your data privacy).

Although older versions like 1.6.3/1.7.1/1.7.6 may be more stable, but we always strongly encourage you to keep updated. GetOrganelle was actively updated with new fixes and new features, but new bugs too. So if you catch one, please do not be surprised and report it to us. We usually have quick response to bugs.

* Find Questions & Answers at [GetOrganelle Discussions](https://github.com/Kinggerm/GetOrganelle/discussions/categories/q-a): **Recommended** 
  
  This was previously located at GetOrganelle Issues where you may find old Q&A

* Report Bugs & Issues at [GetOrganelle Issues](https://github.com/Kinggerm/GetOrganelle/issues): 
  
  Please avoid duplicate and miscellaneous issues

* [GoogleGroups](https://groups.google.com/g/getorganelle)

* QQ group (ID: 908302723): only for mutual help, and we will no longer reply to questions there

**Do NOT** directly write to us with your questions, instead please post the questions **publicly**, using above platforms (we will be informed automatically) or any other platforms (inform us of it). Our emails (jianjun.jin@columbia.edu, yuwenbin@xtbg.ac.cn) are only for receiving public question alert and private data (if applied) associated with those public questions. When you send your private data to us, enclose the email with a link where you posted the question. Our only reply emails will be a receiving confirmation, while our answers will be posted in a public place. 
