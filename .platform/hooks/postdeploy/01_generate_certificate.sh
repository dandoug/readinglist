#!/usr/bin/env bash
sudo certbot -n -d booklist.media -d www.booklist.media --nginx --agree-tos --register-unsafely-without-email
