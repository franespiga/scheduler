FROM continuumio/conda-ci-linux-64-python3.7
ADD . /
WORKDIR /

RUN conda create --name myenv
# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "myenv", "/bin/bash", "-c"]
RUN pip install -r requirements.txt
RUN conda install -c conda-forge coincbc

WORKDIR /var/task
RUN python test_scheduler.py 

EXPOSE 90
#CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "90", "--workers","4"]

ENTRYPOINT ["conda", "run", "-n", "myenv", "python3", "api.py"]