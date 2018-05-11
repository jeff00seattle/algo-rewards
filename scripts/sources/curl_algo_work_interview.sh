#!/usr/bin/env bash

if [ -z "$CURL_REQUEST" ]
  then
    CURL_REQUEST="GET"
fi

if [ -z "$ENDPOINT" ]
  then
    echo "$0: Provide --endpoint" ; usage ; exit 1
fi

CURL_VERBOSE=""
if [ $VERBOSE = true ]
  then
    CURL_VERBOSE=" --verbose"
fi

CURL_CMD="curl \"http://algo.work/interview/${ENDPOINT}\"
  --request $CURL_REQUEST
  $CURL_VERBOSE
  --header \"Content-Type: application/json\"
  --connect-timeout 60
  --location
  --get
  --write-out \"%{time_total}\n\"
"

if [ $VERBOSE = true ]
  then
    echo CURL_CMD=$CURL_CMD
fi

CURL_RESPONSE=$(eval $CURL_CMD)