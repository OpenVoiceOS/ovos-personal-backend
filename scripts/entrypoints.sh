#!/bin/bash

ovos-local-backend --flask-host 0.0.0.0 &
ovos-backend-manager &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?
