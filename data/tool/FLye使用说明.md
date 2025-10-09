# 一、介绍

Flye是用于单分子组装数据的denovo基因组装的软件。这个软件可以用于各种数据集，从小的细菌到大的哺乳动物。

输入是原始的PacBio或者ONT的序列文件，输出是polished的contig。Flye同时也有针对微生物组装的模式。

# 二、安装和使用

安装非常简单～
 `conda install flye`
 使用的话，输入文件是FASTA或者FASTQ格式的，可以是gz压缩或者普通文本。对于raw的话，期望的错误率低于30%，校正之后序列的错误率低于3%，HiFi序列的低于1%。不过要记住，Flye最开始是基于raw reads开发的。

已经不需要提供基因组的大小，但是如果使用 --asm-coverage 则需要提供。

为了减少内存的消耗，可以使用最长的reads来进行初始化的disjointig的组装，使用--asm-coverage和--genome-size就可以了。一般而言，40x的深度已经足够了。

可以单独使用--polish-target进行结果打磨。

# 三、使用示例

- 针对pacbio
   `flye --pacbio-raw E.coli_PacBio_40x.fasta --out-dir out_pacbio --threads 4`
- 针对nanopore数据
   `flye --nano-raw Loman_E.coli_MAP006-1_2D_50x.fasta --out-dir out_nano --threads 4`

# 四、输入数据的类型

- Oxford Nanopore：使用--nano-raw，ONT的数据错误率在5%-15%之间，尤其是在同聚物区域，错误率更高。
- PacBio HiFi：使用--pacbio-hifi的参数来选择这个模式。期望错误率低于1%，我们也可以用--hifi-error这个参数来指定错误率，这样可以获得更完整的组装。
- PacBio CLR：使用--pacbio-raw的参数，错误率在15%左右。注意的是，使用这个模式需要去除接头和分开多个passes。不过需要注意别拆分出了错误的序列。
- error-corrected reads：可以使用--pacbio-corr 或者 --nono-corr这个参数，来支持校正后的序列，这个序列错误率应该小于3%。如果组装的结果比较碎，可能序列中的错误率比较高，这个时候可以考虑用raw reads。
- 多个contig的一致性序列：使用--subassemblies来输入一系列的组装好的contig序列，这个可以用其他组装程序获得，期望的错误率小于1%。这样的话，用--iterations 0 可以来跳过polishing stage。

由于Flye可以直接使用raw reads，因此不需要前期的纠错。Flye会检测嵌合序列和低质量的序列，因此这个也不需要去除。然后，需要去除的是污染的序列。

# 五、参数描述

**最小overlap长度**
 这个参数默认是reads N90，一般不需要设置。如果要设置，可以设置到3-5k。建议设置的越高越好，这样repeat graph就更少会纠缠，但是这样会产生更多的gap。
 **Metagenome mode**
 这个模式用于高度不均匀覆盖度的序列， 对于低至2x的覆盖度的区域也可以进行组装。在一些简单的metagenome中，使用普通的模式，会获得更多的长的序列，而用meta模式，序列会更加的片段化一些。对于复杂的metagenome，建议使用--meta模式。

**Haplotype模式**
 默认的，Flye会合并graph中各种结构（bubbles、superbubbles、roundabout）等，来产生更长的一致性contig。使用--keep-haplotypes来保留更多的path，产生更细节的组装结果。

**Trestle**
 Trestle是一个额外的模块，用于解析没有被read桥接的重复度是2的简单重复。根据数据集，它可能解析一些额外的重复，这对小的(细菌基因组)是有帮助的。使用--trestle选项来启用该模块。在大型基因组上，改善通常是最小的，但计算可能会花费大量时间。

**覆盖度的降低**
 对于大基因组，当深度过高的时候，需要较高的RAM。因此可以使用--asm-coverage来选择特定的深度，一般而言使用30x比较合适。

**打磨的迭代次数**
 程序的最后会进行polish。默认的只进行一次polish，进行多次polish会矫正更多的错误，如果设置为0，那么就不会进行polish。

# 六、结果输出

主要有三种输出文件：

- assembly.fasta：最终的组装的结果
- assembly_graph.gfa|gv：最终的repeat graph，不过edge序列会和contig的序列不一样，因为contig可能会包含额外的多个边。
- assembly_info.txt：contig的额外的信息

每个contig就是图里一个唯一的边，同时这个唯一的contig也会进行两边延伸，来解决repeat区域。
 因此，具有相同id的contig，会比相应的edge要长。这个同OLC算法的软件相似。
 有时候，也会将contig基于repeat graph结构拼接成scaffolds。这些结果会输出成以scaffold_为前缀的文件。
 尽管很难估计可靠的gap大小，一般默认是100个Ns。并且assembly_info.txt文件也会输出这些scaffold是怎么构建的信息。
 assembly_info.txt示例如下

![img](https:////upload-images.jianshu.io/upload_images/12248725-cbe444d28a110a8e?imageMogr2/auto-orient/strip|imageView2/2/w/1080/format/webp)

每列信息如下：

- contig/scaffold id
- 长度
- 覆盖度
- 是否是圈
- 是否是重复
- 重复度
- Alternative group
- 图的路径
   用？？来代表scaffold的gaps，用*代表一个终止node。

# 七、性能比较

直接上图，看各个数据量大小下的资源情况。

![img](https:////upload-images.jianshu.io/upload_images/12248725-5fbcbd7646a0002f?imageMogr2/auto-orient/strip|imageView2/2/w/1080/format/webp)

# 八、算法说明

**什么是repeat graph？**
 Flye算法使用repeat graph作为核心的数据结构，不同于de bruijn图需要精确的kmer的匹配，repeat graph可以构建相似的序列匹配，从而可以容忍较高的噪音。repeat graph的边代表基因组序列，顶点代表连接情况。所有的边要么是唯一的 ，要么是重复的。整个基因组通过遍历这个repeat graph，可以得到。因此unique的graph是只在遍历中出现一次。repeat graph可以用AGB或者Bandage进行可视化，如下所示。[https://github.com/almiheenko/AGB](https://links.jianshu.com/go?to=https%3A%2F%2Fgithub.com%2Falmiheenko%2FAGB) [https://github.com/rrwick/Bandage](https://links.jianshu.com/go?to=https%3A%2F%2Fgithub.com%2Frrwick%2FBandage)

![img](https:////upload-images.jianshu.io/upload_images/12248725-a1cd4d84df689a59?imageMogr2/auto-orient/strip|imageView2/2/w/1080/format/webp)

**Flye的主要流程**
 以下图为例，假设基因组A中有重复序列R1和R2，每个重复序列有2个拷贝，相似度为99%；同时还有四个唯一的片段A、B、C、D。

根据基因组获得和产生了一系列的序列（b），将这些序列进行进行拼接，拼接成disjointig（c），并将这些disjointig进行连接（d），构建连接后disjointig通过比对获得的repeat plot(e)，并将repeat plot转换成repeat graph，即flye的核心数据结构（f），然后将序列比对到repeat graph上(g)，最后根据比对结果，构建R1的两个拷贝和R2的两个拷贝。

![img](https:////upload-images.jianshu.io/upload_images/12248725-c905959b4a53f9d9?imageMogr2/auto-orient/strip|imageView2/2/w/1080/format/webp)

**repeat plot和repeat graph如何相互转换呢？**
 假设一条序列XABYABZBU,其中重复为AB，AB和B。根据局部的自身比对，可以画出如图a的共线性图。如果比对的终点在对角线的投影重合，那么分配为相通的颜色，例如下图a中的蓝色。将对角线上不同的点连接起来，形成线性的结构（b）；将相同颜色的点合并到一起，形成图c，最后对图进行简化得到图（d）。

![img](https:////upload-images.jianshu.io/upload_images/12248725-8df2c973908e569c?imageMogr2/auto-orient/strip|imageView2/2/w/695/format/webp)

**如何解决unbridge repeat？**
 假设有以下b的repeat graph，有两个拷贝的REP，长度为22kb，是处于unbridge的状态。为了获得REP的序列，我们首先或者IN1、IN2、OUT1和OUT2的接头序列，同时对IN1、IN2、OUT1和OUT2进行延申。对延伸后的IN1、IN2、OUT1、OUT2再次去寻找跨越全REP区域的序列，发现有13条和18条，这样，我们把所有的区域都解决了。

![img](https:////upload-images.jianshu.io/upload_images/12248725-adb4cb4b43a3c9c4?imageMogr2/auto-orient/strip|imageView2/2/w/977/format/webp)



