FROM selenium/standalone-chrome
USER root
RUN mkdir /testing && chmod 777 /testing
COPY . /testing 
WORKDIR /testing
RUN python3 -m pip install -r requirements.txt --break-system-packages --ignore-installed
CMD ["python3", "app_testing_headless.py"]