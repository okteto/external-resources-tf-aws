FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY public public
COPY templates templates
COPY main.py .

EXPOSE 8000

CMD python main.py