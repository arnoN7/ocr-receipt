FROM python:3.9

COPY . .

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install open-cv dependancies
RUN apt clean
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
# install tesseract
RUN apt-get install tesseract-ocr -y
RUN apt-get install tesseract-ocr-fra -y

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5002
# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]