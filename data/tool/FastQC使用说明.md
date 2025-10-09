[高通量测序](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=高通量测序&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiLpq5jpgJrph4_mtYvluo8iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoxOTg0MzkwMDksImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.HuVlxgZ7uWN2AgMiSvvQ-J3TvqEYAupR3ouzbgYEL0c&zhida_source=entity)获取的原始数据是一条条reads，再经过检测和拼接形成完整的[基因组序列](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=基因组序列&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiLln7rlm6Dnu4Tluo_liJciLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoxOTg0MzkwMDksImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.Hie0xaimhyQU58XnLi7W7D1QRrNsYP8AnorBFHPFQUk&zhida_source=entity)。这千千万万条序列就相当于我们数据分析实验的材料，如果测序质量比较差，那么得出的结果……，嗯，你懂的。

今天小编分享给大家一个常用的测序数据质控工具FastQC，它可以评估这些序列的质量并给我们出具一份报告，便于我们对测序结果有一个整体的把控，为后续的数据处理提供依据。

接下来我们就一起探索一下如何使用这个软件查看自己测序数据的质量吧~

**01 FastQC简介**

FastQC是一款基于Java语言设计的软件，目前可以直接下载免费使用，一般在[Linux环境](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=Linux环境&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiJMaW51eOeOr-WigyIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjE5ODQzOTAwOSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.taUI5O5ZR2uQbL2wDlNCSXqId_-TKOQtGWw7rMBffnU&zhida_source=entity)下使用命令行执行程序，它可以快速地多线程地对测序数据进行质量控制（Quality Control），还能进行质量可视化来查看质控效果。运行一段时间以后，会出现报告。使用浏览器打开后缀是html的文件，这就是图表化的fastqc报告。

FastQC官网：[https://www.bioinformatics.babraham.ac.uk/projects/fastqc/](https://link.zhihu.com/?target=https%3A//www.bioinformatics.babraham.ac.uk/projects/fastqc/)

![img](https://pic4.zhimg.com/v2-a3514864fe0887a059959bb889482167_1440w.jpg)

FastQC的下载地址：

[https://www.bioinformatics.babraham.ac.uk/projects/download.html#fastqc](https://link.zhihu.com/?target=https%3A//www.bioinformatics.babraham.ac.uk/projects/download.html%23fastqc)，根据链接下载并按照指示安装。软件信息和使用信息可以查看“README”，安装信息查看“Installation and setup instructions”。

![img](https://pica.zhimg.com/v2-f0ffd6befb342a1936e2693ac67a4bf6_1440w.jpg)

FastQC支持的格式

(1) FastQ (all quality encoding variants)

(2) Casava FastQ files*

(3) [Colorspace FastQ](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=Colorspace+FastQ&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiJDb2xvcnNwYWNlIEZhc3RRIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MTk4NDM5MDA5LCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.XwBDODF5iJ-RN7OoyJoP_BynRlfIVFi10TjCuk9mWLE&zhida_source=entity)

(4) [GZip compressed FastQ](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=GZip+compressed+FastQ&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiJHWmlwIGNvbXByZXNzZWQgRmFzdFEiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoxOTg0MzkwMDksImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.xi7hkWjVlq371Dl-OJmLjylo5A2qTH8XK3ohGkiXu64&zhida_source=entity)

(5) [SAM](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=SAM&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiJTQU0iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoxOTg0MzkwMDksImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.ASr6DuVVQ70xHnae9g1UWA7lXiOF7SttgGhvi6_iaPA&zhida_source=entity)

(6) [BAM](https://zhida.zhihu.com/search?content_id=198439009&content_type=Article&match_order=1&q=BAM&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NjAxNDUyOTEsInEiOiJCQU0iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoxOTg0MzkwMDksImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.BA2H3sDLPvumgx4BwQMVAst32_mgrujlPewvszI0K-Y&zhida_source=entity)

(7) SAM/BAM Mapped only (normally used for colorspace data)

**02 安装与使用**

（1）Windows系统

① 首先下载对应的软件包。

![img](https://pic4.zhimg.com/v2-0524d1bf5ff636a63eca53df89d82a3d_1440w.jpg)

② 下载后解压缩，查看文件夹的内容。

![img](https://pic4.zhimg.com/v2-89f5367dce4b1d2b51033acefdd92631_1440w.jpg)

③ 双击“run_fastqc.bat”运行程序，页面如下图所示。

![img](https://pic3.zhimg.com/v2-3e9da0f67fea09fec84e0c4f92616ca6_1440w.jpg)

④ 点击“Help”>“Contents…”,可以查看FastQC的软件简介、基本操作、分析结果等详细信息。

![img](https://pic2.zhimg.com/v2-47c519acb5462bd0b20df71a3d1f9b47_1440w.jpg)

⑤ 点击“File”>“Open…”>选择要分析的序列文件。

![img](https://pic3.zhimg.com/v2-2966f4170cebf46217d015a7f73dffd0_1440w.jpg)

⑥ 通过点击文件夹和文件，选择需要进行分析的数据，点击打开。

![img](https://picx.zhimg.com/v2-e3172cc67401fa64e211104b7863da39_1440w.jpg)

⑦ 现在进入了FastQC的分析界面，稍等片刻就可以查看分析结果。

![img](https://pica.zhimg.com/v2-f1251460248b78c3e8fbc9e94ca93ffa_1440w.jpg)

⑧ 保存报告，点击“File”>“Save report…”>选择要存放的位置。

![img](https://pic1.zhimg.com/v2-290769daa62bf63159637a237f999e94_1440w.jpg)

![img](https://pic2.zhimg.com/v2-7167dfb16c4bf38e1e0471f9b06b3581_1440w.jpg)

⑨ 查看保存的文件。

![img](https://pic2.zhimg.com/v2-e3f9c827316544cbd7bcd51582a42319_1440w.jpg)

（2）Linux系统

FastQC是在Java环境下运行的，所以在安装fastqc之前，Linux下要有相应的Java运行环境（JRE），目前大多数发行版都已经安装了java，所以你可能不需要自己进行安装啦！我们暂时就不介绍如何安装了哦~但是保险起见，我们还是确定一下自己的Linux系统是否安装了java环境。

\#查看是否具有Java

两个命令二选一命令：

```text
which java
java -version
```

![img](https://pic1.zhimg.com/v2-ec6d7a07236149ecdc3d3be94b423ee6_1440w.jpg)

如果显示“not found”，可以根据提示的命令输入后运行进行下载。

Ubuntu系统可以通过执行以下命令安装java。

```text
sudo apt install default-jre
```

完成java环境配置后，就可以开始学习Linux下FastQC安装与使用了。

**基于conda安装**

在Linux系统下可以直接使用conda安装:[https://anaconda.org/bioconda/fastqc](https://link.zhihu.com/?target=https%3A//anaconda.org/bioconda/fastqc)

\#安装代码

```text
conda install -c bioconda fastqc
```

![img](https://pica.zhimg.com/v2-f6912df7ba48cc4f446d9c7378d2804e_1440w.jpg)

\#查看fastqc是否安装完成

```text
fastqc --version
```

![img](https://pic4.zhimg.com/v2-2d1789568da3806ca853667e2d618b61_1440w.jpg)

\#查看fastqc的参数

```text
fastqc --help
```

![img](https://pic2.zhimg.com/v2-338abe9249a12b9d7bd85f145e4cfd81_1440w.jpg)

主要参数解读：

-o 或 --outdir #FastQC生成的报告文件的储存路径，生成的报告的文件名是根据输入来定的

--extract #生成的报告默认会打包成1个压缩文件，使用这个参数是让程序不打包

-t 或 --threads #选择程序运行的线程数

-q 或 --quiet #安静运行模式，一般不选这个选项的时候，程序会实时报告运行的状况

\#使用fastqc进行质量检测，在当前文件夹生成一个.html网页文件和一个.zip文件。

```text
fastqc 样本名称
```

![img](https://pic3.zhimg.com/v2-e726b76ef33c219ea496ff48216117c2_1440w.jpg)

![img](https://pic3.zhimg.com/v2-98eb280985be1f3fb50b8bc181a3009e_1440w.jpg)

\#批量处理样本，在指定文件夹result生成.html网页文件和.zip文件。

```text
fastqc 样本1 样本2 … -o 文件夹
```

![img](https://pica.zhimg.com/v2-1c45732af77ce0ea513543b48794a0f8_1440w.jpg)

![img](https://pic1.zhimg.com/v2-ca8cbfdae0baf31a1dcb0b1824121d9e_1440w.jpg)

![img](https://pic3.zhimg.com/v2-5875aa0530e78004a7a395c9810d7102_1440w.jpg)

**下载安装包**
在网站上选择对应的下载入口：

[http://www.bioinformatics.babraham.ac.uk/projects/download.html#fastqc](https://link.zhihu.com/?target=http%3A//www.bioinformatics.babraham.ac.uk/projects/download.html%23fastqc), 点击进行下载，获得了一个压缩包fastqc_v0.11.9.zip。

![img](https://pic4.zhimg.com/v2-0524d1bf5ff636a63eca53df89d82a3d_1440w.jpg)

首先进行解压缩，运行命令unzip fastqc_v0.11.9.zip。

![img](https://pic2.zhimg.com/v2-d3f37ca51d8d86e6d0d722981e04c165_1440w.jpg)

解压缩后生成了一个名为FastQC的文件夹，cd FastQC进入文件夹，ls -l可以看到里面有一个fastqc执行文件。

![img](https://pica.zhimg.com/v2-42ca78262664b207a135472d50b6b086_1440w.jpg)

**如何运行分析呢？**

./fastqc+文件名称，就可以运行fastqc程序啦！

注意：输出文件默认储存在分析文件所在文件夹中（data）。

![img](https://pic1.zhimg.com/v2-f8b9d8aafed31f005433037d93c4a1f6_1440w.jpg)