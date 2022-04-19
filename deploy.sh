git pull
sudo docker build -t ocr-receipt .
sudo docker run -p 9018:5002 ocr-receipt