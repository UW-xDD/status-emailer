#!/bin/bash
set -e

cd "$(dirname "$0")"

FROM=xDD@chtc.wisc.edu
REPLYTO=edquist@cs.wisc.edu
TO="edquist@cs.wisc.edu, iross@cs.wisc.edu"

TS=$(date +%Y%m%d-%H%M%s)
{
{
echo "\
From: $FROM
Reply-To: $REPLYTO
To: $TO
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8"
#Subject: $subject provided by articlesummary.py

./generate-email-subject+body.sh 7d

} | /usr/sbin/sendmail -t
} </dev/null &>"log/emailer.$TS.log" &

