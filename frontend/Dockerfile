FROM python:3.8.13

WORKDIR /jup

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm -rf requirements.txt
COPY ./CDK /jup/
EXPOSE 8888

ENTRYPOINT ["jupyter", "lab","--ip=0.0.0.0","--NotebookApp.token=''","--NotebookApp.password=''","--allow-root" ]