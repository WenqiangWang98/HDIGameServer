#Deriving the latest base image
FROM python:3.8.10

# Any working directory can be chosen as per choice like '/' or '/home' etc
# i have chosen /usr/app/src
WORKDIR /server

#to COPY the remote file at working directory in container
COPY server.py /server
COPY file.py /server
COPY requirements.txt /server

RUN pip install -r requirements.txt
# Now the structure looks like this '/usr/app/src/test.py'

#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD [ "python", "server.py"]
