FROM pypy:3.8-7.3.7-bullseye
MAINTAINER C.Plug

# Timezone must be set
ENV TZ="Asia/Tokyo"
# Explicitly set the marker for a docker environment
ENV DOCKER=1

# Prepare the pipenv
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv --python /opt/pypy/bin/python

EXPOSE 8080

ADD start.sh /
RUN chmod +x /start.sh
CMD /start.sh