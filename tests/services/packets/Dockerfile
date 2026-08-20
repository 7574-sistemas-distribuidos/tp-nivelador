FROM python:3-alpine
RUN apk update & apk add tcpdump 
COPY . .
ENTRYPOINT ["/bin/sh","-c", "tcpdump -n | python main.py"]