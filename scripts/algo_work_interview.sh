#!/usr/bin/env bash
#  Algorithmia Interview
#

VERBOSE=false
HELP=false
ENDPOINT="a"

USAGE="\nUsage: $0\n
[-v|--verbose]\n
[-h|--help]\n
[--endpoint <string>, default: '${ENDPOINT}']\n"

usage() { echo -e $USAGE 1>&2; exit 1; }

# read the options
OPTS=`getopt -o vh --long verbose,help,endpoint: -n 'algo_work_interview.sh' -- "$@"`
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; usage ; exit 1 ; fi
eval set -- "$OPTS"


# extract options and their arguments into variables.
for i
do
  case "$i"
  in
    -v|--verbose)
      VERBOSE=true ;
      shift ;;
    -h|--help)
      usage ;;
    --endpoint)
      ENDPOINT="$2" ;
      shift 2 ;;
  esac
done

if [ $VERBOSE = true ]
  then
    echo VERBOSE=$VERBOSE
    echo HELP=$HELP
    echo ENDPOINT=$ENDPOINT
fi

source sources/curl_algo_work_interview.sh

jq '.' <<< $CURL_RESPONSE 2>/dev/null