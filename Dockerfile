FROM python:3.8.13

WORKDIR /jup


COPY ./CCDK /jup/
RUN pip install jupyter -U && pip install jupyterlab
RUN pip install pandas
RUN pip install networkx
RUN pip install itables
RUN pip install pyvis
EXPOSE 8888

ENTRYPOINT ["jupyter", "lab","--ip=0.0.0.0","--NotebookApp.token=''","--NotebookApp.password=''","--allow-root" ]