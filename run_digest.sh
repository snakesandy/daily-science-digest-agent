#!/bin/bash
cd "/Users/archacademy/Desktop/Phone Agents/daily-science-digest-agent"
/opt/anaconda3/bin/python -m digest >> ./data/digest.log 2>&1
