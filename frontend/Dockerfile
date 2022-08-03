FROM python:3.8.13

# Setting up virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN /opt/venv/bin/python3 -m pip install --upgrade pip

# Installing packages 
WORKDIR /joyvan
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --force-reinstall jupyter_client
RUN rm -rf requirements.txt

# Copying files
COPY ./CDK /joyvan/

# Configuring Jupter Lab
RUN jupyter trust Demo.ipynb
EXPOSE 8888

ENTRYPOINT ["jupyter-lab", "--ip=0.0.0.0", "--NotebookApp.token=FL32DqxQz6BGQkZjY4ue3MP2EmbSsN5CFqmdPfivtRBD5KKfwr3vwB3zGpYY", "--allow-root", "--no-browser" ]