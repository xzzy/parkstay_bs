#!/bin/bash

# Start the first process
env > /etc/.cronenv
sed -i 's/\"/\\"/g' /etc/.cronenv

if [ $ENABLE_CRON == "True" ];
then
echo "Starting Cron"
service cron start &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start cron: $status"
  exit $status
fi

fi

if [ $ENABLE_WEB == "True" ];
    then
echo "Starting Gunicorn"
# Start the second process
gunicorn parkstay.wsgi --bind :8080 --config /app/gunicorn.ini
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start gunicorn: $status"
  exit $status
fi
else
   echo "ENABLE_WEB environment vairable not set to True, web server is not starting."
   /bin/bash
fi