FROM ubuntu:22.04 as build

WORKDIR /

RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y wget vim bzip2 python3-pip

RUN mkdir -p ~/miniconda3
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh --no-check-certificate && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    rm -rf ~/miniconda3/miniconda.sh

ENV PATH /root/miniconda3/bin:$PATH

RUN conda init bash
RUN conda install -y -c pytorch/label/nightly faiss-cpu

COPY requirements.txt .
RUN conda install -y -c conda-forge --file requirements.txt

WORKDIR /app

COPY . .

EXPOSE 5000

CMD python ./search_service/main.py

