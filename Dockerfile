# start by pulling the python image
FROM python:3.9.19

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

RUN pip install --upgrade pip
# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app
EXPOSE 3000
# configure the container to run in an executed manner
ENTRYPOINT [ "python3" ]

CMD ["main.py" ]
